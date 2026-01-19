import sys
import os
import random
import sounddevice as sd
import soundfile as sf
import numpy as np

from engine.fingerprint import load_file, get_peak_points, generate_hashes
from engine.dl_handler import download_yt_music, get_music_metadata
from database.handler import DatabaseHandler


MIC_DEVICE_INDEX = 2
MIC_DURATION = 5
MIC_SR = 48000
MIC_CHANNELS = 1
MIC_OUTPUT_FILE = "mic.wav"


def record_from_mic():
    """
    Record a 5 second snippet from the mic
    """

    print("Starting to record...")
    sd.default.device = (MIC_DEVICE_INDEX, None)

    audio = sd.rec(
        int(MIC_DURATION * MIC_SR),
        samplerate=MIC_SR,
        channels=MIC_CHANNELS,
        dtype=np.float32
    )

    sd.wait()

    if np.max(np.abs(audio)) < 1e-4:
        raise Exception("Microphone captured silence")

    sf.write(MIC_OUTPUT_FILE, audio, MIC_SR)
    return MIC_OUTPUT_FILE


def match_from_mic():
    """
    Record from mic and compare the temp file
    """
    
    file_path = record_from_mic()
    match_from_file(file_path)
    os.remove(file_path)


def insert_from_url(url):
    """
    Get metadata from YT music URL and download file,
    Generate peaks and hashes,
    Insert metadata and hashes into DB
    """

    print("Getting metadata from link...")
    metadata = get_music_metadata(url)

    with DatabaseHandler() as db:
        for track in metadata:
            try:
                print("===================================")
                download_yt_music(track)

                print("Generating hashes...")
                y, _ = load_file(filename=track.get("audio_path"))
                peak_points = get_peak_points(y=y)
                hashes = generate_hashes(peak_points=peak_points)

                print(f"Generated {len(hashes)} hashes")

                print("Adding song metadata to DB...")
                song_id = db.insert_song_metadata(track)

                print("Adding song fingerprints to DB...")
                db.bulk_insert_fingerprints(hashes, song_id)

            except Exception as e:
                print(f"Failed to download track {track.get('title')}: {e}")
                continue

            finally:
                print(f"Removing audio file: {track.get("audio_path")}")
                os.remove(track.get("audio_path"))

def match_from_file(file_path):
    """
    Load file, generate hashes and compare to DB
    """

    y, _ = load_file(filename=file_path)
    peak_points = get_peak_points(y=y)
    hashes = generate_hashes(peak_points=peak_points)

    print(f"Generated {len(hashes)} hashes")

    sampled_hashes = random.sample(hashes, min(5000, len(hashes)))
    with DatabaseHandler() as db:
        result = db.find_song_from_hashes(sampled_hashes)
    
    if result:
        print("\nTop Matches:")
        for idx, song in enumerate(result, start=1):
            print(f"{idx}. {song['song_name']} (ID: {song['song_id']})")
            print(f"   Votes: {song['votes']}")
            print(f"   Absolute Confidence: {song['confidence']:.3f}")
            print("===================================")
    else:
        print("No matches found.")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <flag> <optional>")
        print("- insert <url>: Takes in YT music URL and insert fingerprints to DB")
        print("- match <file_path>: Takes in file_path and find a match to that audio file")
        print("- mic: Record 5s clip from microphone, and compare to DB")
        sys.exit(1)

    flag = sys.argv[1]

    try:
        if flag == "mic":
            match_from_mic()

        elif flag == "insert":
            if len(sys.argv) < 3:
                raise Exception("URL missing")
            url = sys.argv[2]

            insert_from_url(url)

        elif flag == "match":
            if len(sys.argv) < 3:
                raise Exception("File name missing")
            file_path = sys.argv[2]

            match_from_file(file_path)
        
        else:
            raise Exception("Invalid option flag")

    except Exception as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
