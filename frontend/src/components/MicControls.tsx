import type { ConnectionStatus } from "../hooks/useMeetingSocket";

interface MicControlsProps {
  status: ConnectionStatus;
  isRecording: boolean;
  onStart: () => void;
  onStop: () => void;
  error?: string | null;
}

const statusLabel: Record<ConnectionStatus, string> = {
  idle: "未連線",
  connecting: "連線中…",
  connected: "已連線",
  error: "連線錯誤",
};

export function MicControls({
  status,
  isRecording,
  onStart,
  onStop,
  error,
}: MicControlsProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <span
        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
          status === "connected"
            ? "bg-green-100 text-green-700"
            : status === "error"
              ? "bg-red-100 text-red-700"
              : "bg-slate-100 text-slate-600"
        }`}
      >
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            status === "connected" ? "bg-green-500" : "bg-slate-400"
          }`}
        />
        {statusLabel[status]}
      </span>

      {!isRecording ? (
        <button
          type="button"
          onClick={onStart}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          開始錄音
        </button>
      ) : (
        <button
          type="button"
          onClick={onStop}
          className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        >
          停止錄音
        </button>
      )}

      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
