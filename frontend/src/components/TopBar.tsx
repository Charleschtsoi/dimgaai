import type { ConnectionStatus } from "../hooks/useMeetingSocket";

interface TopBarProps {
  status: ConnectionStatus;
  isRecording: boolean;
  onToggleRecording: () => void;
  error?: string | null;
}

const statusLabel: Record<ConnectionStatus, string> = {
  idle: "未連線",
  connecting: "連線中…",
  connected: "已連線",
  reconnecting: "重新連線中…",
  error: "連線錯誤",
};

export function TopBar({
  status,
  isRecording,
  onToggleRecording,
  error,
}: TopBarProps) {
  return (
    <div className="flex flex-col items-center gap-3 py-2">
      <span
        className={`inline-flex min-h-6 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
          status === "connected"
            ? "bg-green-100 text-green-700"
            : status === "reconnecting"
              ? "bg-amber-100 text-amber-700"
              : status === "error"
                ? "bg-red-100 text-red-700"
                : "bg-slate-100 text-slate-600"
        }`}
      >
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            status === "connected" ? "bg-green-500 animate-pulse" : "bg-slate-400"
          }`}
        />
        {statusLabel[status]}
      </span>

      <button
        type="button"
        onClick={onToggleRecording}
        className={`flex min-h-14 min-w-48 items-center justify-center rounded-full px-8 text-base font-semibold text-white shadow-md transition-transform active:scale-95 ${
          isRecording
            ? "bg-red-600 hover:bg-red-700"
            : "bg-teal-600 hover:bg-teal-700"
        }`}
      >
        {isRecording ? "⏹ 停止錄音" : "🎙️ 開始錄音"}
      </button>

      {error && <p className="text-center text-xs text-red-600">{error}</p>}
    </div>
  );
}
