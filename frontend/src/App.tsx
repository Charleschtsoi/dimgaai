import { useCallback, useMemo, useState } from "react";
import { DocumentUpload } from "./components/DocumentUpload";
import { ExportButton } from "./components/ExportButton";
import { OnboardingOverlay } from "./components/OnboardingOverlay";
import { SettingsPanel } from "./components/SettingsPanel";
import { TopBar } from "./components/TopBar";
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
  const [tutorialStep, setTutorialStep] = useState(0);
  const [tutorialSeen, setTutorialSeen] = useState(false);
  const [, setEngagementCount] = useState(0);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);

  const [config, setConfig] = useState<SessionConfig>({
    llm_provider: "gemini",
    embedding_provider: "google",
  });
  const [configError, setConfigError] = useState<string | null>(null);
  const [savingConfig, setSavingConfig] = useState(false);
  const [docCount, setDocCount] = useState(0);
  const [checking, setChecking] = useState(false);

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
          rawText: event.raw_text,
          isFinal: event.is_final,
          isFactualClaim: Boolean(event.is_factual_claim),
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
        const existingIdx = withoutInterim.findIndex(
          (l) => l.speaker === entry.speaker && l.text === entry.text,
        );
        if (existingIdx >= 0) {
          const next = [...withoutInterim];
          next[existingIdx] = entry;
          return next;
        }
        return [...withoutInterim, entry];
      });
    } else if (event.type === "claim") {
      setLines((prev) =>
        prev.map((l) =>
          l.isFinal && l.text === event.segment
            ? { ...l, isFactualClaim: event.classification === "factual_claim" }
            : l,
        ),
      );
    } else if (event.type === "verdict") {
      setChecking(false);
      setVerdicts((prev) => [...prev, event]);
    } else if (event.type === "questions") {
      setQuestions((prev) => [...prev, event]);
    } else if (event.type === "status" && event.message === "checking") {
      setChecking(true);
    }
  }, []);

  const { status, error, connectAndWait, disconnect, sendAudio } =
    useMeetingSocket({
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
          : config.llm_provider === "anthropic" &&
              config.embedding_provider === "openai"
            ? config.openai_api_key
            : config.openai_api_key,
      anthropic_api_key:
        config.llm_provider === "anthropic" ? config.llm_api_key : undefined,
      google_api_key:
        config.llm_provider === "gemini"
          ? config.llm_api_key
          : config.llm_provider === "anthropic" &&
              (config.embedding_provider ?? "google") === "google"
            ? config.google_api_key
            : config.google_api_key,
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
    if (!config.deepgram_api_key?.trim()) {
      setConfigError("請先在 API 設定輸入 Deepgram 金鑰");
      setSettingsOpen(true);
      return;
    }
    if (!config.llm_api_key?.trim()) {
      setConfigError("請先在 API 設定輸入 LLM 金鑰");
      setSettingsOpen(true);
      return;
    }
    try {
      await saveConfig();
      await connectAndWait();
      await start();
    } catch (e) {
      setConfigError(e instanceof Error ? e.message : "無法開始錄音");
    }
  };

  const handleStop = () => {
    stop();
    disconnect();
    setChecking(false);
    setEngagementCount((c) => {
      const next = c + 1;
      if (next >= 2) setShowInstallPrompt(true);
      return next;
    });
  };

  const handleToggleRecording = () => {
    if (isRecording) handleStop();
    else handleStart();
  };

  const headerNote = useMemo(
    () => (docCount > 0 ? `${docCount} 份參考文件已索引` : "可選：上傳參考 PDF 以啟用核查"),
    [docCount],
  );

  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col gap-4 overflow-x-hidden p-4">
      {!tutorialSeen && (
        <OnboardingOverlay
          step={tutorialStep}
          onNext={() => setTutorialStep((s) => s + 1)}
          onSkip={() => setTutorialSeen(true)}
          onOpenSettings={() => {
            setSettingsOpen(true);
            setTutorialStep(1);
          }}
        />
      )}

      {showInstallPrompt && tutorialSeen && (
        <div className="flex items-center justify-between rounded-lg bg-teal-50 px-4 py-3 text-sm text-teal-900">
          <span>可將 dimgaai 加入主畫面，方便下次使用。</span>
          <button
            type="button"
            onClick={() => setShowInstallPrompt(false)}
            className="min-h-11 rounded-lg px-3 text-teal-700 hover:bg-teal-100"
          >
            知道了
          </button>
        </div>
      )}

      <header className="flex flex-col gap-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-slate-900">dimgaai 點解</h1>
            <p className="text-xs text-slate-500">{headerNote}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <SettingsPanel
              config={config}
              onChange={setConfig}
              onSave={saveConfig}
              saving={savingConfig}
              error={configError}
              forceOpen={settingsOpen}
              onClose={() => setSettingsOpen(false)}
            />
            <ExportButton sessionId={sessionId} />
          </div>
        </div>
        <DocumentUpload sessionId={sessionId} onUploaded={setDocCount} />
      </header>

      <TopBar
        status={status}
        isRecording={isRecording}
        onToggleRecording={handleToggleRecording}
        error={error || micError || configError}
      />

      <main className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-[1fr_minmax(0,24rem)]">
        <TranscriptPanel lines={lines} />
        <VerdictSidebar
          verdicts={verdicts}
          questions={questions}
          checking={checking}
        />
      </main>
    </div>
  );
}
