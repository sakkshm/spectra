from engine.fingerprint import *
from database.handler import *

def main():
    # Check for filename argument
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        y, _ = load_file(filename=file_path)
        peak_points = get_peak_points(y=y)
        hashes = generate_hashes(peak_points=peak_points)

        print(f"Generated {len(hashes)} hashes")
        print("Sample hashes:")
        for h in hashes[:10]:
            print(h)

        print("Trying to add fingerprints to DB...")

        with DatabaseHandler() as db:
            filename = os.path.basename(file_path)
            song_name = os.path.splitext(filename)[0]

            print("Trying to add song metadata to DB...")
            song_id = db.insert_song_metadata(song_name)

            print("Trying to add song fingerprints to DB...")
            db.bulk_insert_fingerprints(hashes, song_id)
        

    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()