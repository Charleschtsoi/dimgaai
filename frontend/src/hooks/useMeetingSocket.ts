import { useCallback, useEffect, useRef, useState } from "react";
import type { ServerEvent } from "../types/events";

export type ConnectionStatus = "idle" | "connecting" | "connected" | "error";

interface UseMeetingSocketOptions {
  sessionId: string;
  onEvent: (event: ServerEvent) => void;
}

export function useMeetingSocket({ sessionId, onEvent }: UseMeetingSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus("connecting");
    setError(null);

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/meeting/${sessionId}`);
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => setStatus("connected");
    ws.onclose = () => {
      setStatus("idle");
      wsRef.current = null;
    };
    ws.onerror = () => {
      setStatus("error");
      setError("WebSocket 連線失敗");
    };
    ws.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data as string) as ServerEvent;
        if (event.type === "error") {
          setError(event.message);
        }
        if (event.type === "status" && event.message === "connected") {
          setStatus("connected");
        }
        onEventRef.current(event);
      } catch {
        // ignore non-json
      }
    };
  }, [sessionId]);

  const disconnect = useCallback(() => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "stop" }));
      ws.close();
    }
    wsRef.current = null;
    setStatus("idle");
  }, []);

  const sendAudio = useCallback((chunk: ArrayBuffer) => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(chunk);
    }
  }, []);

  useEffect(() => {
    return () => disconnect();
  }, [disconnect]);

  return { status, error, connect, disconnect, sendAudio };
}
