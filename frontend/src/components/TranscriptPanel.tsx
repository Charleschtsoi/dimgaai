import { useEffect, useRef } from "react";
import type { TranscriptLine } from "../types/events";

interface TranscriptPanelProps {
  lines: TranscriptLine[];
}

export function TranscriptPanel({ lines }: TranscriptPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  return (
    <section className="flex h-full min-h-64 flex-col rounded-xl border border-slate-200 bg-white shadow-sm lg:min-h-0">
      <header className="border-b border-slate-100 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-700">即時轉錄</h2>
        <p className="text-xs text-slate-500">粵語 (zh-HK) · 講者分離</p>
      </header>
      <div className="flex-1 space-y-3 overflow-y-auto overflow-x-hidden p-4">
        {lines.length === 0 ? (
          <p className="text-sm text-slate-400">等待發言…</p>
        ) : (
          lines.map((line) => (
            <article
              key={line.id}
              className={`rounded-lg px-3 py-2 break-words ${
                line.isFactualClaim
                  ? "border-l-4 border-yellow-400 bg-yellow-50"
                  : line.isFinal
                    ? "bg-slate-50"
                    : "bg-slate-100/60 opacity-70"
              }`}
            >
              <span className="mb-1 inline-block rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700">
                Speaker {line.speaker}
              </span>
              {line.isFactualClaim && (
                <span className="ml-2 text-xs font-medium text-yellow-700">
                  事實陳述
                </span>
              )}
              <p className="text-sm leading-relaxed text-slate-800">{line.text}</p>
            </article>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </section>
  );
}
