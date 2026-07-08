interface ExportButtonProps {
  sessionId: string;
}

export function ExportButton({ sessionId }: ExportButtonProps) {
  const download = (format: "md" | "pdf") => {
    window.open(`/export/${sessionId}?format=${format}`, "_blank");
  };

  return (
    <div className="flex gap-2">
      <button
        type="button"
        onClick={() => download("md")}
        className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
      >
        匯出 Markdown
      </button>
      <button
        type="button"
        onClick={() => download("pdf")}
        className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
      >
        匯出 PDF
      </button>
    </div>
  );
}
