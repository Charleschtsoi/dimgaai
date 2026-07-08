import { useCallback, useEffect, useRef, useState } from "react";
import type { ServerEvent } from "../types/events";

export type ConnectionStatus =
  | "idle"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "error";

interface UseMeetingSocketOptions {
  sessionId: string;
  onEvent: (event: ServerEvent) => void;
  enabled?: boolean;
}

const MAX_RETRIES = 3;
const BACKOFF_MS = [1000, 2000, 4000];
const CONNECT_TIMEOUT_MS = 15_000;

export function useMeetingSocket({
  sessionId,
  onEvent,
  enabled = true,
}: UseMeetingSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const intentionalCloseRef = useRef(false);
  const connectWaiterRef = useRef<{
    resolve: () => void;
    reject: (error: Error) => void;
  } | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const settleConnectWaiter = useCallback(
    (result: "resolve" | "reject", message?: string) => {
      const waiter = connectWaiterRef.current;
      if (!waiter) return;
      connectWaiterRef.current = null;
      if (result === "resolve") {
        waiter.resolve();
      } else {
        waiter.reject(new Error(message || "WebSocket 連線失敗"));
      }
    },
    [],
  );

  const connect = useCallback(() => {
    if (!enabled) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    intentionalCloseRef.current = false;
    setStatus(retriesRef.current > 0 ? "reconnecting" : "connecting");
    setError(null);

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(
      `${protocol}//${window.location.host}/ws/meeting/${sessionId}`,
    );
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => {
      retriesRef.current = 0;
      setStatus("connected");
      ws.send(JSON.stringify({ type: "audio_format", format: "webm" }));
      settleConnectWaiter("resolve");
    };

    ws.onclose = () => {
      wsRef.current = null;
      if (!intentionalCloseRef.current) {
        settleConnectWaiter("reject", "連線已關閉，請檢查 API 金鑰或重新開始錄音。");
      }
      if (intentionalCloseRef.current) {
        setStatus("idle");
        return;
      }
      if (retriesRef.current < MAX_RETRIES) {
        const delay = BACKOFF_MS[retriesRef.current] ?? 4000;
        retriesRef.current += 1;
        setStatus("reconnecting");
        setTimeout(() => connect(), delay);
      } else {
        setStatus("error");
        setError("連線中斷，請重新開始錄音。");
      }
    };

    ws.onerror = () => {
      setError("WebSocket 連線失敗");
      settleConnectWaiter("reject", "WebSocket 連線失敗");
    };

    ws.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data as string) as ServerEvent;
        if (event.type === "error") {
          setError(event.message);
          setStatus("error");
          settleConnectWaiter("reject", event.message);
        }
        if (event.type === "status" && event.message === "connected") {
          setStatus("connected");
        }
        onEventRef.current(event);
      } catch {
        // ignore non-json
      }
    };
  }, [sessionId, enabled, settleConnectWaiter]);

  const connectAndWait = useCallback((): Promise<void> => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      connectWaiterRef.current = { resolve, reject };
      connect();

      window.setTimeout(() => {
        if (!connectWaiterRef.current) return;
        connectWaiterRef.current = null;
        reject(new Error("連線逾時，請檢查 API 金鑰後重試。"));
      }, CONNECT_TIMEOUT_MS);
    });
  }, [connect]);

  const disconnect = useCallback(() => {
    intentionalCloseRef.current = true;
    retriesRef.current = MAX_RETRIES;
    connectWaiterRef.current = null;
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

  return { status, error, connect, connectAndWait, disconnect, sendAudio };
}
