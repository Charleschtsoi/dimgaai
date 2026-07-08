import { useCallback, useMemo, useState } from "react";
import { DocumentUpload } from "./components/DocumentUpload";
import { ExportButton } from "./components/ExportButton";
import { MicControls } from "./components/MicControls";
import { SettingsPanel } from "./components/SettingsPanel";
import { TranscriptPanel } from "./components/TranscriptPanel";
import { VerdictSidebar } from "./components/VerdictSidebar";
import { useAudioCapture } from "./hooks/useAudioCapture";
import { useMeetingSocket } from "./hooks/useMeetingSocket";
import type {
  QuestionsEvent,
  ServerEvent,
  SessionConfig,
  TranscriptLine,
  VerdictEvent,
} from "./types/events";

function createSessionId() {
  return crypto.randomUUID();
}

export default function App() {
  const [sessionId] = useState(createSessionId);
  const [config, setConfig] = useState<SessionConfig>({
    llm_provider: "openai",
  });
  const [configError, setConfigError] = useState<string | null>(null);
  const [savingConfig, setSavingConfig] = useState(false);
  const [docCount, setDocCount] = useState(0);

  const [lines, setLines] = useState<TranscriptLine[]>([]);
  const [verdicts, setVerdicts] = useState<VerdictEvent[]>([]);
  const [questions, setQuestions] = useState<QuestionsEvent[]>([]);

  const handleEvent = useCallback((event: ServerEvent) => {
    if (event.type === "transcript") {
      setLines((prev) => {
        const interimIdx = prev.findIndex((l) => !l.isFinal);
        const entry: TranscriptLine = {
          id: event.is_final
            ? `final-${prev.length}-${Date.now()}`
            : "interim",
          speaker: event.speaker,
          text: event.text,
          isFinal: event.is_final,
        };
        if (!event.is_final) {
          if (interimIdx >= 0) {
            const next = [...prev];
            next[interimIdx] = entry;
            return next;
          }
          return [...prev, entry];
        }
        const withoutInterim = prev.filter((l) => l.isFinal);
        return [...withoutInterim, entry];
      });
    } else if (event.type === "verdict") {
      setVerdicts((prev) => [...prev, event]);
    } else if (event.type === "questions") {
      setQuestions((prev) => [...prev, event]);
    }
  }, []);

  const { status, error, connect, disconnect, sendAudio } = useMeetingSocket({
    sessionId,
    onEvent: handleEvent,
  });

  const { isRecording, micError, start, stop } = useAudioCapture(sendAudio);

  const saveConfig = async () => {
    setSavingConfig(true);
    setConfigError(null);
    const payload: SessionConfig = {
      ...config,
      openai_api_key:
        config.llm_provider === "openai"
          ? config.llm_api_key
          : config.openai_api_key,
      anthropic_api_key:
        config.llm_provider === "anthropic" ? config.llm_api_key : undefined,
    };
    try {
      const res = await fetch(`/session/${sessionId}/configure`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(
          typeof err.detail === "string" ? err.detail : "設定失敗",
        );
      }
    } catch (e) {
      setConfigError(e instanceof Error ? e.message : "設定失敗");
      throw e;
    } finally {
      setSavingConfig(false);
    }
  };

  const handleStart = async () => {
    if (config.deepgram_api_key || config.llm_api_key) {
      try {
        await saveConfig();
      } catch {
        return;
      }
    }
    connect();
    setTimeout(() => start(), 300);
  };

  const handleStop = () => {
    stop();
    disconnect();
  };

  const headerNote = useMemo(
    () => (docCount > 0 ? `${docCount} 份參考文件已索引` : "請先上傳參考 PDF"),
    [docCount],
  );

  return (
    <div className="mx-auto flex min-h-screen max-w-[1280px] flex-col gap-4 p-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">粵語會議支援 Agent</h1>
          <p className="text-xs text-slate-500">{headerNote}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <SettingsPanel
            config={config}
            onChange={setConfig}
            onSave={saveConfig}
            saving={savingConfig}
            error={configError}
          />
          <DocumentUpload sessionId={sessionId} onUploaded={setDocCount} />
          <ExportButton sessionId={sessionId} />
        </div>
      </header>

      <MicControls
        status={status}
        isRecording={isRecording}
        onStart={handleStart}
        onStop={handleStop}
        error={error || micError}
      />

      <main className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-[1fr_380px] lg:gap-4">
        <TranscriptPanel lines={lines} />
        <VerdictSidebar verdicts={verdicts} questions={questions} />
      </main>
    </div>
  );
}
