import os
import sys
import psycopg
from dotenv import load_dotenv

load_dotenv()

class DatabaseHandler:
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not getattr(self, "_initialized", False):
            try:
                DB_URL = os.getenv("DB_URL")
                self._connection = psycopg.connect(DB_URL)
                self._initialized = True
            except Exception as e:
                print("Error initializing DB connection:", e)
                sys.exit(1)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        try:
            if getattr(self, "_connection", None):
                self._connection.close()
                self._connection = None
        except Exception:
            # Ignore exceptions during garbage collection
            pass

    def insert_song_metadata(self, song_name, fingerprinted=False, max_retries=3):

        query = """
            INSERT INTO songs (song_name, fingerprinted)
            VALUES (%s, %s)
            ON CONFLICT (song_name) DO NOTHING
            RETURNING song_id;
        """

        for attempt in range(max_retries):
            try:
                with self._connection.cursor() as cur:
                    cur.execute(query, (song_name, fingerprinted))
                    result = cur.fetchone()

                    if result is None:
                        # Song already exists
                        raise RuntimeError(f"Song '{song_name}' already exists in the database.")

                    song_id = result[0]
                    self._connection.commit()

                return song_id

            except Exception as e:
                self._connection.rollback()
                print(f"Attempt {attempt+1}/{max_retries} failed to insert song '{song_name}': {e}")

        else:
            raise RuntimeError(f"Failed to insert song '{song_name}' after {max_retries} retries")

    def bulk_insert_fingerprints(self, hashes, song_id, chunk_size=10000, max_retries=3):
        
        for i in range(0, len(hashes), chunk_size):
            chunk = hashes[i : i + chunk_size]

            for attempt in range(max_retries):
                try:
                    with self._connection.cursor() as cur:
                        cur.executemany(
                            "INSERT INTO fingerprints(hash, song_id, time_offset) VALUES (%s, %s, %s)",
                            [(h, song_id, t) for h, t in chunk]
                        )
                        self._connection.commit()
                    break
        
                except Exception as e:
                    self._connection.rollback()
                    print(f"Attempt {attempt+1}/{max_retries} failed for chunk starting at index {i}: {e}")
        
            else:
                raise RuntimeError(f"Chunk starting at index {i} failed after {max_retries} retries")

        # After all chunks are inserted, mark the song as fingerprinted
        try:
            with self._connection.cursor() as cur:
                cur.execute(
                    "UPDATE songs SET fingerprinted = TRUE WHERE song_id = %s",
                    (song_id,)
                )
                self._connection.commit()
        
                print(f"Song {song_id} marked as fingerprinted")
        
        except Exception as e:
            self._connection.rollback()
            print(f"Failed to mark song {song_id} as fingerprinted: {e}")

    def find_song_from_hashes(self, hashes, limit = 3, min_votes=20, min_confidence=0.15):

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
                COUNT(*) AS votes,
                COUNT(*)::float / %s AS confidence
            FROM fingerprints f
            JOIN query_hashes q
            ON f.hash = q.hash
            JOIN songs s ON s.song_id = f.song_id
            GROUP BY s.song_id, s.song_name
            HAVING COUNT(*) >= %s AND COUNT(*)::float / %s >= %s
            ORDER BY votes DESC, confidence DESC
            LIMIT %s;
        """

        params = [hash_list, offset_list, total_hashes, min_votes, total_hashes, min_confidence, limit]

        with self._connection.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        if not rows:
            raise RuntimeError("No matching song found")

        results = []
        for song_id, song_name, votes, confidence in rows:
            results.append({
                "song_id": song_id,
                "song_name": song_name,
                "votes": votes,
                "confidence": confidence
            })

        return results
