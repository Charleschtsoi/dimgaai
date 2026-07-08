import { useCallback, useRef, useState } from "react";

const WEBM_FRAME = 0x01;
const TIMESLICE_MS = 250;

function frameWebmChunk(buffer: ArrayBuffer): ArrayBuffer {
  const framed = new Uint8Array(buffer.byteLength + 1);
  framed[0] = WEBM_FRAME;
  framed.set(new Uint8Array(buffer), 1);
  return framed.buffer;
}

function pickMimeType(): string {
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
  ];
  for (const type of candidates) {
    if (MediaRecorder.isTypeSupported(type)) return type;
  }
  return "";
}

export function useAudioCapture(onChunk: (chunk: ArrayBuffer) => void) {
  const [isRecording, setIsRecording] = useState(false);
  const [micError, setMicError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const onChunkRef = useRef(onChunk);
  onChunkRef.current = onChunk;

  const stop = useCallback(() => {
    const recorder = recorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
    recorderRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setIsRecording(false);
  }, []);

  const start = useCallback(async () => {
    setMicError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      streamRef.current = stream;

      const mimeType = pickMimeType();
      if (!mimeType) {
        throw new Error("瀏覽器不支援音訊錄製格式");
      }

      const recorder = new MediaRecorder(stream, { mimeType });
      recorderRef.current = recorder;
      recorder.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          const buffer = await event.data.arrayBuffer();
          onChunkRef.current(frameWebmChunk(buffer));
        }
      };
      recorder.onerror = () => {
        setMicError("錄音發生錯誤，請重試。");
        stop();
      };
      recorder.start(TIMESLICE_MS);
      setIsRecording(true);
    } catch {
      setMicError("無法存取麥克風。請撳「允許」開始錄音。");
      stop();
    }
  }, [stop]);

  return { isRecording, micError, start, stop };
}
