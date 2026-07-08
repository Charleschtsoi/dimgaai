import { useRef, useState } from "react";

interface DocumentUploadProps {
  sessionId: string;
  onUploaded: (count: number) => void;
}

export function DocumentUpload({ sessionId, onUploaded }: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleUpload = async (files: FileList | null) => {
    if (!files?.length) return;
    setUploading(true);
    setMessage(null);

    const form = new FormData();
    form.append("session_id", sessionId);
    for (const file of Array.from(files)) {
      form.append("files", file);
    }

    try {
      const res = await fetch("/documents", { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "上傳失敗");
      }
      const data = await res.json();
      setMessage(`已索引 ${data.documents} 份文件 (${data.chunks_indexed} 段)`);
      onUploaded(data.documents);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "上傳失敗");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div
      className={`min-h-11 rounded-lg border-2 border-dashed px-3 py-2 transition-colors ${
        dragOver ? "border-teal-500 bg-teal-50" : "border-slate-300 bg-white"
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        handleUpload(e.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        multiple
        className="hidden"
        onChange={(e) => handleUpload(e.target.files)}
      />
      <button
        type="button"
        disabled={uploading}
        onClick={() => inputRef.current?.click()}
        className="min-h-11 w-full rounded-lg text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
      >
        {uploading ? "上傳中…" : "📄 上傳參考文件（拖放 PDF）"}
      </button>
      {message && <p className="mt-1 text-xs text-slate-500">{message}</p>}
    </div>
  );
}
