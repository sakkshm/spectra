import sys
import os
import sounddevice as sd
import soundfile as sf
import numpy as np

from server.engine.handler import insert_from_url, match_from_file


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
