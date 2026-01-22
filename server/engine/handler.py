import os
import random

import numpy as np

from server.engine.fingerprint import load_file, get_peak_points, generate_hashes
from server.engine.dl_handler import download_yt_music, get_music_metadata
from server.database.handler import DatabaseHandler


def insert_from_url(url, logging_enabled=True):
    """
    Get metadata from YT music URL and download file,
    Generate peaks and hashes,
    Insert metadata and hashes into DB.
    Only prints logs if logging_enabled=True.
    """

    if logging_enabled:
        print("Getting metadata from link...")
   
    metadata = get_music_metadata(url)

    with DatabaseHandler() as db:
        for track in metadata:
            try:
                if logging_enabled:
                    print("===================================")
                download_yt_music(track)

                if logging_enabled:
                    print("Generating hashes...")
                y, _ = load_file(filename=track.get("audio_path"))
                peak_points = get_peak_points(y=y)
                hashes = generate_hashes(peak_points=peak_points)

                if logging_enabled:
                    print(f"Generated {len(hashes)} hashes")
                    print("Adding song metadata to DB...")

                song_id = db.insert_song_metadata(track)

                if logging_enabled:
                    print("Adding song fingerprints to DB...")
                db.bulk_insert_fingerprints(hashes, song_id)

            except Exception as e:
                if logging_enabled:
                    print(f"Failed to download track {track.get('title')}: {e}")
                continue

            finally:
                if logging_enabled:
                    print(f"Removing audio file: {track.get('audio_path')}")
                if os.path.exists(track.get("audio_path")):
                    os.remove(track.get("audio_path"))


def match_from_file(file_path, logging_enabled=True):
    """
    Load file, generate hashes, and compare to DB.
    Only prints logs if logging_enabled=True.
    """

    y, _ = load_file(filename=file_path)

    if np.max(np.abs(y)) < 1e-3:
        raise Exception("Microphone captured silence")

    peak_points = get_peak_points(y=y)
    hashes = generate_hashes(peak_points=peak_points)

    print(f"Generated {len(hashes)} hashes")
    
    sampled_hashes = random.sample(hashes, min(5000, len(hashes)))
    with DatabaseHandler() as db:
        result = db.find_song_from_hashes(sampled_hashes)
    
    if result:
        if logging_enabled:
            print("\nTop Matches:")
            for idx, song in enumerate(result, start=1):
                print(f"{idx}. {song['song_name']} (ID: {song['song_id']})")
                print(f"   Title: {song['title']}")
                print(f"   Artist: {song['artist']}")
                print(f"   Album: {song['album']}")
                print(f"   Votes: {song['votes']}")
                print(f"   Absolute Confidence: {song['confidence']:.3f}")
                print(f"   Video ID: {song['video_id']}")
                print(f"   URL: {song['webpage_url']}")
                print("===================================")
        return result

    
    else:
        if logging_enabled:
            print("No matches found.")
        return None
