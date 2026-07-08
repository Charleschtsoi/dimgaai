import { useEffect, useMemo, useState } from "react";
import type {
  EmbeddingProvider,
  LlmProvider,
  SessionConfig,
} from "../types/events";

interface SettingsPanelProps {
  config: SessionConfig;
  onChange: (config: SessionConfig) => void;
  onSave: () => Promise<void>;
  saving: boolean;
  error: string | null;
  forceOpen?: boolean;
  onClose?: () => void;
}

const STACK_INFO: Record<
  LlmProvider,
  { label: string; keys: string; note: string }
> = {
  gemini: {
    label: "Google Gemini（推薦 — 2 把金鑰）",
    keys: "2",
    note: "Deepgram（麥克風）+ Google（分析同文件核查）",
  },
  openai: {
    label: "OpenAI（2 把金鑰）",
    keys: "2",
    note: "Deepgram（麥克風）+ OpenAI（分析同文件核查）",
  },
  anthropic: {
    label: "Anthropic（3 把金鑰）",
    keys: "3",
    note: "Deepgram + Anthropic + 嵌入用金鑰（Google 或 OpenAI）",
  },
};

function providerLabel(provider: LlmProvider): string {
  if (provider === "openai") return "OpenAI";
  if (provider === "anthropic") return "Anthropic";
  return "Google Gemini";
}

function countConfiguredKeys(config: SessionConfig): { done: number; total: number } {
  const total = config.llm_provider === "anthropic" ? 3 : 2;
  let done = 0;
  if (config.deepgram_api_key?.trim()) done += 1;
  if (config.llm_api_key?.trim()) done += 1;
  if (config.llm_provider === "anthropic") {
    const embed = config.embedding_provider ?? "google";
    if (embed === "google" && config.google_api_key?.trim()) done += 1;
    if (embed === "openai" && config.openai_api_key?.trim()) done += 1;
  }
  return { done, total };
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
  const embeddingProvider = config.embedding_provider ?? "google";

  useEffect(() => {
    if (forceOpen) setOpen(true);
  }, [forceOpen]);

  const progress = useMemo(() => countConfiguredKeys(config), [config]);
  const stack = STACK_INFO[config.llm_provider];

  const close = () => {
    setOpen(false);
    onClose?.();
  };

  const update = (patch: Partial<SessionConfig>) => {
    onChange({ ...config, ...patch });
  };

  const selectStack = (provider: LlmProvider) => {
    update({
      llm_provider: provider,
      embedding_provider: provider === "anthropic" ? "google" : undefined,
    });
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
          <div className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-xl bg-white p-5 shadow-xl">
            <h3 className="mb-1 text-lg font-semibold">API 設定 (BYOK)</h3>
            <p className="mb-2 text-xs text-slate-500">
              金鑰只會用於此工作階段，不會儲存到伺服器。
            </p>
            <p className="mb-3 rounded-lg bg-teal-50 px-3 py-2 text-xs text-teal-800">
              已設定 {progress.done}/{progress.total} 把必需金鑰
            </p>

            <div className="space-y-3">
              <label className="block text-sm">
                <span className="mb-1 block font-medium text-slate-700">方案</span>
                <select
                  value={config.llm_provider}
                  onChange={(e) => selectStack(e.target.value as LlmProvider)}
                  className="min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="gemini">{STACK_INFO.gemini.label}</option>
                  <option value="openai">{STACK_INFO.openai.label}</option>
                  <option value="anthropic">{STACK_INFO.anthropic.label}</option>
                </select>
                <span className="mt-1 block text-xs text-slate-500">{stack.note}</span>
              </label>

              <p className="text-xs text-slate-600">
                麥克風轉錄：Deepgram（必需，即時粵語）
                <br />
                分析 / 核查 / 問題：{providerLabel(config.llm_provider)}（必需）
              </p>

              <label className="block text-sm">
                <span className="mb-1 block text-slate-600">
                  1. Deepgram API Key *
                </span>
                <input
                  type="password"
                  value={config.deepgram_api_key || ""}
                  onChange={(e) => update({ deepgram_api_key: e.target.value })}
                  className="min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  placeholder="console.deepgram.com"
                />
              </label>

              <label className="block text-sm">
                <span className="mb-1 block text-slate-600">
                  2. {providerLabel(config.llm_provider)} API Key *
                </span>
                <input
                  type="password"
                  value={config.llm_api_key || ""}
                  onChange={(e) => update({ llm_api_key: e.target.value })}
                  className="min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </label>

              {config.llm_provider === "anthropic" && (
                <>
                  <label className="block text-sm">
                    <span className="mb-1 block text-slate-600">
                      3. 文件嵌入（RAG）供應商
                    </span>
                    <select
                      value={embeddingProvider}
                      onChange={(e) =>
                        update({
                          embedding_provider: e.target.value as EmbeddingProvider,
                        })
                      }
                      className="min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    >
                      <option value="google">Google（推薦）</option>
                      <option value="openai">OpenAI</option>
                    </select>
                  </label>
                  <label className="block text-sm">
                    <span className="mb-1 block text-slate-600">
                      3.{" "}
                      {embeddingProvider === "google"
                        ? "Google API Key（嵌入）*"
                        : "OpenAI API Key（嵌入）*"}
                    </span>
                    <input
                      type="password"
                      value={
                        embeddingProvider === "google"
                          ? config.google_api_key || ""
                          : config.openai_api_key || ""
                      }
                      onChange={(e) =>
                        update(
                          embeddingProvider === "google"
                            ? { google_api_key: e.target.value }
                            : { openai_api_key: e.target.value },
                        )
                      }
                      className="min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                      placeholder={
                        embeddingProvider === "google"
                          ? "aistudio.google.com"
                          : "platform.openai.com"
                      }
                    />
                  </label>
                </>
              )}

              <details className="text-sm">
                <summary className="cursor-pointer text-slate-600">
                  進階（可選）
                </summary>
                <label className="mt-2 block text-sm">
                  <span className="mb-1 block text-slate-600">Tavily Key</span>
                  <input
                    type="password"
                    value={config.tavily_api_key || ""}
                    onChange={(e) => update({ tavily_api_key: e.target.value })}
                    className="min-h-11 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </label>
              </details>
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
