import json
import os
import subprocess
import sys

download_dir = "temp_download"

def get_music_metadata(url: str):
    """
    Handles single tracks or playlists/albums.
    Returns a list of metadata dicts for all valid music tracks.
    """
    try:
        meta_proc = subprocess.run(
            ["yt-dlp", "--dump-single-json", url],
            capture_output=True,
            text=True,
            check=True
        )
        if not meta_proc.stdout:
            print("[ERROR] yt-dlp returned empty output.", file=sys.stderr)
            return []

        metadata = json.loads(meta_proc.stdout)
    except subprocess.CalledProcessError:
        print("[ERROR] Could not fetch metadata.", file=sys.stderr)
        return []
    except json.JSONDecodeError:
        print("[ERROR] Failed to parse metadata.", file=sys.stderr)
        return []

    # Handle playlist / album
    if "entries" in metadata:
        entries = metadata["entries"]
        if not entries:
            print("[ERROR] Playlist/album is empty.", file=sys.stderr)
            return []
    else:
        entries = [metadata]

    valid_tracks = []

    for track_meta in entries:
        # Reject if not music
        categories = track_meta.get("categories", [])
        if not categories or "Music" not in categories:
            continue

        # Reject lyric, live, remix, slowed, sped-up
        title_lower = (track_meta.get("track") or track_meta.get("title") or "").lower()
        reject_keywords = ["lyric", "lyrics", "live", "remix", "slowed", "sped", "cover"]
        if any(kw in title_lower for kw in reject_keywords):
            continue

        # Safe filename and path
        safe_title = (track_meta.get("track") or track_meta.get("title")).replace("/", "_").replace("\\", "_")
        filename = f"{safe_title}.wav"
        path = os.path.join(download_dir, filename)

        # Album art
        thumbnails = track_meta.get("thumbnails") or []
        album_art_url = None
        if thumbnails:
            thumbnails_sorted = sorted(thumbnails, key=lambda x: x.get("width", 0), reverse=True)
            album_art_url = thumbnails_sorted[0].get("url")

        info = {
            "video_id": track_meta.get("id"),
            "title": track_meta.get("track") or track_meta.get("title"),
            "artist": track_meta.get("artist") or track_meta.get("uploader"),
            "album": track_meta.get("album") or None,
            "album_art": album_art_url,
            "duration": track_meta.get("duration"),
            "webpage_url": track_meta.get("webpage_url"),
            "tags": track_meta.get("tags") or [],
            "audio_path": path
        }

        valid_tracks.append(info)

    if not valid_tracks:
        print("[ERROR] No valid music tracks found in URL.", file=sys.stderr)

    return valid_tracks


def download_yt_music(track):
    """
    Download audio files from YT Music
    """

    os.makedirs(download_dir, exist_ok=True)

    # Download audio
    print(f"Downloading audio file for: {track.get("title")} - {track.get("artist")} ({track.get("video_id")})")

    try:
        subprocess.run(
            [
                "yt-dlp", track.get("webpage_url"),
                "--extract-audio",
                "--audio-format", "wav",
                "-o", track.get("audio_path")
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to download audio.", file=sys.stderr)
        return None