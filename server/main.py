import sys
import os
import random
import sounddevice as sd
import soundfile as sf
import numpy as np
from engine.fingerprint import *
from database.handler import *

MIC_DEVICE_INDEX = 2
MIC_DURATION = 5
MIC_SR = 48000
MIC_CHANNELS = 1
MIC_OUTPUT_FILE = "mic.wav"

def record_from_mic():

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

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    flag = sys.argv[1]

    try:
        if flag == "mic":
            file_path = record_from_mic()
        else:
            if len(sys.argv) < 3:
                raise Exception("File path missing")
            file_path = sys.argv[2]

        y, _ = load_file(filename=file_path)
        peak_points = get_peak_points(y=y)
        hashes = generate_hashes(peak_points=peak_points)

        print(f"Generated {len(hashes)} hashes")

        if flag == "insert":
            with DatabaseHandler() as db:
                filename = os.path.basename(file_path)
                song_name = os.path.splitext(filename)[0]

                print("Adding song metadata to DB...")
                song_id = db.insert_song_metadata(song_name)

                print("Adding song fingerprints to DB...")
                db.bulk_insert_fingerprints(hashes, song_id)

        elif flag in ("match", "mic"):
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


        else:
            raise Exception("Invalid option flag")

    except Exception as e:
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    main()
