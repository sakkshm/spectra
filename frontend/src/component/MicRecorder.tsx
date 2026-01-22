import { useRef, useState, useEffect } from "react";
import { convertToWav } from "../utils/wavUtils";
import { Button } from "../components/ui/button";
import { Mic, Loader2 } from "lucide-react";

type Props = {
  onRecordingComplete: (wav: Blob) => Promise<void>;
};

const RECORDING_DURATION = 5; // seconds

export default function MicRecorder({ onRecordingComplete }: Props) {
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [timer, setTimer] = useState(0);

  useEffect(() => {
    if (!recording) return;
    const t = setInterval(() => {
      setTimer((v) => {
        if (v >= RECORDING_DURATION) {
          stop();
          return 0;
        }
        return v + 1;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [recording]);

  async function start() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder.current = new MediaRecorder(stream);
    chunks.current = [];
    mediaRecorder.current.ondataavailable = (e) => chunks.current.push(e.data);
    mediaRecorder.current.start();
    setRecording(true);
  }

  async function stop() {
    if (!mediaRecorder.current) return;
    setRecording(false);
    setProcessing(true);

    // Stop all tracks in the stream
    mediaRecorder.current.stream.getTracks().forEach(track => track.stop());

    mediaRecorder.current.stop();
    mediaRecorder.current.onstop = async () => {
      const webm = new Blob(chunks.current);
      const wav = await convertToWav(webm);
      await onRecordingComplete(wav);
      setProcessing(false);
    };
  }

  return (
    <div className="flex flex-col items-center">
      <Button
        onClick={recording ? stop : start}
        disabled={processing}
        className={`relative w-25 h-25 rounded-full bg-zinc-900 border border-zinc-600
        hover:bg-zinc-800 transition-all`}
      >
        {processing ? (
          <Loader2 className="w-12! h-12! animate-spin" />
        ) : (
          <Mic className={`w-12! h-12! ${recording ? "text-red-400 animate-pulse" : ""}`} />
        )}
        {recording && <span className="absolute inset-0 rounded-full animate-ping border border-red-500/70" />}
      </Button>
    </div>
  );
}
