import { useRef, useState } from "react";
import { convertToWav } from "../utils/wavUtils";

type MicRecorderProps = {
  onRecordingComplete: (wavBlob: Blob) => Promise<void> | void;
};

export default function MicRecorder({ onRecordingComplete }: MicRecorderProps){
    const mediaRecorderRef = useRef<MediaRecorder|null>(null);
    const audioChunkRef = useRef<any>([]);
    const [recording, setRecording] = useState<boolean>(false);

    async function startRecording() {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: true
        })

        mediaRecorderRef.current = new MediaRecorder(stream);
        audioChunkRef.current = [];

        mediaRecorderRef.current.ondataavailable = (event) => {
            audioChunkRef.current.push(event.data)
        }

        mediaRecorderRef.current.start();
        setRecording(true);
    }

    async function stopRecording(){
        if(mediaRecorderRef.current){
            mediaRecorderRef.current.stop();
            setRecording(false);

            mediaRecorderRef.current.onstop = async () => {
                const webmBlob = new Blob(audioChunkRef.current, {
                    type: "audio/webm"
                });
    
                const wavBlob = await convertToWav(webmBlob);
                await onRecordingComplete(wavBlob);
            }
        }
    }

  return (
    <div>
      <button onClick={startRecording} disabled={recording}>
        Start Recording
      </button>

      <button onClick={stopRecording} disabled={!recording}>
        Stop & Upload
      </button>
    </div>
  );
}