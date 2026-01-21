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
      <p className="mt-8 text-center text-sm text-gray-500">
        No matches found
      </p>
    );
  }

  return (
    <div className="mt-8 px-4">
        <div className="flex items-center justify-center gap-4 mb-8">
            <div className="h-px w-16 bg-zinc-700" />
            <p className="text-white font-semibold text-xl tracking-wide">
                Top {results.length} Picks
            </p>
            <div className="h-px w-16 bg-zinc-700" />
        </div>

    
      {/* centered + constrained grid */}
      <div className="mx-auto max-w-6xl grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
        {results.map((song) => (
          <Card
            key={song.song_id}
            className="group bg-zinc-900 border border-zinc-800 rounded-md overflow-hidden
                       hover:shadow-lg hover:border-zinc-700 transition-all duration-300"
          >
            {/* Album Art */}
            <div className="relative aspect-square w-max-full overflow-hidden bg-zinc-800">
              <img
                src={song.album_art}
                alt={song.title}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-linear-to-t from-black/70 to-transparent" />
            </div>

            {/* Content */}
            <CardContent className="p-2.5 space-y-1">
              <h3 className="text-white font-medium text-sm leading-tight flex items-center gap-1.5">
                <a
                  href={song.webpage_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline line-clamp-1"
                >
                  {song.title}
                </a>
                <ExternalLink className="w-3 h-3 text-gray-400 opacity-0 group-hover:opacity-100 transition" />
              </h3>

              <p className="text-xs text-gray-400 line-clamp-1">
                {song.artist}{song.album ? ` · ${song.album}` : ""}
              </p>

              <div className="flex justify-between text-[10.5px] text-gray-500 pt-0.5">
                <span>{song.votes} votes</span>
                <span>{(song.confidence * 100).toFixed(1)}%</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
