import os
import psycopg
from dotenv import load_dotenv

load_dotenv()


class DatabaseHandler:

    def __init__(self):
        db_url = os.getenv("DB_URL")
        if not db_url:
            raise RuntimeError("DB_URL not set in environment")

        try:
            self._connection = psycopg.connect(db_url)
        except Exception as e:
            raise RuntimeError(f"Failed to connect to database: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self._connection:
            try:
                self._connection.close()
            finally:
                self._connection = None

    def insert_song_metadata(self, metadata: dict, fingerprinted=False, max_retries=3):
        """
        Insert a song into songs table.
        Returns song_id (existing or newly created).
        """

        song_name = metadata.get("song_name") or metadata.get("title")
        video_id = metadata.get("video_id")
        title = metadata.get("title")
        artist = metadata.get("artist")
        album = metadata.get("album")
        album_art = metadata.get("album_art")
        webpage_url = metadata.get("webpage_url")

        query = """
            INSERT INTO songs
                (song_name, video_id, title, artist, album, album_art, webpage_url, fingerprinted)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (song_name) DO NOTHING
            RETURNING song_id;
        """

        for attempt in range(max_retries):
            try:
                with self._connection.cursor() as cur:
                    cur.execute(
                        query,
                        (
                            song_name,
                            video_id,
                            title,
                            artist,
                            album,
                            album_art,
                            webpage_url,
                            fingerprinted,
                        ),
                    )
                    row = cur.fetchone()

                    if row:
                        song_id = row[0]
                    else:
                        # Already exists, fetch ID
                        cur.execute(
                            "SELECT song_id FROM songs WHERE song_name = %s",
                            (song_name,),
                        )
                        row = cur.fetchone()
                        if not row:
                            raise RuntimeError("Song exists but song_id not found")
                        song_id = row[0]

                self._connection.commit()
                return song_id

            except Exception as e:
                self._connection.rollback()
                print(f"Attempt {attempt + 1}/{max_retries} failed inserting song: {e}")

        raise RuntimeError(f"Failed to insert song '{song_name}' after retries")


    def bulk_insert_fingerprints(self, hashes, song_id, chunk_size=10_000, max_retries=3):
        """
        Insert fingerprints in chunks.
        hashes = [(hash, time_offset), ...]
        """

        for i in range(0, len(hashes), chunk_size):
            chunk = hashes[i : i + chunk_size]

            for attempt in range(max_retries):
                try:
                    with self._connection.cursor() as cur:
                        cur.executemany(
                            """
                            INSERT INTO fingerprints (hash, song_id, time_offset)
                            VALUES (%s, %s, %s)
                            """,
                            [(h, song_id, t) for h, t in chunk],
                        )
                    self._connection.commit()
                    break

                except Exception as e:
                    self._connection.rollback()
                    print(
                        f"Attempt {attempt + 1}/{max_retries} failed "
                        f"for fingerprint chunk starting at {i}: {e}"
                    )

            else:
                raise RuntimeError(f"Fingerprint chunk starting at {i} failed")

        # Mark song as fingerprinted
        try:
            with self._connection.cursor() as cur:
                cur.execute(
                    "UPDATE songs SET fingerprinted = TRUE WHERE song_id = %s",
                    (song_id,),
                )
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            print(f"Failed to mark song {song_id} as fingerprinted: {e}")


    def find_song_from_hashes(
        self,
        hashes,
        limit=3,
        min_votes=20,
        min_confidence=0.15,
    ):
        """
        Match query fingerprints against DB.
        Returns list of matches or empty list.
        """

        if not hashes:
            return []

        total_hashes = len(hashes)
        hash_list = [h for h, _ in hashes]
        offset_list = [int(t) for _, t in hashes]

        query = """
            WITH query_hashes(hash, query_offset) AS (
                SELECT * FROM unnest(%s::bytea[], %s::int[])
            )
            SELECT
                s.song_id,
                s.song_name,
                s.video_id,
                s.title,
                s.artist,
                s.album,
                s.album_art,
                s.webpage_url,
                COUNT(*) AS votes,
                COUNT(*)::float / %s AS confidence
            FROM fingerprints f
            JOIN query_hashes q ON f.hash = q.hash
            JOIN songs s ON s.song_id = f.song_id
            GROUP BY s.song_id, s.song_name
            HAVING COUNT(*) >= %s
               AND COUNT(*)::float / %s >= %s
            ORDER BY votes DESC, confidence DESC
            LIMIT %s;
        """

        params = [
            hash_list,
            offset_list,
            total_hashes,
            min_votes,
            total_hashes,
            min_confidence,
            limit,
        ]

        with self._connection.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        if not rows:
            return []

        results = []
        for (
            song_id,
            song_name,
            video_id,
            title,
            artist,
            album,
            album_art,
            webpage_url,
            votes,
            confidence,
        ) in rows:
            results.append(
                {
                    "song_id": song_id,
                    "song_name": song_name,
                    "video_id": video_id,
                    "title": title,
                    "artist": artist,
                    "album": album,
                    "album_art": album_art,
                    "webpage_url": webpage_url,
                    "votes": votes,
                    "confidence": confidence,
                }
            )

        return results
