import type { QuestionsEvent, VerdictEvent, VerdictType } from "../types/events";

interface VerdictSidebarProps {
  verdicts: VerdictEvent[];
  questions: QuestionsEvent[];
  checking: boolean;
}

const verdictStyles: Record<
  VerdictType,
  { bg: string; text: string; label: string }
> = {
  TRUE: { bg: "bg-green-100", text: "text-green-800", label: "正確" },
  FALSE: { bg: "bg-red-100", text: "text-red-800", label: "錯誤" },
  UNCERTAIN: { bg: "bg-yellow-100", text: "text-yellow-800", label: "不確定" },
};

export function VerdictSidebar({
  verdicts,
  questions,
  checking,
}: VerdictSidebarProps) {
  return (
    <aside className="flex h-full min-h-64 flex-col rounded-xl border border-slate-200 bg-white shadow-sm lg:min-h-0">
      <header className="border-b border-slate-100 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-700">核查結果 & 追問</h2>
      </header>
      <div className="flex-1 space-y-4 overflow-y-auto overflow-x-hidden p-4">
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            事實核查
          </h3>
          {checking && (
            <p className="mb-2 text-sm text-slate-500">核查中…</p>
          )}
          {verdicts.length === 0 && !checking ? (
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
                      <p className="text-sm font-medium text-slate-800 break-words">
                        {v.claim}
                      </p>
                      <span
                        className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${style.bg} ${style.text}`}
                      >
                        {style.label}
                      </span>
                    </div>
                    <p className="mb-2 text-xs text-slate-500">
                      信心：{Math.round(v.confidence * 100)}%
                    </p>
                    <details className="text-xs text-slate-600">
                      <summary className="cursor-pointer font-medium text-slate-700">
                        查看說明
                      </summary>
                      <p className="mt-2">{v.rationale}</p>
                    </details>
                    {(v.source_quote || v.sources[0]) && (
                      <blockquote className="mt-2 border-l-2 border-slate-200 pl-2 text-xs italic text-slate-500 break-words">
                        {(v.source_quote || v.sources[0]?.text || "").slice(0, 160)}
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
                  className="rounded-lg border border-sky-100 bg-sky-50 p-3"
                >
                  <details>
                    <summary className="cursor-pointer text-sm font-medium text-sky-900">
                      {q.questions[0] || "跟進問題"}
                    </summary>
                    <p className="mt-2 text-xs text-sky-700/80">{q.segment}</p>
                    <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-slate-700">
                      {q.questions.map((question, j) => (
                        <li key={j}>{question}</li>
                      ))}
                    </ul>
                  </details>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </aside>
  );
}
