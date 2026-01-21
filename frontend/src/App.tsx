import "./App.css";
import { useState } from "react";
import MicRecorder from "./component/MicRecorder";
import MatchResult from "./component/MatchResult";
import { Alert, AlertDescription } from "./components/ui/alert";
import { AlertTriangle, AudioLines, ExternalLink, Loader2 } from "lucide-react";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL

function App() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[] | null>(null); 
  const [error, setError] = useState<string | null>(null);

  function pingForResult(task_id: string): Promise<any> {
    return new Promise((resolve, reject) => {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(
            `${BACKEND_URL}/task_status/${task_id}`
          );
          if (!response.ok) throw new Error("Failed to fetch task status");

          const data = await response.json();
          if (data.status !== "pending") {
            clearInterval(interval);
            resolve(data);
          }
        } catch (err) {
          clearInterval(interval);
          reject(err);
        }
      }, 1500);
    });
  }

  async function uploadAudio(wavBlob: Blob) {
    setLoading(true);
    setError(null);
    setResults(null);

    const formData = new FormData();
    formData.append("file", wavBlob, "mic.wav");

    try {
      const response = await fetch(`${BACKEND_URL}/match_file`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Failed to start matching task");

      setResults([]);

      const data = await response.json();
      const finalResult = await pingForResult(data.task_id);

      if (finalResult.status === "success") {
        const res = finalResult.result || [];
        setResults(res.length > 0 ? res : []); 
        if (res.length === 0) setError("No match found.");
      } else {
        setResults([]);
        setError("No match found.");
      }
    } catch (err: any) {
      setError(err.message || "Unexpected error occurred.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen relative flex flex-col items-center px-4 py-10 overflow-hidden">
      {/* Gradient Background */}
      <div className="absolute inset-0 bg-linear-to-br from-[#0b0b10] via-[#1c1c26] to-[#0b0b10] -z-10 animate-gradientBackground"></div>
      <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full bg-purple-600/20 blur-3xl -z-5"></div>
      <div className="absolute -bottom-40 -right-40 w-96 h-96 rounded-full bg-blue-500/20 blur-3xl -z-5"></div>

      {/* Header */}
      <h1 className="text-5xl font-semibold tracking-tight mb-2 text-white"> 
        <div className="flex items-center gap-2">
            <AudioLines className="w-12 h-12"/> Spectra
        </div>
        </h1>
      <p className="text-lg text-gray-300 mb-10 text-center max-w-md">
        Identify music easily.
      </p>

      {/* Recorder */}
      <div className="relative flex flex-col items-center m-8">
        <MicRecorder onRecordingComplete={uploadAudio} />
      </div>

      {/* Intro paragraph if no results yet */}
      {results === null && !loading && !error && (
        <>
            <p className="text-gray-400 text-center max-w-sm mt-6 text-lg">
                Press the microphone above to start recording a song snippet, 
                and Spectra will find the match for you!
            </p>
                <br/>
                <br/>
            <p className="text-gray-500 text-center max-w-sm mt-6 text-sm">
                Spectra is a proof-of-concept that currently supports a small library of under 50 songs. I’ve put together a sample playlist so you can try it out!
            <br/><br/>
            <span>
                <a
                    href="https://music.youtube.com/playlist?list=PLDK9ZUC554U0p36ueSUzCbS-kCa2ONrUM"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline flex items-center justify-center"
                >
                    Spectra Test Playlist
                    <ExternalLink className="ml-2 w-4 h-4 text-gray-400 transition" />
                </a>
            </span>
            </p>
        </>
      )}

      {/* Loading / Matching message */}
      {loading && (
        <div className="flex items-center space-x-2 mt-4 text-gray-300">
          <Loader2 className="animate-spin w-5 h-5 text-blue-400" />
          <span>Trying to find a match...</span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-6 w-full max-w-md items-center">
          <Alert className="bg-red-900/80 border-red-700 text-red-100 backdrop-blur items-center">
            <AlertTriangle className="w-5 h-5 mr-2" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* Results */}
      {results && results.length > 0 && <MatchResult results={results} />}
    </div>
  );
}

export default App;
