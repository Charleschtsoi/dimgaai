import { useEffect, useRef, useState } from "react";

interface ExportButtonProps {
  sessionId: string;
}

export function ExportButton({ sessionId }: ExportButtonProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, []);

  const download = (format: "md" | "pdf") => {
    window.open(`/export/${sessionId}?format=${format}`, "_blank");
    setOpen(false);
  };

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="min-h-11 rounded-lg border border-slate-300 bg-white px-4 text-sm text-slate-700 hover:bg-slate-50"
      >
        📥 匯出報告
      </button>
      {open && (
        <div className="absolute right-0 z-10 mt-1 w-40 rounded-lg border border-slate-200 bg-white py-1 shadow-lg">
          <button
            type="button"
            onClick={() => download("md")}
            className="block min-h-11 w-full px-4 text-left text-sm hover:bg-slate-50"
          >
            Markdown
          </button>
          <button
            type="button"
            onClick={() => download("pdf")}
            className="block min-h-11 w-full px-4 text-left text-sm hover:bg-slate-50"
          >
            PDF
          </button>
        </div>
      )}
    </div>
  );
}
