import { useEffect, useState } from "react";
import type { SessionConfig } from "../types/events";

interface SettingsPanelProps {
  config: SessionConfig;
  onChange: (config: SessionConfig) => void;
  onSave: () => Promise<void>;
  saving: boolean;
  error: string | null;
  forceOpen?: boolean;
  onClose?: () => void;
}

export function SettingsPanel({
  config,
  onChange,
  onSave,
  saving,
  error,
  forceOpen = false,
  onClose,
}: SettingsPanelProps) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (forceOpen) setOpen(true);
  }, [forceOpen]);

  const close = () => {
    setOpen(false);
    onClose?.();
  };

  const update = (patch: Partial<SessionConfig>) => {
    onChange({ ...config, ...patch });
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="min-h-11 rounded-lg border border-slate-300 bg-white px-4 text-sm text-slate-700 hover:bg-slate-50"
      >
        ⚙️ API 設定
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl">
            <h3 className="mb-1 text-lg font-semibold">API 設定 (BYOK)</h3>
            <p className="mb-4 text-xs text-slate-500">
              金鑰只會用於此工作階段，不會儲存到伺服器。
            </p>

            <div className="space-y-3">
              <label className="block text-sm">
                <span className="mb-1 block text-slate-600">Deepgram API Key *</span>
                <input
                  type="password"
                  value={config.deepgram_api_key || ""}
                  onChange={(e) => update({ deepgram_api_key: e.target.value })}
                  className="min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  placeholder="Deepgram key"
                />
              </label>

              <label className="block text-sm">
                <span className="mb-1 block text-slate-600">LLM Provider</span>
                <select
                  value={config.llm_provider}
                  onChange={(e) =>
                    update({ llm_provider: e.target.value as "openai" | "anthropic" })
                  }
                  className="min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                </select>
              </label>

              <label className="block text-sm">
                <span className="mb-1 block text-slate-600">
                  {config.llm_provider === "openai" ? "OpenAI" : "Anthropic"} API Key *
                </span>
                <input
                  type="password"
                  value={config.llm_api_key || ""}
                  onChange={(e) => update({ llm_api_key: e.target.value })}
                  className="min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </label>

              {config.llm_provider === "anthropic" && (
                <label className="block text-sm">
                  <span className="mb-1 block text-slate-600">
                    OpenAI Key (embeddings)
                  </span>
                  <input
                    type="password"
                    value={config.openai_api_key || ""}
                    onChange={(e) => update({ openai_api_key: e.target.value })}
                    className="min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    placeholder="Required for RAG embeddings"
                  />
                </label>
              )}

              <label className="block text-sm">
                <span className="mb-1 block text-slate-600">Tavily Key (optional)</span>
                <input
                  type="password"
                  value={config.tavily_api_key || ""}
                  onChange={(e) => update({ tavily_api_key: e.target.value })}
                  className="min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </label>
            </div>

            {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={close}
                className="min-h-11 rounded-lg px-4 text-sm text-slate-600 hover:bg-slate-100"
              >
                取消
              </button>
              <button
                type="button"
                disabled={saving}
                onClick={async () => {
                  try {
                    await onSave();
                    close();
                  } catch {
                    // keep open on error
                  }
                }}
                className="min-h-11 rounded-lg bg-teal-600 px-4 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
              >
                {saving ? "儲存中…" : "儲存"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
