import sys
import librosa
import hashlib
import numpy as np
from scipy.ndimage import maximum_filter

# temporal window params for creating anchor-target pairs.
FAN_OUT = 5             # No. of connections per peak 
MIN_TIME_DELTA = 1      # min time frame difference between an anchor and a target peak
MAX_TIME_DELTA = 40     # max time frame difference between an anchor and a target peak

# Neighborhood size for peak detection (frequency bins × time frames)
neighborhood_size = (20, 10)

def sha1_hash(anchor_freq, target_freq, delta_t, reduction=20):
    s = f"{anchor_freq}|{target_freq}|{delta_t}"
    h = hashlib.sha1(s.encode("utf-8")).hexdigest()

    # reducing hash size for smaller memory size
    return h[:reduction]  # 20 hex chars = 80 bits


def load_file(filename):
    print(f"Loading file: {filename}")
    
    # Load audio, resample to 22050 Hz, convert to mono
    y, sr = librosa.load(
        filename,  
        sr=22050,
        mono=True
    )

    print(f"Sampling rate: {sr}")
    print(f"Duration: {librosa.get_duration(y=y, sr=sr):.2f} sec")

    return y, sr

def get_peak_points(y):
    
    # STFT (Short-Time Fourier Transform): Converts the time-domain signal y into a 2D complex-valued array:
    # Rows → frequency bins, Columns → time frames
    # Represents frequency content over time.

    n_fft = 2048
    hop_length = 512
    stft_result = librosa.stft(
        y,
        n_fft=n_fft,
        hop_length=hop_length
    )

    # Compute amplitude spectrogram
    S = np.abs(stft_result)

    # Convert to dB scale
    S_db = librosa.amplitude_to_db(S, ref=np.max)

    # Supress low energy regions
    S_db[S_db < -80] = -80

    # Detect local maxima in a 2D neighborhood
    # maximum_filter replace each element with the maximum value within its neighborhood window
    # "== S_db" is a check if the original val is max
    local_max = maximum_filter(
        S_db,
        size=neighborhood_size
    ) == S_db

    # Apply amplitude threshold
    amp_threshold = -40
    peaks = np.where(local_max & (S_db > amp_threshold))

    # peak = (time frame, freq bin)
    peak_points = list(zip(peaks[1], peaks[0]))

    # sort by time
    peak_points.sort(key=lambda x: x[0])  

    return peak_points


def generate_hashes(peak_points):
    hashes = []

    for i in range(len(peak_points)):
        anchor_time, anchor_freq = peak_points[i]
        pairs = 0

        for k in range(i + 1, len(peak_points)):
            target_time, target_freq = peak_points[k]
            delta_t = target_time - anchor_time

            if delta_t > MAX_TIME_DELTA:
                break

            if delta_t >= MIN_TIME_DELTA:
                
                # Quantize values to reduce FFT bin jitter
                anchor_freq_q = anchor_freq // 2
                target_freq_q = target_freq // 2
                delta_t_q = delta_t // 2

                h = sha1_hash(anchor_freq_q, target_freq_q, delta_t_q)
                hashes.append((bytes.fromhex(h), anchor_time))
                pairs += 1

            if pairs >= FAN_OUT:
                break

    return hashes