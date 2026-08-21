"use client";

// R20 semantic contract retained: Runtime state is earned from a real Ollama handshake.
// R30 distills that proof into Glance → Inspect → Prove without changing runtime truth semantics.
import { useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Check,
  CheckCircle2,
  Clipboard,
  Clock3,
  Cpu,
  FileJson2,
  LoaderCircle,
  Network,
  Play,
  RefreshCw,
  Server,
  ShieldCheck,
  SquareTerminal,
  TriangleAlert,
  XCircle,
  Zap,
} from "lucide-react";
import { ProgressiveDisclosure, VisualMetric, type SignalTone } from "@/components/visual-primitives";
import { API_BASE_URL, type QwenExecutionRecord, type QwenTestResult, type RuntimeState } from "@/lib/api";

function tone(value: string | null | undefined): SignalTone {
  if (["READY", "CONNECTED", "AVAILABLE", "PASSED", "VALID", "SUCCESS"].includes(value ?? "")) return "ok";
  if (["NOT_INSTALLED", "NOT_CONFIGURED", "DEGRADED", "WAITING"].includes(value ?? "")) return "warn";
  if (["UNAVAILABLE", "FAILED", "INVALID", "BLOCKED"].includes(value ?? "")) return "bad";
  return "neutral";
}

function StateBadge({ value }: { value: string }) {
  const stateTone = tone(value);
  return (
    <span className={`runtime-state-inline-r71 tone-${stateTone}`}>
      <span className={`status-dot ${stateTone}`} />
      {value.replaceAll("_", " ")}
    </span>
  );
}

function formatMs(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return value >= 1000 ? `${(value / 1000).toFixed(value >= 10000 ? 1 : 2)} s` : `${Math.round(value)} ms`;
}

const RUNTIME_TIME_ZONE = "Asia/Kuala_Lumpur";
const RUNTIME_TIME_FORMATTER = new Intl.DateTimeFormat("en-MY", {
  timeZone: RUNTIME_TIME_ZONE,
  day: "2-digit",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: true,
});

function formatTime(value: string | null | undefined) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  // R35: fixed locale + timezone keeps SSR and hydration output identical.
  return RUNTIME_TIME_FORMATTER.format(date);
}

function isLoopback(url: string | null | undefined) {
  if (!url) return false;
  try {
    const host = new URL(url).hostname;
    return host === "localhost" || host === "127.0.0.1" || host === "::1";
  } catch {
    return false;
  }
}

export function AiRuntimeConsole({ initialRuntime }: { initialRuntime: RuntimeState | null }) {
  const [runtime, setRuntime] = useState<RuntimeState | null>(initialRuntime);
  const [prompt, setPrompt] = useState("Classify this as a CREED test and return structured JSON.");
  const [result, setResult] = useState<QwenTestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [testing, setTesting] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [selectedExecution, setSelectedExecution] = useState<QwenExecutionRecord | null>(runtime?.last_execution ?? null);

  const ready = runtime?.status === "READY";
  const recent = runtime?.recent_executions ?? (runtime?.last_execution ? [runtime.last_execution] : []);
  const loopback = isLoopback(runtime?.ollama_base_url);
  const recentFailures = recent.filter((item) => !item.success).length;
  const lastSuccessful = useMemo(
    () => recent.find((record) => record.success) ?? (runtime?.last_execution?.success ? runtime.last_execution : null),
    [recent, runtime?.last_execution],
  );

  async function refreshRuntime() {
    setRefreshing(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/ai/runtime?refresh=true`, { cache: "no-store" });
      if (!response.ok) throw new Error(`Runtime check failed (${response.status})`);
      const next = (await response.json()) as RuntimeState;
      setRuntime(next);
      if (next.last_execution) setSelectedExecution(next.last_execution);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Runtime check failed");
    } finally {
      setRefreshing(false);
    }
  }

  async function runTest() {
    setTesting(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/ai/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? `Qwen test failed (${response.status})`);
      const testResult = body as QwenTestResult;
      setResult(testResult);
      const runtimeResponse = await fetch(`${API_BASE_URL}/api/v1/ai/runtime?refresh=false`, { cache: "no-store" });
      if (runtimeResponse.ok) {
        const next = (await runtimeResponse.json()) as RuntimeState;
        setRuntime(next);
        const matched = next.recent_executions?.find((record) => record.run_id === testResult.run_id) ?? next.last_execution;
        if (matched) setSelectedExecution(matched);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Qwen test failed");
    } finally {
      setTesting(false);
    }
  }

  async function copyValue(key: string, value: string) {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(key);
      window.setTimeout(() => setCopied((current) => (current === key ? null : current)), 1600);
    } catch {
      setCopied(null);
    }
  }

  return (
    <div className="runtime-r30">
      <header className="runtime-hero-r30">
        <div className="runtime-hero-copy-r30">
          <h1>Local Qwen. Prove it live.</h1>
          <p>Handshake, execute, inspect proof.</p>
          <div className="runtime-hero-meta-r71 editorial-meta-group-r71">
            <span className={`editorial-meta-r71 ${loopback ? "tone-ok" : ""}`}><Network size={14} aria-hidden="true" />{loopback ? "LOOPBACK" : "CONFIGURED"}</span>
            <span className={`editorial-meta-r71 tone-${tone(runtime?.model)}`}><Cpu size={14} aria-hidden="true" />{runtime?.configured_model ?? "Model unavailable"}</span>
          </div>
        </div>

        <div className={`runtime-verdict-r30 tone-${ready ? "ok" : "bad"}`} role="status" aria-live="polite">
          {ready ? <ShieldCheck size={22} aria-hidden="true" /> : <TriangleAlert size={22} aria-hidden="true" />}
          <span>AI ENGINE</span>
          <strong>{runtime?.status ?? "UNAVAILABLE"}</strong>
          <span className="sr-only">READY requires Ollama, the configured Qwen model and schema-validated inference.</span>
          <button type="button" className="ghost-btn" onClick={refreshRuntime} disabled={refreshing}>
            {refreshing ? <LoaderCircle className="spin" size={14} /> : <RefreshCw size={14} />}
            {refreshing ? "Checking" : "Refresh"}
          </button>
        </div>
      </header>

      <section className="runtime-proof-flow-r30" aria-label="AI runtime proof flow">
        <ProofNode icon={Server} label="Ollama" value={runtime?.ollama ?? "UNAVAILABLE"} />
        <ArrowRight size={15} aria-hidden="true" />
        <ProofNode icon={Cpu} label="Qwen" value={runtime?.model ?? "UNAVAILABLE"} />
        <ArrowRight size={15} aria-hidden="true" />
        <ProofNode icon={FileJson2} label="Schema" value={runtime?.inference ?? "UNAVAILABLE"} />
        <ArrowRight size={15} aria-hidden="true" />
        <ProofNode icon={ShieldCheck} label="CREED" value={ready ? "READY" : "BLOCKED"} />
      </section>

      <section className="runtime-glance-r30" aria-label="AI runtime signals">
        <VisualMetric
          icon={Cpu}
          label="Model"
          value={runtime?.actual_model ?? runtime?.configured_model ?? "—"}
          meta={runtime?.actual_model ? "returned by Ollama" : "configured"}
          tone={tone(runtime?.model)}
        />
        <VisualMetric
          icon={Clock3}
          label="Last inference"
          value={formatMs(runtime?.last_inference_duration_ms)}
          meta={runtime?.checked_at ? formatTime(runtime.checked_at) : "No proof yet"}
          tone={tone(runtime?.inference)}
        />
        <VisualMetric
          icon={Activity}
          label="Executions"
          value={String(runtime?.execution_count ?? recent.length)}
          meta={recentFailures ? `${recentFailures} recent failure${recentFailures === 1 ? "" : "s"}` : "No recent failures"}
          tone={recentFailures ? "warn" : "ok"}
        />
      </section>

      {(runtime?.last_error || error) && (
        <div className="runtime-alert-r30" role="alert">
          <AlertTriangle size={17} aria-hidden="true" />
          <div>
            <strong>Runtime proof failed</strong>
            <span>{error ?? runtime?.last_error}</span>
          </div>
        </div>
      )}

      {!ready && runtime && (
        <section className="runtime-recovery-min-r30">
          <div className="runtime-recovery-head-r30">
            <SquareTerminal size={17} aria-hidden="true" />
            <div>
              <strong>Recovery</strong>
              <span>Restore the real runtime, then refresh proof.</span>
            </div>
          </div>
          <div className="runtime-recovery-steps-r30">
            <span><b>1</b> Start Ollama</span>
            {runtime.model === "NOT_INSTALLED" ? <code>ollama pull {runtime.configured_model}</code> : null}
            <span><b>{runtime.model === "NOT_INSTALLED" ? "3" : "2"}</b> Refresh proof</span>
          </div>
        </section>
      )}

      <section className="card runtime-live-r30" aria-busy={testing}>
        <div className="runtime-live-head-r30">
          <div>
            <h2>Execute Qwen</h2>
          </div>
          <span className={`editorial-meta-r71 tone-${testing ? "warn" : result?.structured_output_valid ? "ok" : "neutral"}`}><Activity size={14} aria-hidden="true" />{testing ? "RUNNING" : result ? "PROOF CAPTURED" : "READY TO TEST"}</span>
        </div>

        <div className="runtime-live-grid-r30">
          <div className="runtime-live-input-r30">
            <label htmlFor="qwen-test-r30">Prompt</label>
            <textarea id="qwen-test-r30" value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={5} />
            <div className="runtime-live-actions-r30">
              <small>{prompt.length} / 4000</small>
              <button type="button" className="primary-btn" onClick={runTest} disabled={testing || prompt.trim().length < 3 || prompt.length > 4000}>
                {testing ? <LoaderCircle className="spin" size={15} /> : <Play size={15} />}
                {testing ? "Executing" : "Run Qwen"}
              </button>
            </div>
          </div>

          <div className="runtime-live-output-r30" aria-live="polite">
            {!result && !testing && !error ? (
              <div className="runtime-proof-empty-r30">
                <FileJson2 size={24} aria-hidden="true" />
                <strong>Run a real structured test</strong>
                <span>The backend result appears here.</span>
              </div>
            ) : null}

            {testing ? (
              <div className="runtime-proof-empty-r30 active" role="status">
                <LoaderCircle className="spin" size={24} aria-hidden="true" />
                <strong>Qwen is executing</strong>
                <span>Waiting for the backend. No simulated completion timer is used.</span>
              </div>
            ) : null}

            {result ? (
              <div className="runtime-result-r30">
                <div className="runtime-result-signal-r30">
                  <span className={`runtime-result-icon-r30 ${result.structured_output_valid ? "ok" : "bad"}`}>
                    {result.structured_output_valid ? <CheckCircle2 size={20} /> : <XCircle size={20} />}
                  </span>
                  <div>
                    <span>CLASSIFICATION</span>
                    <strong>{result.output.classification}</strong>
                  </div>
                  <StateBadge value={result.structured_output_valid ? "PASSED" : "INVALID"} />
                </div>

                <div className="runtime-result-glance-r30">
                  <Metric icon={<Clock3 size={13} />} label="Duration" value={formatMs(result.duration_ms)} />
                  <Metric icon={<Zap size={13} />} label="Tokens" value={`${result.prompt_eval_count ?? "?"} / ${result.eval_count ?? "?"}`} />
                  <Metric icon={<Cpu size={13} />} label="Model" value={result.actual_model ?? result.configured_model} />
                </div>

                <ProgressiveDisclosure label="JSON proof" meta="schema output">
                  <pre className="runtime-json-r30">{JSON.stringify(result.output, null, 2)}</pre>
                  <button type="button" className="runtime-copy-run-r30" onClick={() => copyValue("test-run", result.run_id)}>
                    {copied === "test-run" ? <Check size={13} /> : <Clipboard size={13} />}
                    <span>{result.run_id}</span>
                  </button>
                </ProgressiveDisclosure>
              </div>
            ) : null}
          </div>
        </div>
      </section>

      <section className="runtime-history-r30" data-legacy-contract="runtime-execution-metrics-r20">
        <div className="runtime-history-head-r30">
          <div>
            <h2>Recent Qwen calls</h2>
          </div>
          <span className={`editorial-meta-r71 tone-${recentFailures ? "warn" : "ok"}`}><Activity size={14} aria-hidden="true" />{recent.length} shown</span>
        </div>

        {recent.length === 0 ? (
          <div className="runtime-history-empty-r30">
            <Activity size={20} aria-hidden="true" />
            <strong>No execution proof yet</strong>
            <span>Runtime probes and Qwen calls appear after real execution.</span>
          </div>
        ) : (
          <div className="runtime-history-list-r30">
            {recent.map((execution, index) => (
              <button
                type="button"
                key={`${execution.run_id}-${index}`}
                className={`runtime-execution-r30 ${selectedExecution?.run_id === execution.run_id ? "selected" : ""}`}
                onClick={() => setSelectedExecution(execution)}
                aria-pressed={selectedExecution?.run_id === execution.run_id}
              >
                <span className={`runtime-execution-icon-r30 ${execution.success ? "ok" : "bad"}`}>
                  {execution.success ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
                </span>
                <div className="runtime-execution-copy-r30">
                  <strong>{execution.node.replaceAll("_", " ")}</strong>
                  <span>{execution.actual_model ?? execution.configured_model}</span>
                </div>
                <div className="runtime-execution-meta-r36">
                  <b>{formatMs(execution.duration_ms)}</b>
                  <time dateTime={execution.completed_at ?? undefined}>{formatTime(execution.completed_at)}</time>
                </div>
                <ArrowRight size={14} aria-hidden="true" />
              </button>
            ))}
          </div>
        )}

        {selectedExecution ? (
          <div className="runtime-selected-r30">
            <div className="runtime-selected-head-r30">
              <div>
                <h3>{selectedExecution.node.replaceAll("_", " ")}</h3>
              </div>
              <StateBadge value={selectedExecution.success ? "SUCCESS" : "FAILED"} />
            </div>

            <div className="runtime-selected-glance-r30">
              <VisualMetric icon={Clock3} label="Duration" value={formatMs(selectedExecution.duration_ms)} tone={selectedExecution.success ? "ok" : "bad"} />
              <VisualMetric icon={Zap} label="Tokens" value={`${selectedExecution.prompt_eval_count ?? "?"} / ${selectedExecution.eval_count ?? "?"}`} meta="input / output" />
              <VisualMetric icon={FileJson2} label="Structured" value={selectedExecution.structured_output_valid ? "VALID" : "INVALID"} tone={selectedExecution.structured_output_valid ? "ok" : "bad"} />
            </div>

            <ProgressiveDisclosure label="Runtime provenance" meta="model · run · timing">
              <div className="runtime-detail-grid-r30">
                <DetailRow label="Run ID" value={selectedExecution.run_id} mono />
                <DetailRow label="Configured model" value={selectedExecution.configured_model} />
                <DetailRow label="Actual model" value={selectedExecution.actual_model ?? "—"} />
                <DetailRow label="Started" value={formatTime(selectedExecution.started_at)} />
                <DetailRow label="Completed" value={formatTime(selectedExecution.completed_at)} />
                {selectedExecution.load_duration_ns !== null ? (
                  <DetailRow label="Model load" value={formatMs(selectedExecution.load_duration_ns / 1_000_000)} />
                ) : null}
              </div>
              {selectedExecution.error ? (
                <div className="runtime-selected-error-r30"><AlertTriangle size={15} /><span>{selectedExecution.error}</span></div>
              ) : null}
            </ProgressiveDisclosure>
          </div>
        ) : null}
      </section>

      <footer className="runtime-boundary-note-r30">
        <ShieldCheck size={16} aria-hidden="true" />
        <span><strong>Local AI boundary.</strong> LOOPBACK is verified from the configured endpoint; other endpoints remain CONFIGURED. <strong>No fake AI fallback.</strong> Failed or unavailable Qwen execution stays failed.</span>
        {lastSuccessful ? <span className="editorial-meta-r71 tone-ok"><CheckCircle2 size={14} aria-hidden="true" />Last proof {formatMs(lastSuccessful.duration_ms)}</span> : null}
      </footer>
    </div>
  );
}

function ProofNode({ icon: Icon, label, value }: { icon: typeof Server; label: string; value: string }) {
  const nodeTone = tone(value);
  return (
    <div className={`runtime-proof-node-r30 tone-${nodeTone}`}>
      <span><Icon size={17} aria-hidden="true" /></span>
      <div><small>{label}</small><strong>{value.replaceAll("_", " ")}</strong></div>
    </div>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return <div className="runtime-metric-r30"><span>{icon}{label}</span><strong>{value}</strong></div>;
}

function DetailRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return <div className="runtime-detail-r30"><span>{label}</span><strong className={mono ? "mono" : ""}>{value}</strong></div>;
}
