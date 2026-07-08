import type { QuestionsEvent, VerdictEvent, VerdictType } from "../types/events";

interface VerdictSidebarProps {
  verdicts: VerdictEvent[];
  questions: QuestionsEvent[];
}

const verdictStyles: Record<
  VerdictType,
  { bg: string; text: string; label: string }
> = {
  TRUE: { bg: "bg-green-100", text: "text-green-800", label: "正確" },
  FALSE: { bg: "bg-red-100", text: "text-red-800", label: "錯誤" },
  UNCERTAIN: { bg: "bg-yellow-100", text: "text-yellow-800", label: "不確定" },
};

export function VerdictSidebar({ verdicts, questions }: VerdictSidebarProps) {
  return (
    <aside className="flex h-full flex-col rounded-xl border border-slate-200 bg-white shadow-sm">
      <header className="border-b border-slate-100 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-700">核查結果 & 追問</h2>
      </header>
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            事實核查
          </h3>
          {verdicts.length === 0 ? (
            <p className="text-sm text-slate-400">未偵測到可核實的陳述</p>
          ) : (
            <div className="space-y-3">
              {verdicts.map((v, i) => {
                const style = verdictStyles[v.verdict];
                return (
                  <article
                    key={`${v.claim}-${i}`}
                    className="rounded-lg border border-slate-100 p-3"
                  >
                    <div className="mb-2 flex items-start justify-between gap-2">
                      <p className="text-sm font-medium text-slate-800">{v.claim}</p>
                      <span
                        className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${style.bg} ${style.text}`}
                      >
                        {style.label}
                      </span>
                    </div>
                    <p className="mb-2 text-xs text-slate-600">{v.rationale}</p>
                    {v.sources[0] && (
                      <blockquote className="border-l-2 border-slate-200 pl-2 text-xs italic text-slate-500">
                        {v.sources[0].text.slice(0, 160)}
                        {v.sources[0].text.length > 160 ? "…" : ""}
                      </blockquote>
                    )}
                    <p className="mt-2 text-[10px] text-slate-400">
                      {v.latency_ms}ms
                      {v.used_web_search ? " · 網絡搜尋" : ""}
                    </p>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            追問問題
          </h3>
          {questions.length === 0 ? (
            <p className="text-sm text-slate-400">等待發言…</p>
          ) : (
            <div className="space-y-3">
              {questions.map((q, i) => (
                <article
                  key={`${q.segment}-${i}`}
                  className="rounded-lg bg-slate-50 p-3"
                >
                  <p className="mb-1 text-xs text-slate-500">{q.segment}</p>
                  <ul className="list-inside list-disc space-y-1 text-sm text-slate-700">
                    {q.questions.map((question, j) => (
                      <li key={j}>{question}</li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </aside>
  );
}
