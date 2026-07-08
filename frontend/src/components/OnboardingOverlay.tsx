interface OnboardingOverlayProps {
  step: number;
  onNext: () => void;
  onSkip: () => void;
  onOpenSettings: () => void;
}

const STEPS = [
  {
    title: "步驟 1：輸入 API 金鑰",
    body: "按「API 設定」輸入 Deepgram 及 LLM 金鑰。如伺服器已設定 .env，可跳過。",
    action: "settings" as const,
  },
  {
    title: "步驟 2：上傳參考文件（可選）",
    body: "拖放 PDF 到上傳區，以便核查會議中的事實陳述。",
    action: "next" as const,
  },
  {
    title: "步驟 3：開始錄音",
    body: "撳「開始錄音」，瀏覽器會要求麥克風權限。請撳「允許」開始錄音。",
    action: "done" as const,
  },
];

export function OnboardingOverlay({
  step,
  onNext,
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
        <p className="mb-6 text-sm text-slate-600">{current.body}</p>
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
              else if (current.action === "done") onSkip();
              else onNext();
            }}
            className="min-h-11 rounded-lg bg-teal-600 px-6 text-sm font-medium text-white hover:bg-teal-700"
          >
            {current.action === "settings"
              ? "開啟設定"
              : current.action === "done"
                ? "明白了"
                : "下一步"}
          </button>
        </div>
      </div>
    </div>
  );
}
