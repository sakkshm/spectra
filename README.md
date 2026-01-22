# Spectra

A music recognition engine powered by audio fingerprinting. It enables fast, accurate identification of songs from audio snippets, inspired by Shazam. The system supports YouTube Music downloads, generates robust fingerprints using spectrogram peaks, and stores them efficiently in a database for real-time matching.

## Features

* Robust audio fingerprinting using spectrogram peak extraction
* Efficient hash-based representation of fingerprints
* Automatic YouTube Music download and metadata extraction
* High-performance storage for millions of fingerprints using PostgreSQL
* Fast matching from local files or recordings
* REST API with asynchronous processing and task status tracking
* Built-in health checks and rate limiting for deployment


## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/spectra.git
cd spectra
```

2. Create a Python virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r server/requirements.txt
```

3. Set up a PostgreSQL database and configure the connection string in a `.env` file:

```
DB_URL=postgresql://username:password@localhost:5432/spectra
```

## API Endpoints

The system provides a REST API using FastAPI:

* `POST /match_file`: Upload a `.wav` file for matching. Returns a `task_id` for asynchronous processing.
* `GET /task_status/{task_id}`: Retrieve the result of a previously submitted matching task.
* `GET /ping`: Simple health check endpoint.
* `GET /health`: Performs system-level health checks including database connectivity and filesystem access.

Rate limiting is applied to all endpoints to prevent abuse.


## Audio Fingerprinting Architecture

### Audio Loading and Preprocessing

* Audio is loaded using `librosa` and resampled to 22050 Hz in mono.
* Short-Time Fourier Transform (STFT) converts the signal into a spectrogram.
* Amplitude spectrogram is converted to decibels and low-energy values are suppressed.

### Peak Detection

* Local maxima are detected using a 2D neighborhood filter.
* Peaks represent (time, frequency) points that are robust to noise.
* Only peaks above a configurable amplitude threshold are retained.

### Fingerprint Hashing

* Peaks are paired within a temporal window to generate **anchor-target pairs**.
* Each pair is converted to a SHA-1 hash, optionally truncated for storage efficiency.
* Hashes are stored with offsets representing their position in the song.


### Fingerprint Alignment

* Matching involves computing the offset differences between query fingerprints and database fingerprints.
* The most common offset difference identifies the song with the highest likelihood.
* This approach ensures accurate recognition even with short audio snippets or background noise.


## Project Structure

```
spectra/
├── server/
│   ├── api/
│   │   └── main.py             # FastAPI routes and handler
│   ├── engine/
│   │   ├── dl_handler.py       # YouTube Music download and metadata
│   │   ├── fingerprint.py      # Spectrogram, peak detection, hashing
│   │   └── handler.py          # Insert & match songs
│   ├── database/
│   │   └── handler.py          # Database connection and CRUD
│   ├── main.py                 # Test driver
│   └── requirements.txt
├── frontend/                   # React UI for upload and display
├── temp_download/              # Temporary audio storage
├── README.md
└── .env
```
