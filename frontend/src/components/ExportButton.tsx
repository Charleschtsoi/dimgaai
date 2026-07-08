import { useEffect, useRef, useState } from "react";

interface ExportButtonProps {
  sessionId: string;
}

export function ExportButton({ sessionId }: ExportButtonProps) {
  const [open, setOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
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

  const download = async (format: "md" | "pdf") => {
    setOpen(false);
    setError(null);
    setExporting(true);
    try {
      const res = await fetch(`/export/${sessionId}?format=${format}`);
      if (!res.ok) {
        let detail = "匯出失敗";
        try {
          const body = await res.json();
          if (typeof body.detail === "string") detail = body.detail;
        } catch {
          // ignore
        }
        throw new Error(detail);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `meeting-${sessionId.slice(0, 8)}.${format}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "匯出失敗");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        disabled={exporting}
        onClick={() => setOpen((v) => !v)}
        className="min-h-11 rounded-lg border border-slate-300 bg-white px-4 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
      >
        {exporting ? "匯出中…" : "📥 匯出報告"}
      </button>
      {error && (
        <p className="absolute right-0 top-full mt-1 w-48 text-xs text-red-600">
          {error}
        </p>
      )}
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
