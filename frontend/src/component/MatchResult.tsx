type Song = {
  song_id: number;
  song_name: string;
  video_id: string;
  title: string;
  artist: string;
  album: string;
  album_art: string;
  webpage_url: string;
  votes: number;
  confidence: number;
};

type Props = {
  results: Song[];
};

export default function MatchResult({ results }: Props) {
  if (!results || results.length === 0) {
    return <p>No matches found.</p>;
  }

  return (
    <div style={{ marginTop: "20px" }}>
      {results.map((song) => (
        <div
          key={song.song_id}
          style={{
            display: "flex",
            alignItems: "center",
            marginBottom: "15px",
            border: "1px solid #ccc",
            padding: "10px",
            borderRadius: "8px",
          }}
        >
          <img
            src={song.album_art}
            alt={song.title}
            style={{ width: "150px", height: "80px", marginRight: "15px", borderRadius: "4px" }}
          />
          <div>
            <h3 style={{ margin: 0 }}>
              <a href={song.webpage_url} target="_blank" rel="noopener noreferrer">
                {song.title}
              </a>
            </h3>
            <p style={{ margin: "2px 0" }}>
              {song.artist} — {song.album}
            </p>
            <p style={{ margin: "2px 0", fontSize: "0.9em" }}>
              Votes: {song.votes} | Confidence: {(song.confidence * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
