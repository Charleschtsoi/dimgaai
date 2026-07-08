interface OnboardingOverlayProps {
  step: number;
  onNext?: () => void;
  onSkip: () => void;
  onOpenSettings: () => void;
}

const STEPS = [
  {
    title: "步驟 1：設定 2 把 API 金鑰",
    body: "即時會議需要兩類 API：\n\n• Deepgram — 麥克風轉錄（粵語）\n• Google Gemini（推薦）— 分析、核查、問題\n\n按「開啟設定」選擇方案並輸入金鑰。",
    action: "settings" as const,
  },
  {
    title: "步驟 2：開始錄音",
    body: "（可選）先上傳 PDF 參考文件。然後撳「開始錄音」並允許麥克風權限。",
    action: "done" as const,
  },
];

export function OnboardingOverlay({
  step,
  onSkip,
  onOpenSettings,
}: OnboardingOverlayProps) {
  const current = STEPS[step];
  if (!current) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 sm:items-center">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <p className="mb-1 text-xs font-medium text-teal-600">
          新手指引 {step + 1} / {STEPS.length}
        </p>
        <h2 className="mb-2 text-lg font-semibold text-slate-900">
          {current.title}
        </h2>
        <p className="mb-6 whitespace-pre-line text-sm text-slate-600">
          {current.body}
        </p>
        <div className="flex justify-between gap-2">
          <button
            type="button"
            onClick={onSkip}
            className="min-h-11 rounded-lg px-4 text-sm text-slate-600 hover:bg-slate-100"
          >
            跳過
          </button>
          <button
            type="button"
            onClick={() => {
              if (current.action === "settings") onOpenSettings();
              else onSkip();
            }}
            className="min-h-11 rounded-lg bg-teal-600 px-6 text-sm font-medium text-white hover:bg-teal-700"
          >
            {current.action === "settings" ? "開啟設定" : "明白了，開始"}
          </button>
        </div>
      </div>
    </div>
  );
}
