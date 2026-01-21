import { Card, CardContent } from "../components/ui/card";
import { ExternalLink } from "lucide-react";

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
    return (
      <p className="mt-10 text-center text-sm text-gray-500">
        No matches found
      </p>
    );
  }

  return (
    <div className="mt-10 grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
      {results.map((song) => (
        <Card
          key={song.song_id}
          className="group bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden
                     hover:shadow-xl hover:border-zinc-700 transition-all duration-300"
        >
          {/* Album Art */}
          <div className="relative">
            <img
              src={song.album_art}
              alt={song.title}
              className="w-full h-44 object-cover"
            />
            <div className="absolute inset-0 bg-linear-to-t from-black/70 to-transparent" />
          </div>

          {/* Content */}
          <CardContent className="p-4 space-y-2">
            <h3 className="text-white font-semibold text-base leading-tight flex items-center gap-2">
              <a
                href={song.webpage_url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline"
              >
                {song.title}
              </a>
              <ExternalLink className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition" />
            </h3>

            <p className="text-sm text-gray-400">
              {song.artist} · {song.album ? song.album : ""}
            </p>

            <div className="flex justify-between text-xs text-gray-500 pt-2">
              <span>Votes: {song.votes}</span>
              <span>{(song.confidence * 100).toFixed(1)}% match</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
