import { Card } from "../components/ui/card";
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
      <p className="mt-8 text-center text-sm text-gray-500">
        No matches found, try again!
      </p>
    );
  }

  return (
    <div className="mt-8 px-4">
      {/* Section header */}
      <div className="flex items-center justify-center gap-4 mb-8">
        <div className="h-px w-16 bg-zinc-700" />
        <p className="text-white font-semibold text-xl tracking-wide">
          Top {results.length} Picks
        </p>
        <div className="h-px w-16 bg-zinc-700" />
      </div>

      {/* Grid */}
      <div className="mx-auto max-w-6xl grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
        {results.map((song) => (
            <Card
            key={song.song_id}
            className="group relative bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden
                        hover:shadow-lg hover:border-zinc-700 transition-all duration-300"
            >
            {/* Album Art / Fixed Aspect Ratio */}
            <div className="relative aspect-square w-full overflow-hidden bg-zinc-800 flex items-center justify-center">
                {song.album_art ? (
                <img
                    src={song.album_art}
                    alt={song.title}
                    className="w-full h-full object-cover"
                />
                ) : (
                // Fallback if no image
                <div className="text-gray-500 text-sm">No Image</div>
                )}

                {/* Gradient overlay for text readability */}
                <div className="absolute inset-0 bg-linear-to-t from-black/80 via-black/40 to-transparent" />

                {/* Text overlay */}
                <div className="absolute bottom-2 left-2 right-2 text-white">
                <a
                    href={song.webpage_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-lg font-semibold hover:underline line-clamp-1 flex items-center gap-2"
                >
                    {song.title}
                    <ExternalLink className="w-3 h-3 text-gray-300 opacity-80" />
                </a>
                <p className="text-sm text-gray-300 line-clamp-1">
                    {song.artist}{song.album ? ` · ${song.album}` : ""}
                </p>
                <div className="flex justify-between text-xs text-gray-500 pt-2">
                    <span>{song.votes} votes</span>
                    <span>{(song.confidence * 100).toFixed(1)}%</span>
                </div>
                </div>
            </div>
            </Card>

        ))}
      </div>
    </div>
  );
}
