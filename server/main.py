from engine.fingerprint import *

def main():
    # Check for filename argument
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <filename>")
        sys.exit(1)

    filename = sys.argv[1]

    try:
        y, _ = load_file(filename=filename)
        peak_points = get_peak_points(y=y)
        hashes = generate_hashes(peak_points=peak_points)

        print(f"Generated {len(hashes)} hashes")
        print("Sample hashes:")
        for h in hashes[:10]:
            print(h)

    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()