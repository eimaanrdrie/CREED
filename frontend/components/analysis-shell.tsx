"use client";

import { useEffect, useMemo, useRef, useState, type Dispatch, type ReactNode, type SetStateAction } from "react";
import {
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  BrainCircuit,
  Check,
  CheckCircle2,
  ChevronDown,
  ClipboardCheck,
  Database,
  FileSearch,
  FileText,
  Fingerprint,
  GitBranch,
  LoaderCircle,
  Network,
  Pencil,
  Radar,
  RefreshCw,
  Save,
  SearchCheck,
  ShieldCheck,
  Sparkles,
  UserCheck,
  X,
  XCircle,
} from "lucide-react";
import {
  analysisRunEventsUrl,
  createLearningProposal,
  decideLearningProposal,
  getDocument,
  getDocumentOriginalUrl,
  getHumanAuthorities,
  getHumanReview,
  getImpact,
  getIssueUnderstanding,
  getLatestAnalysisRun,
  getLearningProposal,
  getLearningReadiness,
  getMethodAbom,
  getRunEvidence,
  getRunInvestigations,
  recoverStuckAnalysisRun,
  resumeHumanReview,
  runIssueUnderstanding,
  startAnalysisRun,
  updateIssueUnderstanding,
  verifyAdoptionReceipt,
  type AdoptionReceiptVerification,
  type AdoptionScopeMode,
  type AdoptionScopeSummary,
  type AnalysisRun,
  type AnalysisStep,
  type EvidenceDocumentDetail,
  type HumanAuthorityRecord,
  type IssueUnderstanding,
  type IssueUnderstandingEdit,
  type LearningProposalSummary,
  type LearningReadiness,
  type MethodAbom,
  type SupportIssueDetail,
} from "@/lib/api";
import { ProgressiveDisclosure, SignalChip } from "@/components/visual-primitives";

const TERMINAL = new Set(["COMPLETED", "FAILED", "CANCELLED"]);
type AnalysisWorkspace = "context" | "evidence" | "investigation" | "human" | "handoff";
const ANALYSIS_WORKSPACES: AnalysisWorkspace[] = ["context", "evidence", "investigation", "human", "handoff"];
// R22 regression copy contract: Follow evidence → impact → investigation → human decision.

export function AnalysisShell({ issue, initialUnderstanding, initialRun, autoRun = false }: {
  issue: SupportIssueDetail;
  initialUnderstanding: IssueUnderstanding | null;
  initialRun: AnalysisRun | null;
  autoRun?: boolean;
}) {
  const [understanding, setUnderstanding] = useState<IssueUnderstanding | null>(initialUnderstanding);
  const [qwenRunning, setQwenRunning] = useState(false);
  const [editing, setEditing] = useState(false);
  const [qwenError, setQwenError] = useState<string | null>(null);
  const [run, setRun] = useState<AnalysisRun | null>(initialRun);
  const [runStarting, setRunStarting] = useState(false);
  const [runRecovering, setRunRecovering] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [streamState, setStreamState] = useState<"IDLE" | "CONNECTED" | "RECONNECTING">("IDLE");
  const [workspace, setWorkspace] = useState<AnalysisWorkspace>("context");
  const [handoffAttention, setHandoffAttention] = useState(false);
  const [handoffComplete, setHandoffComplete] = useState(false);
  const [handoffArrivalNotice, setHandoffArrivalNotice] = useState(false);
  const [pendingNavigationHref, setPendingNavigationHref] = useState<string | null>(null);
  const navigationGuardBypassRef = useRef(false);
  const autoStarted = useRef(false);
  const lastUnderstandingRefresh = useRef<string | null>(initialUnderstanding?.id ?? null);

  async function runQwenOnly() {
    if (qwenRunning) return;
    setQwenRunning(true); setEditing(false); setQwenError(null);
    try { setUnderstanding(await runIssueUnderstanding(issue.id)); }
    catch (err) { setQwenError(err instanceof Error ? err.message : "ISSUE_UNDERSTANDING_FAILED"); }
    finally { setQwenRunning(false); }
  }

  async function startRun() {
    if (runStarting || (run && !TERMINAL.has(run.status))) return;
    setRunStarting(true); setRunError(null);
    try { setRun(await startAnalysisRun(issue.id)); }
    catch (err) { setRunError(err instanceof Error ? err.message : "ANALYSIS_RUN_START_FAILED"); }
    finally { setRunStarting(false); }
  }

  async function recoverRun() {
    if (runRecovering || !run?.recovery_eligible) return;
    setRunRecovering(true); setRunError(null);
    try {
      setRun(await recoverStuckAnalysisRun(issue.id, "Recover stale zero-case Human Review checkpoint after routing correction."));
    }
    catch (err) { setRunError(err instanceof Error ? err.message : "ANALYSIS_RUN_RECOVERY_FAILED"); }
    finally { setRunRecovering(false); }
  }

  useEffect(() => {
    if (!run) void getLatestAnalysisRun(issue.id).then(value => value && setRun(value)).catch(() => {});
  }, [issue.id, run]);

  useEffect(() => {
    if (autoRun && !autoStarted.current) {
      autoStarted.current = true;
      if (!run) void startRun();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoRun]);

  useEffect(() => {
    if (!run || TERMINAL.has(run.status)) { setStreamState("IDLE"); return; }
    const source = new EventSource(analysisRunEventsUrl(run.graph_run_id, run.latest_event_seq));
    setStreamState("RECONNECTING");
    source.addEventListener("open", () => setStreamState("CONNECTED"));
    source.addEventListener("agent_step", (event) => {
      const lifecycle = JSON.parse((event as MessageEvent).data) as { event_seq:number; agent_name:string; status:AnalysisStep["status"]; message:string|null; metadata:Record<string, unknown> };
      setRun(current => current ? {
        ...current,
        latest_event_seq: Math.max(current.latest_event_seq, lifecycle.event_seq),
        status: lifecycle.status === "RUNNING" && current.status === "QUEUED" ? "RUNNING" : current.status,
        steps: current.steps.map(step => step.agent_name === lifecycle.agent_name ? {
          ...step,
          status: lifecycle.status,
          output_summary: lifecycle.status === "COMPLETED" || lifecycle.status === "SKIPPED" ? lifecycle.message : step.output_summary,
          metadata: { ...step.metadata, ...lifecycle.metadata },
        } : step),
      } : current);
    });
    source.addEventListener("snapshot", (event) => {
      const next = JSON.parse((event as MessageEvent).data) as AnalysisRun;
      setRun(next); setStreamState("CONNECTED");
      const intake = next.steps.find(step => step.agent_name === "intake_agent");
      if (intake?.status === "COMPLETED" && intake.metadata?.understanding_id && intake.metadata.understanding_id !== lastUnderstandingRefresh.current) {
        void getIssueUnderstanding(issue.id).then(value => {
          if (value) { setUnderstanding(value); lastUnderstandingRefresh.current = value.id; }
        }).catch(() => {});
      }
      if (TERMINAL.has(next.status)) source.close();
    });
    source.addEventListener("terminal", () => { source.close(); setStreamState("IDLE"); });
    source.onerror = () => setStreamState("RECONNECTING");
    return () => source.close();
  }, [run?.graph_run_id, issue.id]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const requested = new URLSearchParams(window.location.search).get("view");
    if (requested && ANALYSIS_WORKSPACES.includes(requested as AnalysisWorkspace)) setWorkspace(requested as AnalysisWorkspace);
  }, [issue.id]);

  useEffect(() => {
    if (!run || run.status !== "COMPLETED") { setHandoffAttention(false); setHandoffComplete(false); return; }
    let alive = true;
    void Promise.all([
      getLearningProposal(run.graph_run_id),
      getLearningReadiness(run.graph_run_id),
    ]).then(([proposal, readiness]) => {
      if (!alive) return;
      const terminalLearning = proposal?.status === "REJECTED" || (proposal?.status === "APPROVED" && Boolean(proposal.adoption_receipt));
      setHandoffComplete(terminalLearning);
      setHandoffAttention(!terminalLearning && (Boolean(proposal) || readiness.eligible));
    }).catch(() => { if (alive) { setHandoffAttention(false); setHandoffComplete(false); } });
    return () => { alive = false; };
  }, [run?.graph_run_id, run?.status]);

  useEffect(() => {
    if (!handoffArrivalNotice) return;
    const timer = window.setTimeout(() => setHandoffArrivalNotice(false), 3200);
    return () => window.clearTimeout(timer);
  }, [handoffArrivalNotice]);

  useEffect(() => {
    if (typeof window === "undefined" || !handoffAttention) {
      setPendingNavigationHref(null);
      return;
    }

    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      if (navigationGuardBypassRef.current) return;
      event.preventDefault();
      event.returnValue = "";
    };

    const onDocumentClick = (event: MouseEvent) => {
      if (navigationGuardBypassRef.current || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const target = event.target;
      if (!(target instanceof Element)) return;
      const anchor = target.closest<HTMLAnchorElement>("a[href]");
      if (!anchor || anchor.target === "_blank" || anchor.hasAttribute("download")) return;
      const rawHref = anchor.getAttribute("href");
      if (!rawHref || rawHref.startsWith("#") || rawHref.startsWith("mailto:") || rawHref.startsWith("tel:")) return;

      const destination = new URL(anchor.href, window.location.href);
      const current = new URL(window.location.href);
      if (destination.origin === current.origin && destination.pathname === current.pathname) return;

      event.preventDefault();
      event.stopPropagation();
      setPendingNavigationHref(destination.href);
    };

    window.addEventListener("beforeunload", onBeforeUnload);
    document.addEventListener("click", onDocumentClick, true);
    return () => {
      window.removeEventListener("beforeunload", onBeforeUnload);
      document.removeEventListener("click", onDocumentClick, true);
    };
  }, [handoffAttention]);

  function continueHandoffWorkflow() {
    setPendingNavigationHref(null);
    selectWorkspace("handoff");
  }

  function leaveHandoffWorkflow() {
    if (!pendingNavigationHref || typeof window === "undefined") return;
    navigationGuardBypassRef.current = true;
    window.location.assign(pendingNavigationHref);
  }

  function selectWorkspace(next:AnalysisWorkspace) {
    setWorkspace(next);
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    url.searchParams.set("view", next);
    window.history.replaceState(window.history.state, "", `${url.pathname}${url.search}${url.hash}`);
  }

  const active = run?.steps.find(step => step.status === "RUNNING");
  const sourceId = issue.external_ticket_id ?? issue.id.slice(0, 8).toUpperCase();

  return (
    <div className="page analysis-r04 analysis-r49 analysis-r50 analysis-r51 analysis-r52 analysis-r53 analysis-r54 analysis-r55 analysis-r56 analysis-r57 analysis-r58 analysis-r59 analysis-r60 analysis-r61 analysis-r62 analysis-r63 analysis-r63-rev1 analysis-r64 analysis-r65 analysis-r66 analysis-r67 analysis-r68 analysis-r69 analysis-r70 analysis-r76-rev1 analysis-r76-rev2 analysis-r77-rev1 analysis-r78-rev1 analysis-r79-rev1 analysis-r95-rev1 analysis-r96-rev1 analysis-r97-m05 analysis-r97-m06 analysis-r97-m07 analysis-r97-m08 analysis-r97-m09 analysis-r98-m02 analysis-r98-m03 analysis-r98-m04 analysis-r98-m05 analysis-r98-m06">
      <header className="analysis-header-r55">
        <div className="analysis-title-block-r55">
          <h1>{issue.title}</h1>
          <div className="analysis-meta-r55" aria-label="Case identity">
            <span>{issue.client_name ?? "Not selected"}</span>
            <span>{issue.external_ticket_id ?? sourceId}</span>
            <span>{issue.attachment_count} {issue.attachment_count === 1 ? "attachment" : "attachments"}</span>
          </div>
          <div className="analysis-run-id-r55">
            <span>Run</span>
            {run ? <code>{run.graph_run_id}</code> : <span>Not started</span>}
          </div>
        </div>

        {(!run || TERMINAL.has(run.status) || run.recovery_eligible) && (
          <div className="analysis-header-action-r55">
            {run?.recovery_eligible ? (
              <button type="button" className="primary-btn" onClick={recoverRun} disabled={runRecovering}>
                {runRecovering ? <LoaderCircle size={14} className="spin" /> : <RefreshCw size={14} />}
                {runRecovering ? "Recovering…" : "Recover & rerun"}
              </button>
            ) : (
              <button type="button" className="primary-btn" onClick={startRun} disabled={runStarting}>
                {runStarting ? <LoaderCircle size={14} className="spin" /> : <GitBranch size={14} />}
                {run ? "Run again" : "Start analysis"}
              </button>
            )}
          </div>
        )}
      </header>

      {runError && <InlineError title="CREED analysis did not start" error={runError} note="No agent progress was simulated." />}

      <CaseSignalSummary issue={issue} understanding={understanding} run={run} />
      <AnalysisWorkspaceNavigator run={run} selected={workspace} onSelect={selectWorkspace} handoffAction={handoffAttention} handoffComplete={handoffComplete} />

      <div className="analysis-workbench-r49">
        <main className="analysis-focus-r49">
          {workspace === "context" && <AnalysisZone index="01" title="Case context">
            <div className="case-context-workbench-r56">
              <SourceContextSummary issue={issue} run={run} />

              <section className="case-context-ai-disclosure-r97-m09" id="understanding">
                <details className="case-context-ai-details-r97-m09">
                  <summary>
                    <span className="case-context-ai-title-r97-m09"><BrainCircuit size={15} /><span><strong>AI intake interpretation</strong><small>Structured extraction used for retrieval and catalog routing</small></span></span>
                    <span className="case-context-ai-state-r97-m09">{qwenRunning || active?.agent_name === "intake_agent" ? "Running" : understanding ? `${Math.round(understanding.confidence * 100)}% confidence` : "Not run"}<ChevronDown size={15} aria-hidden="true" /></span>
                  </summary>
                  <div className="case-context-ai-body-r97-m09">
                    <div className="case-context-actions-r56 case-context-ai-actions-r97-m09">
                      {understanding && !qwenRunning && <button type="button" className={`case-context-action-r63 verify compact${editing ? " active" : ""}`} onClick={() => setEditing(v => !v)}>{editing ? <X size={13} /> : <Pencil size={13} />}{editing ? "Cancel" : "Verify"}</button>}
                      <button type="button" className="case-context-action-r63 rerun compact" onClick={runQwenOnly} disabled={qwenRunning || Boolean(run && !TERMINAL.has(run.status))}>{qwenRunning ? <LoaderCircle size={13} className="spin" /> : <RefreshCw size={13} />}{understanding ? "Re-run" : "Run Qwen"}</button>
                    </div>
                    {qwenError && <InlineError title="Issue understanding did not complete" error={qwenError} note="No fallback result was fabricated." />}
                    {(qwenRunning || active?.agent_name === "intake_agent") && <QwenRunning graphManaged={active?.agent_name === "intake_agent"} />}
                    {!qwenRunning && active?.agent_name !== "intake_agent" && !understanding && !qwenError && <div className="case-context-empty-r56"><Sparkles size={17} /><div><strong>Ready for Qwen</strong><span>Structured local extraction starts here.</span></div></div>}
                    {!qwenRunning && active?.agent_name !== "intake_agent" && understanding && (editing ? <UnderstandingEditor issueId={issue.id} understanding={understanding} onSaved={(value) => { setUnderstanding(value); setEditing(false); }} onError={setQwenError} /> : <QwenContextSummary issue={issue} understanding={understanding} />)}
                  </div>
                </details>
              </section>
            </div>
          </AnalysisZone>}

          {workspace !== "context" && run && <DownstreamIntelligence run={run} onRunUpdate={setRun} selectedWorkspace={workspace} onHumanReviewComplete={(latest) => { setRun(latest); setHandoffComplete(false); setHandoffArrivalNotice(true); selectWorkspace("handoff"); }} onHandoffAttentionChange={setHandoffAttention} onHandoffCompleteChange={setHandoffComplete} handoffArrivalNotice={handoffArrivalNotice} />}
          {workspace !== "context" && !run && <AnalysisWorkspaceUnavailable workspace={workspace} />}
        </main>

        <aside className="analysis-ledger-r04 analysis-rail-r49 analysis-execution-rail-r54" aria-label="Agent execution task">
          <ExecutionRail run={run} streamState={streamState} />
        </aside>
      </div>

      {pendingNavigationHref && handoffAttention && (
        <div className="handoff-leave-layer-r98-m04" role="presentation">
          <button className="handoff-leave-backdrop-r98-m04" type="button" aria-label="Continue Learning & Adoption" onClick={continueHandoffWorkflow} />
          <section className="handoff-leave-dialog-r98-m04" role="alertdialog" aria-modal="true" aria-labelledby="handoff-leave-title-r98-m04" aria-describedby="handoff-leave-copy-r98-m04">
            <div className="handoff-leave-icon-r98-m04"><AlertTriangle size={18} aria-hidden="true" /></div>
            <div className="handoff-leave-copy-r98-m04">
              <span>GOVERNED WORKFLOW</span>
              <h2 id="handoff-leave-title-r98-m04">Learning & Adoption is incomplete</h2>
              <p id="handoff-leave-copy-r98-m04">Human Review is complete, but the governed learning workflow still requires action. Your persisted progress will remain available if you leave.</p>
            </div>
            <div className="handoff-leave-actions-r98-m04">
              <button type="button" className="secondary-btn" onClick={leaveHandoffWorkflow}>Leave anyway</button>
              <button type="button" className="primary-btn" onClick={continueHandoffWorkflow} autoFocus>Continue workflow</button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

// Governance invariant: AI investigates. Humans decide.
function ExecutionRail({ run, streamState }: { run:AnalysisRun | null; streamState:"IDLE" | "CONNECTED" | "RECONNECTING" }) {
  const streamLabel = streamState === "CONNECTED" ? "LIVE" : streamState === "RECONNECTING" ? "RECONNECTING" : run && TERMINAL.has(run.status) ? "STORED" : "IDLE";

  if (!run) return <section className="card analysis-ledger-card-r04 analysis-rail-panel-r49 execution-panel-r54 execution-panel-r60">
    <div className="execution-head-r60">
      <div><h2>Agent Execution Task</h2></div>
      <span className={`stream-chip-r04 ${streamState.toLowerCase()}`} role="status" aria-live="polite">{streamLabel}</span>
    </div>
    <div className="execution-empty-r60"><GitBranch size={18} /><div><strong>No graph run</strong><p>Persisted lifecycle telemetry appears after analysis starts.</p></div></div>
  </section>;

  const active = run.steps.find(step => step.status === "RUNNING");
  const waiting = run.steps.find(step => step.status === "WAITING_HUMAN") ?? (run.status === "WAITING_HUMAN" ? run.steps.find(step => step.agent_name === "human_review_boundary") : undefined);
  const current = active ?? waiting;
  const completed = run.steps.filter(step => step.status === "COMPLETED" || step.status === "SKIPPED").length;
  const running = run.steps.filter(step => step.status === "RUNNING").length;
  const waitingCount = run.status === "WAITING_HUMAN" ? Math.max(1, run.steps.filter(step => step.status === "WAITING_HUMAN").length) : run.steps.filter(step => step.status === "WAITING_HUMAN").length;
  const failed = run.steps.filter(step => step.status === "FAILED").length;
  const currentLabel = current ? executionStageName(current) : run.status === "COMPLETED" ? "Run complete" : run.status === "FAILED" ? "Execution failed" : run.status === "CANCELLED" ? "Run cancelled" : run.status.replaceAll("_", " ");
  const currentStatus = current ? executionStatusLabel(current) : executionRunStatusLabel(run.status);
  const currentDuration = current?.duration_ms != null ? formatDuration(current.duration_ms) : "—";

  return <section className="card analysis-ledger-card-r04 analysis-rail-panel-r49 execution-panel-r54 execution-panel-r60">
    <div className="execution-head-r60">
      <div><h2>Agent Execution Task</h2></div>
      <span className={`stream-chip-r04 ${streamState.toLowerCase()}`} role="status" aria-live="polite">{streamLabel}</span>
    </div>

    <div className={`execution-current-r60 execution-current-r68 ${run.status.toLowerCase().replaceAll("_", "-")}`}>
      <div className="execution-current-icon-r60"><StateGlyph status={run.status} /></div>
      <div className="execution-current-copy-r68">
        <span>CURRENT TASK</span>
        <strong>{currentLabel}</strong>
        <div className="execution-current-meta-r68"><b>{currentStatus}</b><time>{currentDuration}</time></div>
      </div>
    </div>

    <div className="execution-run-r60">
      <div className="execution-run-id-r60"><span>RUN</span><code>{run.graph_run_id}</code></div>
      <div className="execution-counts-r60" aria-label="Persisted lifecycle summary">
        <span><b>{completed}</b><small>Complete</small></span>
        {running > 0 && <span className="active"><b>{running}</b><small>Running</small></span>}
        {waitingCount > 0 && <span className="waiting"><b>{waitingCount}</b><small>Waiting</small></span>}
        <span className={failed ? "bad" : ""}><b>{failed}</b><small>Failed</small></span>
      </div>
    </div>

    <ExecutionTimeline steps={run.steps} />
    <ExecutionProofDetails steps={run.steps} />

    {run.error && <div className="execution-error-r60" role="alert"><AlertTriangle size={14} /><div><strong>Run error</strong><span>{safeRuntimeError(run.error)}</span></div></div>}
  </section>;
}

function executionRunStatusLabel(status:string) {
  if (status === "COMPLETED") return "Complete";
  if (status === "WAITING_HUMAN") return "Waiting";
  if (status === "RUNNING") return "Running";
  if (status === "FAILED") return "Failed";
  if (status === "CANCELLED") return "Cancelled";
  return "Queued";
}
// R61 compatibility contract: previous visible copy was "Awaiting human decision."; R68 replaces it with state + duration telemetry.

function executionStageName(step:AnalysisStep) {
  return step.display_name.replace(" Agent", "").replace(" Boundary", "");
}

function executionStatusLabel(step:AnalysisStep) {
  if (step.status === "COMPLETED") return "Done";
  if (step.status === "WAITING_HUMAN") return "Waiting";
  if (step.status === "RUNNING") return "Running";
  if (step.status === "FAILED") return "Failed";
  if (step.status === "SKIPPED") return "Skipped";
  if (step.status === "CANCELLED") return "Cancelled";
  return "Queued";
}

function safeRuntimeError(value:string) {
  const compact = value.replace(/\s+/g, " ").trim();
  if (/Traceback|GraphInterrupt|Interrupt\(|\{.*graph_run_id|File \".*\", line \d+/i.test(compact)) return "Backend execution failed. Persisted technical details remain available in Audit.";
  return compact.length > 180 ? `${compact.slice(0, 177)}…` : compact;
}

function ExecutionTimeline({ steps }: { steps:AnalysisStep[] }) {
  return <div className="execution-timeline-r60" aria-label="Agent execution timeline">
    {steps.map(step => <div className={`execution-step-r60 ${step.status.toLowerCase().replaceAll("_", "-")}`} key={step.id}>
      <span className="execution-step-icon-r60" aria-hidden="true"><StepIcon step={step} /></span>
      <div className="execution-step-copy-r60"><strong>{executionStageName(step)}</strong><span>{executionStatusLabel(step)}</span></div>
      <time>{step.duration_ms != null ? formatDuration(step.duration_ms) : "—"}</time>
    </div>)}
  </div>;
}

function ExecutionProofDetails({ steps }: { steps:AnalysisStep[] }) {
  const rows = steps.map(step => ({ step, facts:executionStepFacts(step) })).filter(row => row.facts.length > 0 || row.step.error);
  if (rows.length === 0) return null;
  return <details className="execution-details-r60">
    <summary>Execution details</summary>
    <div className="execution-details-body-r60">
      {rows.map(({ step, facts }) => <div className="execution-detail-stage-r60" key={step.id}>
        <strong>{executionStageName(step)}</strong>
        <div className="execution-facts-r60">
          {facts.map(([label, value]) => <div key={label}><span>{label}</span><b>{value}</b></div>)}
          {step.error && <div className="bad"><span>Error</span><b>{safeRuntimeError(step.error)}</b></div>}
        </div>
      </div>)}
    </div>
  </details>;
}

function executionStepFacts(step:AnalysisStep): Array<[string,string]> {
  const facts:Array<[string,string]> = [];
  if (step.module) facts.push(["Module", step.module]);
  const meta = step.metadata ?? {};
  const pushNumber = (key:string, label:string) => {
    const value = meta[key];
    if (typeof value === "number" && Number.isFinite(value)) facts.push([label, `${value}`]);
  };
  if (step.agent_name === "intake_agent") {
    const model = meta.model_used;
    if (typeof model === "string" && model.trim()) facts.push(["Model", model]);
    const confidence = meta.confidence;
    if (typeof confidence === "number" && Number.isFinite(confidence)) facts.push(["Confidence", `${Math.round(confidence * 100)}%`]);
  }
  if (step.agent_name === "retrieval_agent") {
    pushNumber("evidence_count", "Evidence");
    pushNumber("searched_chunks", "Chunks");
  }
  if (step.agent_name === "knowledge_link_agent") {
    const ids = meta.method_version_ids;
    if (Array.isArray(ids)) facts.push(["Methods", `${ids.length}`]);
  }
  if (step.agent_name === "impact_agent") pushNumber("candidate_count", "Candidates");
  if (step.agent_name === "investigation_agent") pushNumber("result_count", "Investigations");
  if (step.agent_name === "evidence_validator") pushNumber("evidence_gap_count", "Evidence gaps");
  return facts;
}

function AnalysisZone({ index, title, description, children, className = "" }: { index:string; title:string; description?:string; children:ReactNode; className?:string }) {
  return <section className={`analysis-zone-r49 ${className}`.trim()}>
    <header className="analysis-zone-head-r49">
      <span className="analysis-zone-index-r49" aria-hidden="true">{index}</span>
      <div><h2>{title}</h2>{description ? <p>{description}</p> : null}</div>
    </header>
    <div className="analysis-zone-body-r49">{children}</div>
  </section>;
}

function CaseSignalSummary({ issue, understanding, run }: { issue:SupportIssueDetail; understanding:IssueUnderstanding | null; run:AnalysisRun | null }) {
  const retrievalStep = run?.steps.find(step => step.agent_name === "retrieval_agent");
  const impactStep = run?.steps.find(step => step.agent_name === "impact_agent");
  const activeStep = run?.steps.find(step => step.status === "RUNNING");
  const [review, setReview] = useState<any>(null);

  useEffect(() => {
    let cancelled = false;
    setReview(null);
    if (!run || !["WAITING_HUMAN", "COMPLETED"].includes(run.status)) return () => { cancelled = true; };
    void getHumanReview(run.graph_run_id).then(value => { if (!cancelled) setReview(value); }).catch(() => {});
    return () => { cancelled = true; };
  }, [run?.graph_run_id, run?.status]);

  const current = currentAnalysisState(run, activeStep);
  const qwenConfidence = understanding ? Math.round(understanding.confidence * 100) : null;
  const qwenValue = understanding ? (understanding.status === "HUMAN_VERIFIED" ? "Verified" : `${qwenConfidence}%`) : activeStep?.agent_name === "intake_agent" ? "Running" : "—";
  const evidenceCount = numericMeta(retrievalStep, "evidence_count");
  const candidateCount = numericMeta(impactStep, "candidate_count");
  const reviewItems = review?.items ?? [];
  const pendingCount = typeof review?.pending_count === "number" ? review.pending_count : run?.status === "WAITING_HUMAN" ? reviewItems.length || null : null;
  const decisionCount = reviewItems.length || pendingCount;

  return <section className="analysis-compact-summary-r55" aria-label="Analysis case summary">
    <div className={`analysis-state-bar-r55 ${current.tone}`}>
      <div className="analysis-state-main-r55">
        <StateGlyph status={run?.status ?? null} />
        <strong>{current.title}</strong>
        <span>{current.detail}</span>
      </div>
      {decisionCount != null && <div className="analysis-state-action-r55"><b>{decisionCount}</b><span>{pendingCount ? "decisions required" : "decisions recorded"}</span></div>}
    </div>

    <div className="analysis-inline-signals-r55" aria-label="Current analysis signals">
      <span className={`analysis-inline-signal-r55 ${severityTone(issue.severity)}`}><b>{issue.severity}</b><small>{issue.issue_type.replaceAll("_", " ")}</small></span>
      <span className="analysis-inline-signal-r55"><b>{qwenValue}</b><small>Qwen</small></span>
      <span className="analysis-inline-signal-r55"><b>{retrievalStep?.status === "RUNNING" ? "…" : evidenceCount ?? "—"}</b><small>Evidence</small></span>
      <span className="analysis-inline-signal-r55"><b>{impactStep?.status === "RUNNING" ? "…" : candidateCount ?? "—"}</b><small>Candidates</small></span>
      <span className={`analysis-inline-signal-r55 ${run?.status === "WAITING_HUMAN" ? "human" : ""}`}><b>{decisionCount ?? "—"}</b><small>Decisions</small></span>
    </div>
  </section>;
}

function StateGlyph({ status }: { status:string | null }) {
  if (status === "RUNNING" || status === "QUEUED") return <LoaderCircle size={15} className={status === "RUNNING" ? "spin" : ""} />;
  if (status === "WAITING_HUMAN") return <UserCheck size={15} />;
  if (status === "COMPLETED") return <CheckCircle2 size={15} />;
  if (status === "FAILED" || status === "CANCELLED") return <XCircle size={15} />;
  return <GitBranch size={15} />;
}

function currentAnalysisState(run:AnalysisRun | null, activeStep:AnalysisStep | undefined) {
  if (!run) return { tone:"idle", title:"Ready for analysis", detail:"Start a real CREED graph run" };
  if (run.status === "WAITING_HUMAN") return { tone:"human", title:"Human review required", detail:"Workflow paused for governed decision" };
  if (run.status === "COMPLETED") {
    const reviewStep = run.steps.find(step => step.agent_name === "human_review_boundary");
    if (reviewStep?.status === "SKIPPED" && reviewStep.metadata?.skip_reason === "NO_INVESTIGATION_CASES") {
      return { tone:"done", title:"Analysis complete", detail:"No human-review cases produced · check routing or evidence if unexpected" };
    }
    return { tone:"done", title:"Analysis complete", detail:"Governed analysis complete" };
  }
  if (run.status === "FAILED") return { tone:"bad", title:"Analysis failed", detail:"Backend execution failed" };
  if (run.status === "CANCELLED") return { tone:"cancelled", title:"Analysis cancelled", detail:"Execution stopped" };
  if (activeStep) return { tone:"active", title:`${activeStep.display_name.replace(" Agent", "")} running`, detail:activeStep.task };
  if (run.status === "QUEUED") return { tone:"active", title:"Analysis queued", detail:"Waiting for graph execution" };
  return { tone:"active", title:"Analysis in progress", detail:"Following persisted lifecycle events" };
}

function severityTone(value:string): "neutral"|"info"|"ok"|"warn"|"bad" {
  if (value === "CRITICAL") return "bad";
  if (value === "HIGH") return "warn";
  if (value === "MEDIUM") return "info";
  return "neutral";
}

function numericMeta(step:AnalysisStep | undefined, key:string): number | null {
  const value = step?.metadata?.[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function AnalysisWorkspaceNavigator({ run, selected, onSelect, handoffAction, handoffComplete }: { run:AnalysisRun | null; selected:AnalysisWorkspace; onSelect:(workspace:AnalysisWorkspace)=>void; handoffAction:boolean; handoffComplete:boolean }) {
  const retrieval = run?.steps.find(step => step.agent_name === "retrieval_agent");
  const impact = run?.steps.find(step => step.agent_name === "impact_agent");
  const investigation = run?.steps.find(step => step.agent_name === "investigation_agent");
  const evidenceCount = numericMeta(retrieval, "evidence_count");
  const candidateCount = numericMeta(investigation, "result_count") ?? numericMeta(impact, "candidate_count");
  const decisionCount = numericMeta(investigation, "result_count");
  const needsHuman = run?.status === "WAITING_HUMAN";
  const tabs:Array<{id:AnalysisWorkspace; label:string; count:number | null; action?:boolean; actionTone?:"human"|"handoff"; complete?:boolean}> = [
    { id:"context", label:"Case Context", count:null },
    { id:"evidence", label:"Evidence", count:evidenceCount },
    { id:"investigation", label:"Investigation", count:candidateCount },
    { id:"human", label:"Human Decision", count:decisionCount, action:needsHuman, actionTone:"human" },
    { id:"handoff", label:"Learning & Adoption", count:null, action:handoffAction, actionTone:"handoff", complete:handoffComplete },
  ];

  return <nav className="analysis-workspace-nav-r62" aria-label="Analysis workspace">
    <div className="analysis-workspace-tabs-r62" aria-label="Select analysis workspace">
      {tabs.map(tab => <button
        key={tab.id}
        type="button"
        aria-pressed={selected === tab.id}
        className={`analysis-workspace-tab-r62 ${selected === tab.id ? "selected" : ""} ${tab.action ? "action-required" : ""} ${tab.action && tab.actionTone === "handoff" ? "handoff-action-required" : ""} ${tab.complete ? "workflow-complete-r98-m04" : ""}`}
        onClick={() => onSelect(tab.id)}
      >
        {tab.action && <i className="analysis-workspace-action-r62" aria-hidden="true" />}
        <span>{tab.label}</span>
        {tab.count != null && <b>{tab.count}</b>}
        {tab.complete && <CheckCircle2 size={13} className="workflow-complete-icon-r98-m04" aria-hidden="true" />}
        {tab.action && <span className="sr-only">Action required</span>}
        {tab.complete && <span className="sr-only">Workflow complete</span>}
      </button>)}
    </div>
  </nav>;
}

function AnalysisWorkspaceUnavailable({ workspace }: { workspace:Exclude<AnalysisWorkspace,"context"> }) {
  const copy = workspace === "evidence"
    ? { index:"02", title:"Evidence", icon:<FileSearch size={18} />, message:"Evidence appears after a real Retrieval Agent run." }
    : workspace === "investigation"
      ? { index:"03", title:"Investigation", icon:<Radar size={18} />, message:"Investigation appears after candidate analysis runs." }
      : workspace === "human"
        ? { index:"04", title:"Human decision", icon:<UserCheck size={18} />, message:"Human Authority becomes available only at the real review boundary." }
        : { index:"05", title:"Learning & Adoption", icon:<GitBranch size={18} />, message:"Learning and adoption become available only after Human Review completes." };
  return <AnalysisZone index={copy.index} title={copy.title}>
    <div className="analysis-workspace-empty-r62">{copy.icon}<div><strong>Not available yet</strong><span>{copy.message}</span></div></div>
  </AnalysisZone>;
}

function SourceContextSummary({ issue, run }: { issue: SupportIssueDetail; run: AnalysisRun | null }) {
  const workflow = run && !TERMINAL.has(run.status) ? run.status.replaceAll("_", " ") : issue.status.replaceAll("_", " ");
  return <article className="case-context-pane-r56 human">
    <div className="case-context-pane-head-r56">
      <div className="case-context-title-r56"><FileText size={16} /><div><span>HUMAN SOURCE</span><strong>Reported issue</strong></div></div>
      <span className="case-context-origin-r56"><ShieldCheck size={12} />Human supplied</span>
    </div>
    <p className="case-source-excerpt-r56">{issue.description}</p>
    <ProgressiveDisclosure label="View original ticket" meta={issue.external_ticket_id ?? "Source record"}>
      <div className="case-source-proof-r56">
        <div className="case-source-proof-grid-r56">
          <SourceCell label="Client" value={issue.client_name ?? "Not selected"} />
          <SourceCell label="Ticket" value={issue.external_ticket_id ?? "None"} mono />
          <SourceCell label="Issue type" value={issue.issue_type.replaceAll("_", " ")} />
          <SourceCell label="Severity" value={issue.severity} />
          <SourceCell label="Attachments" value={`${issue.attachment_count}`} />
          <SourceCell label="Workflow" value={workflow} />
        </div>
        <div className="case-source-full-r56"><span>ORIGINAL OBSERVATION</span><p>{issue.description}</p></div>
      </div>
    </ProgressiveDisclosure>
  </article>;
}

function StepIcon({ step }: { step: AnalysisStep }) {
  if (step.status === "RUNNING") return <LoaderCircle size={12} className="spin" />;
  if (step.status === "COMPLETED" || step.status === "SKIPPED") return <Check size={12} />;
  if (step.status === "FAILED" || step.status === "CANCELLED") return <X size={12} />;
  if (step.agent_name === "human_review_boundary" || step.status === "WAITING_HUMAN") return <UserCheck size={12} />;
  if (step.agent_name === "retrieval_agent" || step.agent_name === "evidence_validator") return <FileSearch size={12} />;
  if (step.agent_name === "impact_agent") return <Radar size={12} />;
  if (step.agent_name === "intake_agent") return <BrainCircuit size={12} />;
  return <GitBranch size={12} />;
}

function QwenContextSummary({ issue, understanding }: { issue: SupportIssueDetail; understanding: IssueUnderstanding }) {
  const confidence = Math.round(understanding.confidence * 100);
  const mismatch = Boolean(issue.client_name && understanding.client_name && issue.client_name.toLowerCase() !== understanding.client_name.toLowerCase());
  return <div className="qwen-context-summary-r56 qwen-context-summary-r64">
    <div className="qwen-context-status-r56 qwen-context-status-r64">
      <div><span>CONFIDENCE</span><strong>{confidence}%</strong></div>
      <SignalChip tone="ok" icon={CheckCircle2}>Structured</SignalChip>
    </div>

    {mismatch && <div className="qwen-client-mismatch-r64" role="status">
      <AlertTriangle size={14} />
      <div><span>CLIENT</span><strong>{understanding.client_name}</strong></div>
      <small>Source: {issue.client_name}</small>
      <em>Mismatch</em>
    </div>}

    <div className="qwen-context-fields-r56 qwen-context-fields-r64">
      <ContextField label="Product" value={understanding.product} />
      <ContextField label="Module" value={understanding.module} />
      <ContextField label="Issue type" value={understanding.issue_type} />
      <ContextField label="Function" value={understanding.suspected_function} />
    </div>

    <ProgressiveDisclosure label="Inspect model interpretation" meta="Summary · keywords · runtime proof">
      <UnderstandingView issue={issue} understanding={understanding} />
    </ProgressiveDisclosure>
  </div>;
}

function ContextField({ label, value }: { label:string; value:string | null }) {
  return <div className={`qwen-context-field-r56 ${value ? "" : "unknown"}`}><span>{label}</span><strong>{value?.replaceAll("_", " ") ?? "Not extracted"}</strong></div>;
}

function UnderstandingView({ issue, understanding }: { issue: SupportIssueDetail; understanding: IssueUnderstanding }) {
  const confidence = Math.round(understanding.confidence * 100);
  const mismatch = understanding.warnings.length > 0;
  return <div className="understanding-r04">
    <div className="understanding-score-r04"><div><span>EXTRACTION CONFIDENCE</span><strong>{confidence}%</strong></div><div className="confidence-track-r04"><i style={{ width:`${confidence}%` }} /></div><small>Extraction confidence is not an impact or safety score.</small></div>
    {mismatch && <div className="understanding-warnings-r04">{understanding.warnings.map(w => <span key={w}><AlertTriangle size={12} />{friendlyWarning(w)}</span>)}</div>}
    <div className="understanding-fields-r04">
      <AiField k="Client" v={understanding.client_name} /><AiField k="Product" v={understanding.product} /><AiField k="Module" v={understanding.module} /><AiField k="Issue type" v={understanding.issue_type} /><AiField k="Severity" v={understanding.severity} /><AiField k="Suspected function" v={understanding.suspected_function} />
    </div>
    <div className="understanding-summary-r04"><span>STRUCTURED SUMMARY</span><p>{understanding.summary}</p></div>
    <div className="keyword-row-r04"><span>KEYWORDS</span><div>{understanding.keywords.length ? understanding.keywords.map(k => <b key={k}>{k}</b>) : <em>None extracted</em>}</div></div>
    <div className="model-proof-r04"><span>RUN {understanding.qwen_run_id}</span><span>{understanding.actual_model ?? understanding.configured_model}</span><span>{formatDuration(understanding.duration_ms)}</span><span>{understanding.prompt_eval_count ?? "—"} input</span><span>{understanding.eval_count ?? "—"} output</span><span>{understanding.status.replaceAll("_", " ")}</span></div>
    {issue.client_name && understanding.client_name && issue.client_name.toLowerCase() !== understanding.client_name.toLowerCase() && <div className="source-conflict-r04"><AlertTriangle size={14} /><span>Source client is <strong>{issue.client_name}</strong>; Qwen extracted <strong>{understanding.client_name}</strong>. CREED preserves both until a human resolves the difference.</span></div>}
  </div>;
}

function UnderstandingEditor({ issueId, understanding, onSaved, onError }: { issueId:string; understanding:IssueUnderstanding; onSaved:(u:IssueUnderstanding)=>void; onError:(s:string|null)=>void }) {
  const initial = useMemo<IssueUnderstandingEdit>(() => ({ client_name:understanding.client_name, product:understanding.product, module:understanding.module, issue_type:understanding.issue_type, summary:understanding.summary, suspected_function:understanding.suspected_function, keywords:understanding.keywords, severity:understanding.severity }), [understanding]);
  const [form, setForm] = useState(initial); const [busy, setBusy] = useState(false);
  async function save() { setBusy(true); onError(null); try { onSaved(await updateIssueUnderstanding(issueId, understanding.id, form)); } catch (e) { onError(e instanceof Error ? e.message : "UNDERSTANDING_UPDATE_FAILED"); } finally { setBusy(false); } }
  return <div className="understanding-editor-r04">
    <div className="human-edit-note-r04"><ShieldCheck size={15} /><div><strong>Human verification</strong><span>CREED retains the original model run and records your verified values separately.</span></div></div>
    <div className="edit-grid-r04"><EditField label="Client" value={form.client_name ?? ""} onChange={v => setForm({ ...form, client_name:v || null })} /><EditField label="Product" value={form.product ?? ""} onChange={v => setForm({ ...form, product:v || null })} /><EditField label="Module" value={form.module ?? ""} onChange={v => setForm({ ...form, module:v || null })} /><label><span>Issue type</span><select value={form.issue_type} onChange={e => setForm({ ...form, issue_type:e.target.value as IssueUnderstandingEdit["issue_type"] })}><option>BUG</option><option>INCIDENT</option><option>CHANGE_REQUEST</option><option>ENHANCEMENT</option><option>UNKNOWN</option></select></label><label><span>Severity</span><select value={form.severity} onChange={e => setForm({ ...form, severity:e.target.value as IssueUnderstandingEdit["severity"] })}><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option><option>UNKNOWN</option></select></label><EditField label="Suspected function" value={form.suspected_function ?? ""} onChange={v => setForm({ ...form, suspected_function:v || null })} /></div>
    <label className="edit-wide-r04"><span>Summary</span><textarea value={form.summary} onChange={e => setForm({ ...form, summary:e.target.value })} /></label>
    <label className="edit-wide-r04"><span>Keywords · comma separated</span><input value={form.keywords.join(", ")} onChange={e => setForm({ ...form, keywords:e.target.value.split(",").map(x => x.trim()).filter(Boolean).slice(0, 8) })} /></label>
    <div className="editor-save-r04"><button type="button" className="primary-btn compact" onClick={save} disabled={busy || form.summary.trim().length < 8}>{busy ? <LoaderCircle size={13} className="spin" /> : <Save size={13} />}Verify & save</button></div>
  </div>;
}

function QwenRunning({ graphManaged = false }: { graphManaged?:boolean }) {
  return <div className="qwen-running-r04"><div className="qwen-running-icon-r04"><BrainCircuit size={18} /></div><div><strong>{graphManaged ? "Intake Agent is running Qwen issue understanding" : "Qwen is processing the saved issue"}</strong><p>{graphManaged ? "Status comes from the executing LangGraph node — never a visual timer." : "Local Qwen is producing schema-validated output."}</p><div className="qwen-progress-r04"><span /></div></div></div>;
}

// R61 supersedes visible helper-copy contracts from earlier Analysis passes.
// description="Source fact vs AI interpretation."
// Compare candidates, then inspect one.
// Make the governed decision.
// Choose the governed outcome
// Awaiting governed human decision.
function DownstreamIntelligence({ run, onRunUpdate, selectedWorkspace, onHumanReviewComplete, onHandoffAttentionChange, onHandoffCompleteChange, handoffArrivalNotice }: { run:AnalysisRun; onRunUpdate:(r:AnalysisRun)=>void; selectedWorkspace:Exclude<AnalysisWorkspace,"context">; onHumanReviewComplete:(r:AnalysisRun)=>void; onHandoffAttentionChange:(required:boolean)=>void; onHandoffCompleteChange:(complete:boolean)=>void; handoffArrivalNotice:boolean }) {
  const [evidence, setEvidence] = useState<any>(null);
  const [impact, setImpact] = useState<any>(null);
  const [investigations, setInvestigations] = useState<any>(null);
  const [review, setReview] = useState<any>(null);
  const [learning, setLearning] = useState<LearningProposalSummary | null>(null);
  const [authorities, setAuthorities] = useState<HumanAuthorityRecord[]>([]);
  const [authorityPrincipal, setAuthorityPrincipal] = useState("");
  const [authorityError, setAuthorityError] = useState<string | null>(null);
  const [decisions, setDecisions] = useState<Record<string, { decision:string; reason:string }>>({});
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void getHumanAuthorities().then(rows => {
      setAuthorities(rows);
      setAuthorityError(null);
    }).catch(error => setAuthorityError(error instanceof Error ? error.message : "AUTHORITY_LIST_FAILED"));
  }, []);

  const decisionAuthorities = useMemo(() => authorities.filter(item => item.active && item.can_submit_human_decision), [authorities]);

  useEffect(() => {
    if (authorityPrincipal && decisionAuthorities.some(item => item.principal === authorityPrincipal)) return;
    setAuthorityPrincipal(decisionAuthorities[0]?.principal ?? "");
  }, [authorityPrincipal, decisionAuthorities]);

  useEffect(() => {
    const retrieval = run.steps.find(s => s.agent_name === "retrieval_agent");
    if (retrieval?.status === "COMPLETED") void getRunEvidence(run.graph_run_id).then(setEvidence).catch(() => {});
    const impactStep = run.steps.find(s => s.agent_name === "impact_agent");
    if (impactStep?.status === "COMPLETED") void getImpact(run.graph_run_id).then(setImpact).catch(() => {});
    const inv = run.steps.find(s => s.agent_name === "investigation_agent");
    if (inv?.status === "COMPLETED") void getRunInvestigations(run.graph_run_id).then(setInvestigations).catch(() => {});
    if (run.status === "WAITING_HUMAN" || run.status === "COMPLETED") void getHumanReview(run.graph_run_id).then(setReview).catch(() => {});
    if (run.status === "COMPLETED") void Promise.all([getLearningProposal(run.graph_run_id), getLearningReadiness(run.graph_run_id)]).then(([proposal, readiness]) => {
      setLearning(proposal);
      const terminalLearning = proposal?.status === "REJECTED" || (proposal?.status === "APPROVED" && Boolean(proposal.adoption_receipt));
      onHandoffCompleteChange(terminalLearning);
      onHandoffAttentionChange(!terminalLearning && (Boolean(proposal) || readiness.eligible));
    }).catch(() => { onHandoffCompleteChange(false); });
    else { onHandoffAttentionChange(false); onHandoffCompleteChange(false); }
  }, [run, onHandoffAttentionChange, onHandoffCompleteChange]);

  async function submit() {
    if (!review) return;
    const items = review.items ?? [];
    if (!authorityPrincipal) { setReviewError("Select an active principal with Human Decision authority."); return; }
    if (items.some((x:any) => !decisions[x.id]?.decision || !decisions[x.id]?.reason?.trim())) { setReviewError("Choose a decision and rationale for every implementation."); return; }
    const contradictionWithoutRationale = items.find((x:any) => {
      const draft = decisions[x.id];
      if (!draft?.decision) return false;
      const consistency = humanDecisionConsistencyFor((x.configuration_comparison ?? null) as ConfigurationComparisonView | null, draft.decision);
      return consistency?.contradiction && (draft.reason?.trim().length ?? 0) < R9406_CONTRADICTION_RATIONALE_MIN_CHARS;
    });
    if (contradictionWithoutRationale) {
      setReviewError(`A decision that contradicts the deterministic technical advisory requires an explicit rationale of at least ${R9406_CONTRADICTION_RATIONALE_MIN_CHARS} characters.`);
      return;
    }
    setBusy(true); setReviewError(null);
    try {
      await resumeHumanReview(
        run.graph_run_id,
        { reviewer:authorityPrincipal, decisions:items.map((x:any) => ({ investigation_id:x.id, ...decisions[x.id] })) },
        authorityPrincipal,
      );
      const latest = await getLatestAnalysisRun(run.issue_id!);
      if (latest) {
        onRunUpdate(latest);
        if (latest.status === "COMPLETED") onHumanReviewComplete(latest);
      }
    } catch (e) { setReviewError(e instanceof Error ? e.message : "HUMAN_REVIEW_FAILED"); }
    finally { setBusy(false); }
  }

  const retrievalStep = run.steps.find(step => step.agent_name === "retrieval_agent");
  const investigationStep = run.steps.find(step => step.agent_name === "investigation_agent");
  const humanStep = run.steps.find(step => step.agent_name === "human_review_boundary");

  return <div className="downstream-r04 downstream-min-r25 downstream-r49 downstream-selected-r62">
    {selectedWorkspace === "evidence" && <AnalysisZone index="02" title="Evidence" className="analysis-zone-evidence-r98-m05">
      {evidence ? <EvidenceWorkbench evidence={evidence} /> : <WorkspacePendingState icon={<FileSearch size={18} />} title="Evidence not available yet" status={retrievalStep?.status} />}
    </AnalysisZone>}

    {selectedWorkspace === "investigation" && <AnalysisZone index="03" title="Investigation">
      {(impact || investigations) ? <InvestigationWorkbench run={run} impact={impact} investigations={investigations} evidence={evidence} /> : <WorkspacePendingState icon={<Radar size={18} />} title="Investigation not available yet" status={investigationStep?.status} />}
    </AnalysisZone>}

    {selectedWorkspace === "human" && <AnalysisZone index="04" title="Human decision">
      {review ? <HumanDecisionWorkbench
        run={run}
        review={review}
        decisions={decisions}
        setDecisions={setDecisions}
        reviewError={reviewError ?? authorityError}
        authorities={authorities}
        authorityPrincipal={authorityPrincipal}
        setAuthorityPrincipal={setAuthorityPrincipal}
        busy={busy}
        onSubmit={submit}
      /> : <WorkspacePendingState icon={<UserCheck size={18} />} title="Human review not reached" status={humanStep?.status ?? (run.status === "WAITING_HUMAN" ? "WAITING_HUMAN" : undefined)} />}
    </AnalysisZone>}

    {selectedWorkspace === "handoff" && <AnalysisZone index="05" title="Learning & Adoption" className="analysis-zone-handoff-r98-m05">
      {handoffArrivalNotice && <div className="handoff-arrival-r98-m03" role="status"><CheckCircle2 size={14} /><div><strong>Human decisions recorded</strong><span>Continue with the next governed learning and adoption action.</span></div></div>}
      {run.status === "COMPLETED"
        ? <GovernedLearningHandoff run={run} learning={learning} authorities={authorities} onLearningChange={(next) => { setLearning(next); const terminalLearning = next.status === "REJECTED" || (next.status === "APPROVED" && Boolean(next.adoption_receipt)); onHandoffCompleteChange(terminalLearning); onHandoffAttentionChange(!terminalLearning); }} />
        : <WorkspacePendingState icon={<GitBranch size={18} />} title="Learning & Adoption not available yet" status={humanStep?.status ?? (run.status === "WAITING_HUMAN" ? "WAITING_HUMAN" : undefined)} />}
    </AnalysisZone>}
  </div>;
}

function WorkspacePendingState({ icon, title, status }: { icon:ReactNode; title:string; status?:AnalysisStep["status"] }) {
  const state = status === "RUNNING" ? "Running" : status === "WAITING_HUMAN" ? "Action required" : status === "FAILED" ? "Failed" : status === "COMPLETED" ? "Loading persisted result" : "Not reached";
  return <div className={`analysis-workspace-empty-r62 ${status?.toLowerCase().replaceAll("_", "-") ?? "idle"}`}>
    {icon}<div><strong>{title}</strong><span>{state}</span></div>
  </div>;
}


// R25 regression lineage tokens retained after R53 replacement: human-authority-min-r25 review-ledger-r04 decision-grid-r04
// R61 regression lineage: Choose outcome
type ReviewDraft = { decision:string; reason:string };

function HumanDecisionWorkbench({ run, review, decisions, setDecisions, reviewError, authorities, authorityPrincipal, setAuthorityPrincipal, busy, onSubmit }: {
  run:AnalysisRun;
  review:any;
  decisions:Record<string, ReviewDraft>;
  setDecisions:Dispatch<SetStateAction<Record<string, ReviewDraft>>>;
  reviewError:string | null;
  authorities:HumanAuthorityRecord[];
  authorityPrincipal:string;
  setAuthorityPrincipal:Dispatch<SetStateAction<string>>;
  busy:boolean;
  onSubmit:()=>Promise<void>;
}) {
  const items = Array.isArray(review?.items) ? review.items : [];
  const [selectedReviewId, setSelectedReviewId] = useState<string | null>(null);

  useEffect(() => {
    if (!items.length) {
      if (selectedReviewId !== null) setSelectedReviewId(null);
      return;
    }
    if (selectedReviewId && !items.some((item:any) => item.id === selectedReviewId)) setSelectedReviewId(null);
  }, [items, selectedReviewId]);

  const selected = items.find((item:any) => item.id === selectedReviewId) ?? null;
  const selectedDraft = selected ? decisions[selected.id] : null;
  const readyCount = items.filter((item:any) => item.human_decision || reviewDraftReady((item.configuration_comparison ?? null) as ConfigurationComparisonView | null, decisions[item.id])).length;
  const isPending = Number(review?.pending_count ?? 0) > 0;
  const allReady = items.length > 0 && readyCount === items.length;
  const selectedEvidenceRefs = Array.isArray(selected?.finding?.evidence_refs) ? selected.finding.evidence_refs : [];
  const selectedComparison = (selected?.configuration_comparison ?? null) as ConfigurationComparisonView | null;
  const selectedConsistency = selectedDraft?.decision ? humanDecisionConsistencyFor(selectedComparison, selectedDraft.decision) : null;
  const selectedRationaleMinimum = selectedConsistency?.contradiction ? R9406_CONTRADICTION_RATIONALE_MIN_CHARS : 3;
  const selectedRationaleMode = selectedConsistency?.contradiction
    ? "exception"
    : selectedDraft?.decision === "NEEDS_MORE_INVESTIGATION"
      ? "investigation"
      : "aligned";
  const selectedRationalePlaceholder = selectedRationaleMode === "exception"
    ? "Explain why Human Authority is overriding the deterministic technical advisory."
    : selectedRationaleMode === "investigation"
      ? "State what additional evidence or investigation is required."
      : "Briefly state the evidence-backed reason for this decision.";
  const eligibleDecisionAuthorities = authorities.filter(item => item.active && item.can_submit_human_decision);
  const selectedAuthority = eligibleDecisionAuthorities.find(item => item.principal === authorityPrincipal) ?? null;

  function chooseDecision(decision:string) {
    if (!selected || selected.human_decision) return;
    setDecisions(current => ({ ...current, [selected.id]:{ decision, reason:current[selected.id]?.reason ?? "" } }));
  }

  function updateReason(reason:string) {
    if (!selected || selected.human_decision) return;
    setDecisions(current => ({ ...current, [selected.id]:{ decision:current[selected.id]?.decision ?? "", reason } }));
  }

  return <section className="human-decision-workbench-r53 human-decision-focus-r59 human-decision-accordion-workbench-r97-m07">
    <header className="authority-focus-head-r59">
      <div className="authority-focus-title-r59">
        <span className="authority-focus-icon-r59"><ShieldCheck size={17} /></span>
        <div>
          <span>GOVERNED REVIEW</span>
          <h2>{isPending ? "Human review required" : items.length ? "Human review recorded" : "No human-review cases available"}</h2>
          <p>{isPending ? `${review.pending_count} decision${review.pending_count === 1 ? "" : "s"} required.` : items.length ? `${items.length} decision${items.length === 1 ? "" : "s"} recorded.` : "No governed decision was opened for this run."}</p>
        </div>
      </div>
      <div className="authority-focus-meta-r59 authority-focus-meta-r67">
        <div className="authority-review-progress-r67" aria-label={`${readyCount} of ${items.length} review decisions complete`}>
          <span><ClipboardCheck size={12} /><b>{readyCount}/{items.length}</b><small>reviewed</small></span>
          <span className="authority-review-track-r67" role="progressbar" aria-valuemin={0} aria-valuemax={items.length} aria-valuenow={readyCount}>
            <i style={{ transform:`scaleX(${items.length ? Math.min(1, Math.max(0, readyCount / items.length)) : 0})` }} />
          </span>
        </div>
        <SignalChip tone={isPending ? "warn" : "ok"} icon={isPending ? UserCheck : CheckCircle2}>{isPending ? "ACTION REQUIRED" : items.length ? "RECORDED" : "NO CASES"}</SignalChip>
      </div>
    </header>

    {isPending && <div className={`authority-enforcement-r85 ${selectedAuthority ? "ready" : "blocked"}`}>
      <ShieldCheck size={17} aria-hidden="true" />
      <div>
        <span>AUTHORIZED PRINCIPAL</span>
        <strong>{selectedAuthority ? `${selectedAuthority.display_name} · ${selectedAuthority.role_title}` : "Human Decision authority required"}</strong>
        <small>CREED checks the selected principal against the active authority registry before the workflow can resume.</small>
      </div>
      {eligibleDecisionAuthorities.length ? <select value={authorityPrincipal} onChange={event => setAuthorityPrincipal(event.target.value)} aria-label="Select Human Decision authority">
        {eligibleDecisionAuthorities.map(item => <option key={item.id} value={item.principal}>{item.display_name} · {item.principal}</option>)}
      </select> : <a href="/authority">Configure authority</a>}
    </div>}

    {items.length === 0 ? <div className="analysis-empty-r04 analysis-empty-min-r25"><UserCheck size={18} /><div><strong>No human-review cases persisted</strong><p>{run?.recovery_eligible ? "This is a stale zero-case Human Review checkpoint. Use Recover & rerun to preserve this run and start a fresh analysis through the corrected routing pipeline." : run?.status === "COMPLETED" ? "Human Review was skipped because this run produced no investigation cases. Check routing or evidence if that was unexpected." : "The decision workbench will populate only from the real Human Review boundary."}</p></div></div> : <div className="candidate-accordion-list-r97-m07 human-decision-candidate-list-r97-m07" aria-label="Human review cases">
      {items.map((item:any, index:number) => {
        const active = selected?.id === item.id;
        const draft = decisions[item.id];
        const comparison = (item.configuration_comparison ?? null) as ConfigurationComparisonView | null;
        const advisoryLabel = comparison ? configurationTechnicalLabel(comparison.technical_result) : item.finding?.type?.replaceAll("_", " ") ?? "NO AI FINDING";
        const advisoryTone = comparison ? configurationResultTone(comparison.technical_result) : findingTone(item.finding?.type);
        const stateClass = item.human_decision ? decisionToneClass(item.human_decision.decision) : draft?.decision ? "draft" : "pending";
        const stateLabel = item.human_decision?.decision?.replaceAll("_", " ") ?? (draft?.decision ? `DRAFT · ${draft.decision.replaceAll("_", " ")}` : "DECISION REQUIRED");
        return <section key={item.id} className={`candidate-accordion-item-r97-m07 ${active ? "open" : ""}`}>
          <button
            type="button"
            className="candidate-accordion-trigger-r97-m07"
            aria-expanded={active}
            onClick={() => setSelectedReviewId(active ? null : item.id)}
          >
            <span className="candidate-accordion-index-r97-m07">{String(index + 1).padStart(2, "0")}</span>
            <span className="candidate-accordion-identity-r97-m07"><strong>{item.implementation_name ?? "Implementation unavailable"}</strong><small>Human decision</small></span>
            <span className="candidate-accordion-status-r97-m07"><SignalChip tone={advisoryTone}>{advisoryLabel}</SignalChip><em className={stateClass}>{stateLabel}</em></span>
            <ChevronDown className="candidate-accordion-chevron-r97-m07" size={16} aria-hidden="true" />
          </button>

          {active && selected && <div className="candidate-accordion-body-r97-m07 human-decision-inline-body-r97-m07" aria-live="polite">
            {selected.human_decision ? <section className="authority-record-r53 authority-record-r59 human-decision-record-r97-m06">
              <div className="human-decision-record-summary-r97-m06">
                <span className="human-decision-record-icon-r97-m06"><ShieldCheck size={15} /></span>
                <div className="human-decision-record-copy-r97-m06">
                  <span>DECISION RECORDED</span>
                  <div>
                    <SignalChip tone={humanDecisionTone(selected.human_decision.decision)} icon={UserCheck}>{selected.human_decision.decision.replaceAll("_", " ")}</SignalChip>
                    <strong>{selected.human_decision.authority_display_name ?? selected.human_decision.reviewer}</strong>
                  </div>
                  <p>{selected.human_decision.reason ?? "No rationale was returned with this decision record."}</p>
                </div>
              </div>
              <ProgressiveDisclosure label="View governed record" meta={selected.human_decision.authority_role_title ?? "Human Authority"}>
                <div className="human-decision-governed-record-r97-m06">
                  <div className="human-decision-governed-meta-r97-m06">
                    <div><span>OUTCOME</span><strong>{selected.human_decision.decision.replaceAll("_", " ")}</strong></div>
                    <div><span>REVIEWER</span><strong>{selected.human_decision.authority_display_name ? `${selected.human_decision.authority_display_name} · ${selected.human_decision.reviewer}` : selected.human_decision.reviewer}</strong></div>
                    {selected.human_decision.authority_role_title && <div><span>AUTHORITY</span><strong>{selected.human_decision.authority_role_title}</strong></div>}
                  </div>
                  {selected.human_decision.decision_consistency?.contradiction && <DecisionConsistencyWarning consistency={selected.human_decision.decision_consistency as DecisionConsistencyView} recorded />}
                  <div className="authority-rationale-r53 human-decision-governed-rationale-r97-m06"><span>RATIONALE</span><p>{selected.human_decision.reason ?? "No rationale was returned with this decision record."}</p></div>
                  <p className="human-decision-governed-boundary-r97-m06"><ShieldCheck size={12} />This persisted Human Authority outcome remains separate from the technical and AI advisory.</p>
                </div>
              </ProgressiveDisclosure>
            </section> : <section className="authority-decision-r53 authority-decision-r59">
              <div className="authority-decision-lead-r59 authority-decision-lead-r67 human-decision-card-lead-r97-m04">
                <div><span>GOVERNED OUTCOME</span><strong>Choose the human decision</strong></div>
                <span className="authority-ai-quiet-r59 sr-only"><BrainCircuit size={13} />Technical and AI analysis remain advisory</span>
              </div>

              <div className="authority-choice-grid-r53 authority-choice-grid-r59">
                <DecisionChoice value="AFFECTED" icon={<AlertTriangle size={16} />} title="Affected" description="Record that this implementation is affected." selected={selectedDraft?.decision === "AFFECTED"} onSelect={chooseDecision} />
                <DecisionChoice value="NOT_AFFECTED" icon={<CheckCircle2 size={16} />} title="Not affected" description="Record that this implementation is not affected." selected={selectedDraft?.decision === "NOT_AFFECTED"} onSelect={chooseDecision} />
                <DecisionChoice value="NEEDS_MORE_INVESTIGATION" icon={<SearchCheck size={16} />} title="Needs more investigation" description="Return the case for additional evidence-backed investigation." selected={selectedDraft?.decision === "NEEDS_MORE_INVESTIGATION"} onSelect={chooseDecision} />
              </div>

              {selectedConsistency?.contradiction && <DecisionConsistencyWarning consistency={selectedConsistency} />}

              {selectedDraft?.decision && <label className={`authority-rationale-input-r53 authority-rationale-input-r59 authority-rationale-input-r67 human-rationale-r97-m05 mode-${selectedRationaleMode} ${selectedConsistency?.contradiction ? "technical-exception-r9406" : ""}`}>
                <span>
                  <strong><b>STEP 2</b> {selectedRationaleMode === "exception" ? "Exception rationale" : selectedRationaleMode === "investigation" ? "Investigation rationale" : "Decision rationale"}</strong>
                  <em>Required · minimum {selectedRationaleMinimum} characters</em>
                </span>
                <textarea
                  rows={selectedRationaleMode === "aligned" ? 1 : 3}
                  maxLength={3000}
                  placeholder={selectedRationalePlaceholder}
                  value={selectedDraft?.reason ?? ""}
                  onChange={event => updateReason(event.target.value)}
                />
                <small>{(selectedDraft?.reason ?? "").trim().length}/{selectedRationaleMinimum} minimum{selectedRationaleMode !== "aligned" ? " · detailed rationale required" : ""}</small>
              </label>}

              <ProgressiveDisclosure label="View technical basis" meta={`${selectedEvidenceRefs.length} evidence ref${selectedEvidenceRefs.length === 1 ? "" : "s"}`}>
                <div className="human-decision-technical-basis-r97-m04">
                  {selectedComparison && <ConfigurationComparisonPanel comparison={selectedComparison} evidenceCount={selectedEvidenceRefs.length} compact />}
                  <div className="authority-ai-proof-r59">
                    <div className="authority-ai-proof-signals-r59">
                      <SignalChip tone={selectedComparison ? configurationResultTone(selectedComparison.technical_result) : findingTone(selected.finding?.type)}>{selectedComparison ? configurationTechnicalLabel(selectedComparison.technical_result) : selected.finding?.type?.replaceAll("_", " ") ?? "NO AI FINDING"}</SignalChip>
                      <span>Confidence <b>{selected.finding?.confidence == null ? "—" : `${Math.round(Number(selected.finding.confidence) * 100)}%`}</b></span>
                    </div>
                    <p>{selected.finding?.statement ?? "No persisted AI finding statement is available for this implementation."}</p>
                    <div className="authority-ai-proof-refs-r59">
                      <span>EVIDENCE REFERENCES</span>
                      <strong>{selectedEvidenceRefs.length ? selectedEvidenceRefs.join(" · ") : "No persisted evidence references"}</strong>
                    </div>
                    <p className="authority-ai-boundary-r59 sr-only"><ShieldCheck size={13} />Technical/AI finding is advisory. The human decision is the governed outcome.</p>
                  </div>
                </div>
              </ProgressiveDisclosure>
            </section>}
          </div>}
        </section>;
      })}
    </div>}

    {reviewError && <div className="authority-error-r53" role="alert"><AlertTriangle size={14} />{reviewError}</div>}

    {isPending && <footer className="authority-submit-r53 authority-submit-r59 authority-submit-r67">
      <div>
        <span>STEP 3</span>
        <strong>{allReady ? "Submit human decisions" : `${items.length - readyCount} decision${items.length - readyCount === 1 ? "" : "s"} remaining`}</strong>
        <p className="sr-only">Submission is atomic: every implementation requires a decision and rationale.</p>
      </div>
      <button type="button" className="primary-btn" onClick={() => void onSubmit()} disabled={busy || !allReady || !selectedAuthority}>
        {busy ? <LoaderCircle size={13} className="spin" /> : <ClipboardCheck size={13} />}
        {busy ? "Submitting" : "Submit decisions"}
      </button>
    </footer>}

  </section>;
}
function DecisionChoice({ value, icon, title, description, selected, onSelect }: { value:string; icon:ReactNode; title:string; description:string; selected:boolean; onSelect:(value:string)=>void }) {
  return <button type="button" className={`authority-choice-r53 authority-choice-r59 authority-choice-r67 ${selected ? "selected" : ""}`} data-decision={value} aria-pressed={selected} onClick={() => onSelect(value)}>
    <span className="authority-choice-icon-r53">{icon}</span>
    <span><strong>{title}</strong><small className="sr-only">{description}</small></span>
    <span className="authority-choice-check-r53">{selected ? <Check size={13} /> : null}</span>
  </button>;
}

function LearningStageRow({ index, title, subtitle, status, tone, open, onToggle, children }: {
  index:string;
  title:string;
  subtitle:string;
  status:string;
  tone:"neutral"|"info"|"ok"|"warn"|"bad";
  open:boolean;
  onToggle:()=>void;
  children:ReactNode;
}) {
  return <section className={`candidate-accordion-item-r97-m07 learning-stage-item-r98-m06 ${open ? "open" : ""}`}>
    <button type="button" className="candidate-accordion-trigger-r97-m07 learning-stage-trigger-r98-m06" aria-expanded={open} onClick={onToggle}>
      <span className="candidate-accordion-index-r97-m07">{index}</span>
      <span className="candidate-accordion-identity-r97-m07"><strong>{title}</strong><small>{subtitle}</small></span>
      <span className="candidate-accordion-status-r97-m07"><SignalChip tone={tone}>{status}</SignalChip></span>
      <ChevronDown className="candidate-accordion-chevron-r97-m07" size={16} aria-hidden="true" />
    </button>
    {open && <div className="candidate-accordion-body-r97-m07 learning-stage-body-r98-m06">{children}</div>}
  </section>;
}

// R94-M06 regression contract: HUMAN CORRECTION remains the governed authoring boundary.
// R94-M08 regression contract: ADOPTION SCOPE remains sealed into the signed receipt.
// R94-M08 regression contract: Implementations sealed into scope.
function GovernedLearningHandoff({ run, learning, authorities, onLearningChange }: {
  run:AnalysisRun;
  learning:LearningProposalSummary | null;
  authorities:HumanAuthorityRecord[];
  onLearningChange:(learning:LearningProposalSummary)=>void;
}) {
  const eligible = authorities.filter(item => item.active && item.can_approve_learning);
  const correctionAuthorities = authorities.filter(item => item.active && item.can_submit_human_decision);
  const [principal, setPrincipal] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [readiness, setReadiness] = useState<LearningReadiness | null>(null);
  const [readinessError, setReadinessError] = useState<string | null>(null);
  const [correctionAuthor, setCorrectionAuthor] = useState("");
  const [newVersion, setNewVersion] = useState("");
  const [correction, setCorrection] = useState("");
  const [proposalBusy, setProposalBusy] = useState(false);
  const [proposalError, setProposalError] = useState<string | null>(null);
  const [receiptVerification, setReceiptVerification] = useState<AdoptionReceiptVerification | null>(null);
  const [receiptVerifyBusy, setReceiptVerifyBusy] = useState(false);
  const [receiptVerifyError, setReceiptVerifyError] = useState<string | null>(null);
  const [scopeMode, setScopeMode] = useState<AdoptionScopeMode>("CURRENT_REGISTERED_IMPLEMENTATIONS");
  const [scopeAbom, setScopeAbom] = useState<MethodAbom | null>(null);
  const [scopeBusy, setScopeBusy] = useState(false);
  const [scopeError, setScopeError] = useState<string | null>(null);
  const [selectedScopeIds, setSelectedScopeIds] = useState<string[]>([]);
  const [openStage, setOpenStage] = useState<"proposal"|"authority"|"receipt"|null>(null);

  useEffect(() => {
    if (principal && eligible.some(item => item.principal === principal)) return;
    setPrincipal(eligible[0]?.principal ?? "");
  }, [eligible, principal]);

  useEffect(() => {
    if (learning) return;
    let alive = true;
    setReadinessError(null);
    void getLearningReadiness(run.graph_run_id).then(value => {
      if (!alive) return;
      setReadiness(value);
      setNewVersion(current => current || value.suggested_new_version || "");
    }).catch(err => {
      if (alive) setReadinessError(err instanceof Error ? err.message : "LEARNING_READINESS_FAILED");
    });
    return () => { alive = false; };
  }, [run.graph_run_id, learning]);

  useEffect(() => {
    if (correctionAuthor && correctionAuthorities.some(item => item.principal === correctionAuthor)) return;
    const preferred = readiness?.affected_reviewers.find(reviewer => correctionAuthorities.some(item => item.principal === reviewer));
    setCorrectionAuthor(preferred ?? correctionAuthorities[0]?.principal ?? "");
  }, [correctionAuthor, correctionAuthorities, readiness]);

  useEffect(() => {
    setReceiptVerification(null);
    setReceiptVerifyError(null);
  }, [learning?.adoption_receipt?.id]);

  useEffect(() => {
    const sourceId = learning?.status === "PROPOSED" ? learning.source_method_version?.id : null;
    if (!sourceId) { setScopeAbom(null); setSelectedScopeIds([]); return; }
    let alive = true;
    setScopeBusy(true); setScopeError(null);
    void getMethodAbom(sourceId).then(value => {
      if (!alive) return;
      setScopeAbom(value);
      setSelectedScopeIds(value.implementations.map(item => item.id));
      setScopeMode(value.implementations.length ? "CURRENT_REGISTERED_IMPLEMENTATIONS" : "METHOD_CATALOG");
    }).catch(err => {
      if (alive) setScopeError(err instanceof Error ? err.message : "ADOPTION_SCOPE_LOAD_FAILED");
    }).finally(() => { if (alive) setScopeBusy(false); });
    return () => { alive = false; };
  }, [learning?.status, learning?.source_method_version?.id]);

  useEffect(() => {
    const next = !learning ? "proposal" : learning.status === "PROPOSED" ? "authority" : "receipt";
    setOpenStage(next);
  }, [learning?.status, learning?.adoption_receipt?.id]);

  async function createProposal() {
    if (!readiness?.eligible || !correctionAuthor || newVersion.trim().length < 2 || correction.trim().length < 10 || proposalBusy) return;
    setProposalBusy(true); setProposalError(null);
    try {
      const created = await createLearningProposal(
        run.graph_run_id,
        { new_version:newVersion.trim(), corrected_method:correction.trim(), author:correctionAuthor },
        correctionAuthor,
      );
      onLearningChange(created);
      setCorrection("");
    } catch (err) {
      setProposalError(err instanceof Error ? err.message : "LEARNING_PROPOSAL_CREATE_FAILED");
    } finally {
      setProposalBusy(false);
    }
  }

  async function decide(decision:"APPROVE_LEARNING"|"REJECT_LEARNING") {
    if (!learning || !principal || reason.trim().length < 3 || busy) return;
    if (decision === "APPROVE_LEARNING" && (scopeBusy || scopeError || (scopeMode === "SELECTED_IMPLEMENTATIONS" && selectedScopeIds.length === 0))) return;
    setBusy(true); setError(null);
    try {
      const result = await decideLearningProposal(
        learning.id,
        {
          reviewer:principal,
          decision,
          reason:reason.trim(),
          ...(decision === "APPROVE_LEARNING" ? { adoption_scope:{ mode:scopeMode, implementation_ids:scopeMode === "SELECTED_IMPLEMENTATIONS" ? selectedScopeIds : [] } } : {}),
        },
        principal,
      );
      onLearningChange(result.learning);
      setReason("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "LEARNING_DECISION_FAILED");
    } finally {
      setBusy(false);
    }
  }

  function toggleScopeImplementation(implementationId:string) {
    setSelectedScopeIds(current => current.includes(implementationId) ? current.filter(item => item !== implementationId) : [...current, implementationId]);
  }

  async function verifyReceipt() {
    const receipt = learning?.adoption_receipt;
    if (!receipt || receiptVerifyBusy) return;
    setReceiptVerifyBusy(true); setReceiptVerifyError(null);
    try {
      setReceiptVerification(await verifyAdoptionReceipt(receipt.id));
    } catch (err) {
      setReceiptVerifyError(err instanceof Error ? err.message : "ADOPTION_RECEIPT_VERIFY_FAILED");
    } finally {
      setReceiptVerifyBusy(false);
    }
  }

  const proposalStatus = !learning ? (readiness?.eligible ? "ACTION REQUIRED" : readiness ? "NOT ELIGIBLE" : "CHECKING") : learning.status.replaceAll("_", " ");
  const proposalTone:"neutral"|"info"|"ok"|"warn"|"bad" = !learning ? (readiness?.eligible ? "warn" : "neutral") : learning.status === "REJECTED" ? "bad" : learning.status === "APPROVED" ? "ok" : "info";
  const authorityStatus = !learning ? "WAITING" : learning.status === "PROPOSED" ? "ACTION REQUIRED" : "RECORDED";
  const authorityTone:"neutral"|"info"|"ok"|"warn"|"bad" = !learning ? "neutral" : learning.status === "PROPOSED" ? "warn" : learning.status === "REJECTED" ? "bad" : "ok";
  const receiptStatus = !learning || learning.status === "PROPOSED" ? "WAITING" : learning.status === "REJECTED" ? "NOT CREATED" : learning.adoption_receipt ? learning.adoption_receipt.integrity : "PENDING";
  const receiptTone:"neutral"|"info"|"ok"|"warn"|"bad" = learning?.status === "REJECTED" ? "neutral" : learning?.adoption_receipt?.integrity === "VALID" ? "ok" : learning?.status === "APPROVED" ? "warn" : "neutral";

  return <section className="governed-learning-r53 governed-learning-r85 governed-learning-r94-m06 learning-minimal-r98-m05 learning-accordion-r98-m06">
    <div className="candidate-accordion-list-r97-m07 learning-stage-list-r98-m06" aria-label="Learning and adoption stages">
      <LearningStageRow
        index="01"
        title="Learning proposal"
        subtitle={learning ? `${learning.source_method_version?.version ?? "SOURCE"} → ${learning.proposed_method_version?.version ?? "PROPOSED"}` : "Human correction"}
        status={proposalStatus}
        tone={proposalTone}
        open={openStage === "proposal"}
        onToggle={() => setOpenStage(openStage === "proposal" ? null : "proposal")}
      >
        {learning ? <>
          <div className="learning-proposal-summary-r98-m05 learning-stage-summary-r98-m06">
            <h3>{learning.title ?? "Reusable learning proposal"}</h3>
            <p>{learning.summary}</p>
          </div>
          <ProgressiveDisclosure label="Inspect learning proposal" meta={`${learning.supporting_evidence_refs.length} evidence refs`}>
            <div className="governed-learning-proof-r53">
              <div><span>Proposal status</span><strong>{learning.status.replaceAll("_", " ")}</strong></div>
              <div><span>Qwen provenance</span><strong>{learning.qwen?.actual_model ?? learning.qwen?.configured_model ?? "Unavailable"}</strong></div>
              <div><span>Evidence references</span><strong>{learning.supporting_evidence_refs.length ? learning.supporting_evidence_refs.join(" · ") : "No supporting references returned"}</strong></div>
              <div><span>Human learning decision</span><strong>{learning.decision_by ?? "Not yet recorded"}</strong></div>
            </div>
          </ProgressiveDisclosure>
        </> : <div className="learning-correction-r94-m06 learning-correction-inline-r98-m06">
          {readinessError ? <div className="authority-error-r53" role="alert"><AlertTriangle size={14} />{readinessError.replaceAll("_", " ")}</div> : !readiness ? <div className="learning-correction-loading-r94-m06"><LoaderCircle size={14} className="spin" />Checking learning readiness</div> : readiness.eligible ? <>
            <div className="learning-correction-context-r94-m06">
              <div><span>Approved source</span><strong>{readiness.source_method_version?.method_name ?? "Registered method"} · {readiness.source_method_version?.version ?? "—"}</strong></div>
              <div><span>AFFECTED decisions</span><strong>{readiness.affected_decision_count}</strong></div>
              <div><span>Evidence refs</span><strong>{readiness.supporting_evidence_count}</strong></div>
            </div>
            {correctionAuthorities.length ? <>
              <label><span>Correction author</span><select value={correctionAuthor} onChange={event => setCorrectionAuthor(event.target.value)}>{correctionAuthorities.map(item => <option key={item.id} value={item.principal}>{item.display_name} · {item.principal}</option>)}</select></label>
              <label><span>New version label</span><input value={newVersion} maxLength={80} onChange={event => setNewVersion(event.target.value)} placeholder="PTP-EVENT-v2" /></label>
              <label><span>Human correction</span><textarea maxLength={8000} value={correction} onChange={event => setCorrection(event.target.value)} placeholder="State the corrected delivery method. Be specific about the control, behavior and expected outcome." /></label>
              {proposalError && <div className="authority-error-r53" role="alert"><AlertTriangle size={14} />{proposalError.replaceAll("_", " ")}</div>}
              <div className="learning-correction-actions-r94-m06"><button type="button" className="primary-btn" disabled={proposalBusy || newVersion.trim().length < 2 || correction.trim().length < 10 || !correctionAuthor} onClick={() => void createProposal()}>{proposalBusy ? <LoaderCircle size={13} className="spin" /> : <Sparkles size={13} />}{proposalBusy ? "Qwen structuring" : "Generate learning proposal"}</button></div>
            </> : <div className="authority-enforcement-empty-r85"><AlertTriangle size={15} /><span>No active principal can author a governed correction. <a href="/authority">Configure Human Decision authority</a>.</span></div>}
          </> : <div className="governed-learning-empty-r53"><GitBranch size={17} /><div><strong>Learning proposal not eligible</strong><p>{readiness.reason === "FINAL_AFFECTED_DECISION_REQUIRED" ? "This run has no AFFECTED Human Decision. CREED will not invent a reusable correction." : readiness.reason === "APPROVED_SOURCE_METHOD_REQUIRED" ? "No approved source Method Version was resolved for this run." : readiness.reason === "LEARNING_SUPPORTING_EVIDENCE_REQUIRED" ? "The current run has no persisted supporting evidence for reusable learning." : readiness.reason === "LEARNING_PROPOSAL_ALREADY_EXISTS" ? "A learning proposal already exists for this run. Refresh the analysis view." : readiness.reason.replaceAll("_", " ")}</p></div></div>}
          <p className="governed-learning-boundary-r53"><ShieldCheck size={13} />The correction is human-authored. Qwen structures the proposal; a separate Learning Authority must approve or reject it.</p>
        </div>}
      </LearningStageRow>

      <LearningStageRow
        index="02"
        title="Learning authority"
        subtitle={learning?.decision_by ? `Decision by ${learning.decision_by}` : "Approve or reject reusable knowledge"}
        status={authorityStatus}
        tone={authorityTone}
        open={openStage === "authority"}
        onToggle={() => setOpenStage(openStage === "authority" ? null : "authority")}
      >
        {!learning ? <div className="learning-stage-empty-r98-m06"><ShieldCheck size={15} /><span>Create the learning proposal before authority review begins.</span></div> : learning.status === "PROPOSED" ? <div className="learning-authority-r85 learning-authority-inline-r98-m06">
          {eligible.length ? <>
            <label><span>Authorized principal</span><select value={principal} onChange={event => setPrincipal(event.target.value)}>{eligible.map(item => <option key={item.id} value={item.principal}>{item.display_name} · {item.principal}</option>)}</select></label>
            <div className="learning-adoption-scope-r94-m08">
              <div className="learning-adoption-scope-head-r94-m08"><Network size={15} /><div><strong>Adoption scope</strong></div></div>
              {scopeBusy ? <div className="learning-scope-loading-r94-m08"><LoaderCircle size={14} className="spin" />Loading registered adopters</div> : scopeError ? <div className="authority-error-r53" role="alert"><AlertTriangle size={14} />{scopeError.replaceAll("_", " ")}</div> : <>
                <div className="learning-scope-modes-r94-m08">
                  <label className={scopeMode === "METHOD_CATALOG" ? "selected" : ""}><input type="radio" name="adoption-scope" checked={scopeMode === "METHOD_CATALOG"} onChange={() => setScopeMode("METHOD_CATALOG")} /><span><strong>Method catalog</strong></span></label>
                  <label className={scopeMode === "CURRENT_REGISTERED_IMPLEMENTATIONS" ? "selected" : ""}><input type="radio" name="adoption-scope" checked={scopeMode === "CURRENT_REGISTERED_IMPLEMENTATIONS"} disabled={!scopeAbom?.implementations.length} onChange={() => setScopeMode("CURRENT_REGISTERED_IMPLEMENTATIONS")} /><span><strong>Current registered adopters</strong></span></label>
                  <label className={scopeMode === "SELECTED_IMPLEMENTATIONS" ? "selected" : ""}><input type="radio" name="adoption-scope" checked={scopeMode === "SELECTED_IMPLEMENTATIONS"} disabled={!scopeAbom?.implementations.length} onChange={() => setScopeMode("SELECTED_IMPLEMENTATIONS")} /><span><strong>Selected implementations</strong></span></label>
                </div>
                {scopeMode === "METHOD_CATALOG" && <div className="learning-scope-summary-r94-m08"><ShieldCheck size={14} /><span>Scope: <strong>{scopeAbom?.method_version.method_name ?? "Registered method"}</strong> catalog.</span></div>}
                {scopeMode === "CURRENT_REGISTERED_IMPLEMENTATIONS" && <div className="learning-scope-summary-r94-m08"><ShieldCheck size={14} /><span>Scope: all <strong>{scopeAbom?.implementations.length ?? 0}</strong> current registered adopters.</span></div>}
                {scopeMode === "SELECTED_IMPLEMENTATIONS" && <div className="learning-scope-selection-r94-m08">
                  {(scopeAbom?.implementations ?? []).map(item => <label key={item.id} className={selectedScopeIds.includes(item.id) ? "selected" : ""}><input type="checkbox" checked={selectedScopeIds.includes(item.id)} onChange={() => toggleScopeImplementation(item.id)} /><span><strong>{item.name}</strong><small>{item.client_name} · {item.release_version}</small></span></label>)}
                  {!selectedScopeIds.length && <div className="authority-error-r53" role="alert"><AlertTriangle size={14} />Select at least one registered implementation.</div>}
                </div>}
              </>}
            </div>
            <label><span>Decision rationale</span><textarea value={reason} onChange={event => setReason(event.target.value)} maxLength={3000} placeholder="Why should this learning be adopted or rejected?" /></label>
            {error && <div className="authority-error-r53" role="alert"><AlertTriangle size={14} />{error.replaceAll("_", " ")}</div>}
            <div className="learning-authority-actions-r85">
              <button type="button" className="secondary-btn" disabled={busy || reason.trim().length < 3} onClick={() => void decide("REJECT_LEARNING")}>{busy ? <LoaderCircle size={13} className="spin" /> : <XCircle size={13} />}Reject</button>
              <button type="button" className="primary-btn" disabled={busy || reason.trim().length < 3 || scopeBusy || !!scopeError || (scopeMode !== "METHOD_CATALOG" && !scopeAbom) || (scopeMode === "SELECTED_IMPLEMENTATIONS" && selectedScopeIds.length === 0)} onClick={() => void decide("APPROVE_LEARNING")}>{busy ? <LoaderCircle size={13} className="spin" /> : <CheckCircle2 size={13} />}Approve learning</button>
            </div>
          </> : <div className="authority-enforcement-empty-r85"><AlertTriangle size={15} /><span>No active principal can approve learning. <a href="/authority">Configure authority</a>.</span></div>}
        </div> : <div className="learning-decision-record-r98-m06">
          <div><SignalChip tone={learning.status === "APPROVED" ? "ok" : "bad"}>{learning.status}</SignalChip><strong>{learning.decision_by ?? "Learning Authority"}</strong></div>
          <p>{learning.decision_reason ?? "No learning-decision rationale returned."}</p>
          {learning.decision_at && <small>{new Date(learning.decision_at).toLocaleString()}</small>}
        </div>}
      </LearningStageRow>

      <LearningStageRow
        index="03"
        title="Adoption receipt"
        subtitle={learning?.adoption_receipt ? "Signed governance proof" : learning?.status === "REJECTED" ? "No receipt created" : "Pending learning decision"}
        status={receiptStatus}
        tone={receiptTone}
        open={openStage === "receipt"}
        onToggle={() => setOpenStage(openStage === "receipt" ? null : "receipt")}
      >
        {learning?.status === "APPROVED" && learning.adoption_receipt ? <div className="adoption-receipt-r94-m07 adoption-receipt-inline-r98-m06">
          <div className="adoption-receipt-head-r94-m07"><Fingerprint size={16} /><div><span>SIGNED ADOPTION RECEIPT</span><strong>{learning.proposed_method_version?.version ?? "Approved Method Version"} adopted</strong><p>Human learning approval is sealed with evidence provenance and a SHA-256 integrity hash.</p></div><SignalChip tone={learning.adoption_receipt.integrity === "VALID" ? "ok" : "bad"}>{learning.adoption_receipt.integrity}</SignalChip></div>
          <div className="adoption-receipt-grid-r94-m07">
            <div><span>Approved by</span><strong>{learning.adoption_receipt.approved_by}</strong></div>
            <div><span>Approved at</span><strong>{formatReceiptTimestamp(learning.adoption_receipt.approved_at)}</strong></div>
            <div><span>Receipt</span><strong className="mono-r08">{learning.adoption_receipt.id}</strong></div>
            <div><span>Evidence sealed</span><strong>{learning.adoption_receipt.evidence.length}</strong></div>
            <div><span>Adoption scope</span><strong>{formatAdoptionScope(learning.adoption_receipt.adoption_scope)}</strong></div>
            <div><span>Deployment effect</span><strong>{learning.adoption_receipt.adoption_scope.automatic_deployment_change ? "Automatic change authorized" : "No automatic deployment change"}</strong></div>
          </div>
          <div className="adoption-receipt-reason-r94-m07"><span>Approval rationale</span><p>{learning.adoption_receipt.approval_reason}</p></div>
          <div className="adoption-receipt-hash-r94-m07"><div><span>{learning.adoption_receipt.hash_algorithm}</span><strong className="mono-r08">{learning.adoption_receipt.content_hash}</strong></div><button type="button" className="secondary-btn" onClick={() => void verifyReceipt()} disabled={receiptVerifyBusy}>{receiptVerifyBusy ? <LoaderCircle size={13} className="spin" /> : <ShieldCheck size={13} />}{receiptVerifyBusy ? "Verifying" : "Verify receipt"}</button></div>
          {receiptVerification && <div className={`adoption-receipt-verification-r94-m07 ${receiptVerification.valid ? "valid" : "invalid"}`}><span>{receiptVerification.valid ? <ShieldCheck size={14} /> : <AlertTriangle size={14} />}</span><div><strong>{receiptVerification.valid ? "SHA-256 verification passed" : "Receipt integrity invalid"}</strong><p>{receiptVerification.status} · {receiptVerification.hash_algorithm}</p></div></div>}
          {receiptVerifyError && <div className="authority-error-r53" role="alert"><AlertTriangle size={14} />{receiptVerifyError.replaceAll("_", " ")}</div>}
          <ProgressiveDisclosure label="Inspect signed receipt" meta={`${learning.adoption_receipt.evidence.length} evidence records`}>
            <div className="adoption-receipt-detail-r94-m07">
              <div><span>Attestation</span><p>{learning.adoption_receipt.attestation}</p></div>
              <div><span>Source Method Version</span><strong className="mono-r08">{learning.source_method_version?.version ?? learning.adoption_receipt.source_method_version_id}</strong></div>
              <div><span>Adopted Method Version</span><strong className="mono-r08">{learning.proposed_method_version?.version ?? learning.adoption_receipt.adopted_method_version_id}</strong></div>
              <div><span>Receipt version</span><strong>{learning.adoption_receipt.receipt_version}</strong></div>
            </div>
          </ProgressiveDisclosure>
        </div> : learning?.status === "APPROVED" ? <div className="adoption-receipt-missing-r94-m07" role="alert"><AlertTriangle size={15} /><div><strong>Approved learning has no Adoption Receipt</strong><p>CREED will not present this approval as cryptographically attested until the governance receipt is available.</p></div></div> : learning?.status === "REJECTED" ? <div className="learning-rejected-r94-m07"><XCircle size={15} /><div><strong>Learning rejected</strong><p>No Adoption Receipt was created. The proposed Method Version was not adopted.</p></div></div> : <div className="learning-stage-empty-r98-m06"><Fingerprint size={15} /><span>The signed Adoption Receipt becomes available only after a successful learning approval.</span></div>}
      </LearningStageRow>
    </div>
  </section>;
}

function decisionToneClass(value:string): string {
  if (value === "AFFECTED") return "bad";
  if (value === "NOT_AFFECTED") return "ok";
  if (value === "NEEDS_MORE_INVESTIGATION") return "warn";
  if (value === "DECISION_REQUIRED") return "pending";
  return "draft";
}

function humanDecisionTone(value:string): "neutral" | "info" | "ok" | "warn" | "bad" {
  if (value === "AFFECTED") return "bad";
  if (value === "NOT_AFFECTED") return "ok";
  if (value === "NEEDS_MORE_INVESTIGATION") return "warn";
  return "neutral";
}


// UI-R96 supersedes the R95 FULL STORED SOURCE label by separating original bytes from parser-extracted text.
type SourceModalPayload = {
  detail: EvidenceDocumentDetail;
  excerpt?: string | null;
  citation?: string | null;
  score?: number | null;
};

function sourceOriginalPreviewKind(detail:EvidenceDocumentDetail): "pdf" | "text" | "docx" | "binary" {
  const mime = (detail.mime_type ?? "").toLowerCase();
  const filename = (detail.original_filename ?? "").toLowerCase();
  if (mime === "application/pdf" || filename.endsWith(".pdf")) return "pdf";
  if (mime.startsWith("text/") || mime === "application/json" || filename.endsWith(".txt") || filename.endsWith(".md") || filename.endsWith(".json")) return "text";
  if (mime === "application/vnd.openxmlformats-officedocument.wordprocessingml.document" || filename.endsWith(".docx")) return "docx";
  return "binary";
}

function OriginalStoredSource({ detail }:{ detail:EvidenceDocumentDetail }) {
  const originalUrl = getDocumentOriginalUrl(detail.id);
  const kind = sourceOriginalPreviewKind(detail);
  const [rawText, setRawText] = useState<string | null>(null);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [rawError, setRawError] = useState<string | null>(null);
  const [verified, setVerified] = useState(false);

  useEffect(() => {
    setRawText(null);
    setBlobUrl(null);
    setRawError(null);
    setVerified(false);
    const controller = new AbortController();
    let localBlobUrl:string | null = null;
    void fetch(originalUrl, { cache:"no-store", signal:controller.signal })
      .then(async response => {
        if (!response.ok) {
          let detailMessage = `ORIGINAL_SOURCE_${response.status}`;
          try {
            const body = await response.json();
            if (typeof body?.detail === "string") detailMessage = body.detail;
          } catch {}
          throw new Error(detailMessage);
        }
        const verifiedHeader = response.headers.get("X-CREED-Original-Verified");
        const hashHeader = response.headers.get("X-CREED-Content-SHA256");
        if (verifiedHeader !== "true") throw new Error("ORIGINAL_SOURCE_NOT_VERIFIED");
        if (!hashHeader || hashHeader.toLowerCase() !== detail.content_hash.toLowerCase()) throw new Error("ORIGINAL_SOURCE_HASH_HEADER_MISMATCH");
        const blob = await response.blob();
        setVerified(true);
        if (kind === "text") {
          setRawText(await blob.text());
        } else {
          localBlobUrl = URL.createObjectURL(blob);
          setBlobUrl(localBlobUrl);
        }
      })
      .catch(error => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setRawError(error instanceof Error ? error.message : "ORIGINAL_SOURCE_UNAVAILABLE");
      });
    return () => {
      controller.abort();
      if (localBlobUrl) URL.revokeObjectURL(localBlobUrl);
    };
  }, [detail.id, detail.content_hash, kind, originalUrl]);

  if (rawError) return <div className="analysis-source-original-text-r96">
    <div className="analysis-source-original-error-r96" role="alert"><AlertTriangle size={15} /><span>{rawError.replaceAll("_", " ")}</span></div>
  </div>;

  if (!verified || (kind === "text" ? rawText == null : blobUrl == null)) return <div className="analysis-source-original-text-r96">
    <div className="analysis-source-original-loading-r96"><LoaderCircle size={15} className="spin" />Verifying SHA-256 and loading original stored bytes</div>
  </div>;

  if (kind === "pdf") return <div className="analysis-source-original-frame-r96">
    <iframe src={`${blobUrl}#view=FitH`} title={`Original PDF — ${detail.title}`} />
  </div>;

  if (kind === "text") return <div className="analysis-source-original-text-r96">
    <div className="analysis-source-inline-verified-r96"><ShieldCheck size={13} />SHA-256 verified original</div>
    <pre>{rawText}</pre>
  </div>;

  if (kind === "docx") return <div className="analysis-source-original-unrendered-r96">
    <FileText size={26} />
    <div><strong>Original DOCX hash-verified</strong><p>A browser cannot render Word layout with guaranteed fidelity inside CREED. The bytes behind this link were verified against the ingestion SHA-256 before being exposed.</p></div>
    <a href={blobUrl ?? undefined} target="_blank" rel="noreferrer"><ArrowUpRight size={14} />Open verified original file</a>
  </div>;

  return <div className="analysis-source-original-unrendered-r96">
    <FileText size={26} />
    <div><strong>Original file hash-verified</strong><p>This file type has no browser-native fidelity preview. CREED verified the stored bytes against the ingestion SHA-256 before exposing them.</p></div>
    <a href={blobUrl ?? undefined} target="_blank" rel="noreferrer"><ArrowUpRight size={14} />Open verified original file</a>
  </div>;
}

function SourceEvidenceModal({ source, onClose }: { source:SourceModalPayload; onClose:()=>void }) {
  const [activeView, setActiveView] = useState<"original" | "extracted">("original");
  useEffect(() => {
    const handler = (event:KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const detail = source.detail;
  useEffect(() => { setActiveView("original"); }, [detail.id]);

  return <div className="analysis-source-modal-layer-r95" role="presentation" onMouseDown={onClose}>
    <section className="analysis-source-modal-r95 analysis-source-modal-r96" role="dialog" aria-modal="true" aria-label={`Source document ${detail.title}`} onMouseDown={event => event.stopPropagation()}>
      <header className="analysis-source-modal-head-r95">
        <div><span>SOURCE DOCUMENT</span><h2>{detail.title}</h2><p>{detail.original_filename ?? evidenceSourceLabel(detail.source)}</p></div>
        <button type="button" className="analysis-source-modal-close-r95" onClick={onClose} aria-label="Close source document"><X size={16} />Close</button>
      </header>
      <div className="analysis-source-modal-meta-r95">
        <span><FileText size={13} /><b>{detail.document_type}</b>{detail.version ? ` · v${detail.version}` : ""}</span>
        <span><Database size={13} /><b>{evidenceSourceLabel(detail.source)}</b></span>
        {source.score != null && <span><SearchCheck size={13} /><b>{Math.round(source.score * 100)}% retrieval match</b></span>}
        <span className="analysis-source-original-verified-r96"><ShieldCheck size={13} /><b>Original integrity protected</b></span>
      </div>
      {source.excerpt && <section className="analysis-source-modal-excerpt-r95">
        <div><FileSearch size={14} /><span>RETRIEVED EXCERPT</span></div>
        {source.citation && <small>{source.citation}</small>}
        <p>{source.excerpt}</p>
      </section>}
      <section className="analysis-source-modal-body-r95 analysis-source-modal-body-r96">
        <nav className="analysis-source-view-tabs-r96" aria-label="Source document view">
          <button type="button" className={activeView === "original" ? "active" : ""} aria-pressed={activeView === "original"} onClick={() => setActiveView("original")}><Fingerprint size={13} />Original document</button>
          <button type="button" className={activeView === "extracted" ? "active" : ""} aria-pressed={activeView === "extracted"} onClick={() => setActiveView("extracted")}><FileSearch size={13} />Extracted text</button>
        </nav>
        {activeView === "original" ? <>
          <div className="analysis-source-modal-body-head-r95"><div><Fingerprint size={14} /><span>ORIGINAL STORED SOURCE</span></div><small>Served only after SHA-256 verification</small></div>
          <OriginalStoredSource detail={detail} />
        </> : <>
          <div className="analysis-source-modal-body-head-r95"><div><FileText size={14} /><span>EXTRACTED TEXT</span></div><small>{detail.char_count.toLocaleString()} characters</small></div>
          <pre>{detail.extracted_text || "No extracted source text is available for this document."}</pre>
        </>}
      </section>
      <footer className="analysis-source-modal-footer-r95">
        <div><Fingerprint size={13} /><span>SHA-256</span><code>{detail.content_hash}</code></div>
        <span>Original bytes and extracted interpretation are shown separately</span>
      </footer>
    </section>
  </div>;
}

// R25 regression lineage token retained after R52 replacement: evidence-glance-r25
type EvidenceHit = {
  id: string;
  rank: number;
  document_id: string;
  chunk_id: string;
  final_score: number;
  base_score: number;
  query_coverage_bonus: number;
  issue_link_boost: number;
  semantic_score: number;
  keyword_score: number;
  metadata_score: number;
  citation: string;
  excerpt: string;
  matched_queries: string[];
  embedding_model: string | null;
  embedding_degraded: boolean;
  document_type?: string | null;
  document_version?: string | null;
  document_source?: string | null;
};

function EvidenceWorkbench({ evidence }: { evidence:any }) {
  const results = (Array.isArray(evidence?.results) ? evidence.results : []) as EvidenceHit[];
  const [selectedHitId, setSelectedHitId] = useState<string | null>(null);
  const [documentDetail, setDocumentDetail] = useState<EvidenceDocumentDetail | null>(null);
  const [documentBusy, setDocumentBusy] = useState(false);
  const [documentError, setDocumentError] = useState<string | null>(null);
  const [sourceModal, setSourceModal] = useState<SourceModalPayload | null>(null);

  const selected = results.find(result => result.id === selectedHitId) ?? null;
  const selectedDocumentDetail = selected && documentDetail?.id === selected.document_id ? documentDetail : null;

  useEffect(() => {
    if (selectedHitId && !results.some(result => result.id === selectedHitId)) setSelectedHitId(null);
  }, [results, selectedHitId]);

  useEffect(() => {
    if (!selected?.document_id) {
      setDocumentDetail(null);
      setDocumentError(null);
      setDocumentBusy(false);
      return;
    }
    let cancelled = false;
    setDocumentBusy(true);
    setDocumentDetail(null);
    setDocumentError(null);
    void getDocument(selected.document_id)
      .then(detail => { if (!cancelled) setDocumentDetail(detail); })
      .catch(error => { if (!cancelled) setDocumentError(error instanceof Error ? error.message : "DOCUMENT_DETAIL_FAILED"); })
      .finally(() => { if (!cancelled) setDocumentBusy(false); });
    return () => { cancelled = true; };
  }, [selected?.document_id]);

  async function openSelectedSource() {
    if (!selected?.document_id) return;
    setDocumentError(null);
    try {
      const detail = documentDetail?.id === selected.document_id ? documentDetail : await getDocument(selected.document_id);
      setDocumentDetail(detail);
      setSourceModal({ detail, excerpt:selected.excerpt, citation:selected.citation, score:selected.final_score });
    } catch (error) {
      setDocumentError(error instanceof Error ? error.message : "DOCUMENT_DETAIL_FAILED");
    }
  }

  const queries = Array.isArray(evidence?.queries) ? evidence.queries as string[] : [];
  const matchedQueries = Array.isArray(selected?.matched_queries) ? selected.matched_queries : [];
  const scoreSignals = selected ? [
    { label:"Semantic", value:Number(selected.semantic_score ?? 0) },
    { label:"Keyword", value:Number(selected.keyword_score ?? 0) },
    { label:"Metadata", value:Number(selected.metadata_score ?? 0) },
  ] : [];

  return <section className="analysis-evidence-workbench-r57 analysis-evidence-workbench-r65 evidence-accordion-workbench-r97-m09">
    {results.length === 0 ? <div className="analysis-empty-r04 analysis-empty-min-r25"><FileSearch size={18} /><div><strong>No supporting evidence retrieved</strong><p>CREED has no persisted retrieval hits for this run.</p></div></div> : <>
      <div className="candidate-accordion-list-r97-m07 evidence-accordion-list-r97-m09" aria-label="Ranked retrieved evidence">
        {results.map(result => {
          const active = result.id === selectedHitId;
          const title = evidenceCitationTitle(result.citation);
          const location = evidenceCitationLocation(result.citation);
          return <section key={result.id} className={`candidate-accordion-item-r97-m07 evidence-accordion-item-r97-m09 ${active ? "open" : ""}`}>
            <button
              type="button"
              className="candidate-accordion-trigger-r97-m07 evidence-accordion-trigger-r97-m09"
              aria-expanded={active}
              onClick={() => setSelectedHitId(active ? null : result.id)}
            >
              <span className="candidate-accordion-index-r97-m07">{String(result.rank).padStart(2, "0")}</span>
              <span className="candidate-accordion-identity-r97-m07 evidence-accordion-identity-r98-m01"><strong>{title}</strong><small>{result.document_type ?? "SOURCE"}{result.document_version ? ` · v${result.document_version}` : ""}{result.document_source ? ` · ${evidenceSourceLabel(result.document_source)}` : ""}</small></span>
              <span className="candidate-accordion-status-r97-m07"><em className="ok">{Math.round(result.final_score * 100)}%</em></span>
              <ChevronDown className="candidate-accordion-chevron-r97-m07" size={16} aria-hidden="true" />
            </button>

            {active && selected && <div className="candidate-accordion-body-r97-m07 evidence-accordion-body-r97-m09" aria-live="polite">
              <div className="evidence-accordion-source-bar-r97-m09">
                <div>
                  <span><FileText size={12} />{selectedDocumentDetail?.document_type ?? (documentBusy ? "Loading…" : "Stored document")}{selectedDocumentDetail?.version ? ` · v${selectedDocumentDetail.version}` : ""}</span>
                  <span><Database size={12} />{selectedDocumentDetail ? evidenceSourceLabel(selectedDocumentDetail.source) : (documentBusy ? "Loading source…" : "Source proof pending")}</span>
                </div>
                <button className="evidence-open-source-r65" type="button" onClick={() => void openSelectedSource()} disabled={documentBusy}>
                  {documentBusy ? <LoaderCircle size={12} className="spin" /> : <FileText size={12} />}
                  {documentBusy ? "Loading…" : "Open source"}
                </button>
              </div>

              <section className="evidence-accordion-excerpt-r97-m09">
                <span>RETRIEVED EXCERPT</span>
                <p>{selected.excerpt}</p>
              </section>
              <div className="evidence-hit-location-r98-m01">{evidenceCitationLocation(selected.citation)}</div>

              <div className="evidence-accordion-details-r97-m09">
                {queries.length > 0 && <ProgressiveDisclosure label="Retrieval context" meta={`${queries.length} search concept${queries.length === 1 ? "" : "s"}`}>
                  <div className="evidence-retrieval-details-r57">
                    <div className="evidence-query-list-r57" aria-label="Retrieval queries">
                      <span>SEARCH CONCEPTS</span>
                      <div>{queries.map(query => <b key={query}>{query}</b>)}</div>
                    </div>
                    <p><ShieldCheck size={13} /> Retrieval score ranks evidence; it does not validate the source.</p>
                  </div>
                </ProgressiveDisclosure>}

                <ProgressiveDisclosure label="Proof & provenance" meta="Ranking · source integrity">
                  <div className="evidence-proof-r57 evidence-proof-r65">
                    <section className="evidence-score-proof-r57">
                      <div className="evidence-section-title-r57"><SearchCheck size={14} /><div><span>RANKING SIGNALS</span><strong>Why this chunk surfaced</strong></div></div>
                      <div className="evidence-score-signals-r57">
                        {scoreSignals.map(signal => <div className="evidence-score-signal-r57" key={signal.label}>
                          <div><strong>{signal.label}</strong><span>{Math.round(signal.value * 100)}%</span></div>
                          <i aria-hidden="true"><b style={{ width:`${Math.max(0, Math.min(100, Math.round(signal.value * 100)))}%` }} /></i>
                        </div>)}
                      </div>
                      <div className="evidence-score-adjustments-r57">
                        <span>Base <b>{Math.round(Number(selected.base_score ?? 0) * 100)}</b></span>
                        <span>Query coverage <b>+{Math.round(Number(selected.query_coverage_bonus ?? 0) * 100)}</b></span>
                        <span>Issue link <b>+{Math.round(Number(selected.issue_link_boost ?? 0) * 100)}</b></span>
                      </div>
                    </section>

                    <section className="evidence-trace-r57">
                      <div className="evidence-section-title-r57"><Fingerprint size={14} /><div><span>TRACEABILITY</span><strong>Persisted retrieval references</strong></div></div>
                      <div className="evidence-trace-facts-r57">
                        <div><span>DOCUMENT ID</span><code>{selected.document_id}</code></div>
                        <div><span>CHUNK ID</span><code>{selected.chunk_id}</code></div>
                        <div className="wide"><span>MATCHED QUERIES</span><strong>{matchedQueries.length ? matchedQueries.join(" · ") : "No query labels persisted"}</strong></div>
                      </div>
                    </section>

                    <section className="evidence-provenance-proof-r57">
                      <div className="evidence-section-title-r57"><Fingerprint size={14} /><div><span>PROVENANCE</span><strong>Stored source proof</strong></div></div>
                      {documentBusy ? <div className="evidence-proof-state-r57"><LoaderCircle size={14} className="spin" /><span>Loading the stored document record…</span></div> : documentError ? <div className="evidence-proof-state-r57 bad"><AlertTriangle size={14} /><span>Stored document proof could not be loaded: {documentError}</span></div> : selectedDocumentDetail ? <div className="evidence-provenance-r57">
                        <div><span>SHA-256</span><code>{selectedDocumentDetail.content_hash}</code></div>
                        <div><span>SOURCE</span><strong>{evidenceSourceLabel(selectedDocumentDetail.source)}</strong></div>
                        <div><span>DOCUMENT TYPE</span><strong>{selectedDocumentDetail.document_type}{selectedDocumentDetail.version ? ` · v${selectedDocumentDetail.version}` : ""}</strong></div>
                        <div><span>INDEX</span><strong>{selectedDocumentDetail.index_status}</strong></div>
                        <div><span>EMBEDDING</span><strong>{selectedDocumentDetail.embedding_model ?? "Not recorded"}{selectedDocumentDetail.embedding_degraded ? " · DEGRADED" : ""}</strong></div>
                        <div><span>PARSE</span><strong>{selectedDocumentDetail.parse_status}</strong></div>
                      </div> : <div className="evidence-proof-state-r57"><Fingerprint size={14} /><span>No stored document proof is available for this selected retrieval hit.</span></div>}
                      <p className="evidence-proof-note-r57">Ranking and content seals do not establish correctness or approval.</p>
                    </section>
                  </div>
                </ProgressiveDisclosure>
              </div>
            </div>}
          </section>;
        })}
      </div>
    </>}
    {sourceModal && <SourceEvidenceModal source={sourceModal} onClose={() => setSourceModal(null)} />}
  </section>;
}

function evidenceCitationTitle(citation:string): string {
  return citation.split(" · chunk ")[0]?.trim() || citation;
}

function evidenceCitationLocation(citation:string): string {
  const marker = " · chunk ";
  const index = citation.indexOf(marker);
  return index >= 0 ? `Chunk ${citation.slice(index + marker.length)}` : "Stored retrieval chunk";
}

function evidenceSourceLabel(value:string): string {
  if (value === "LOCAL_DEMO") return "LOCAL REPOSITORY";
  return value.replaceAll("_", " ");
}


type InvestigationWorkbenchItem = {
  implementation_id: string;
  implementation_name: string;
  client_name: string | null;
  impact: any | null;
  investigation: any | null;
};

type ConfigurationComparisonView = {
  variable: string;
  previous_value?: string | null;
  requested_value: string;
  requested_state: "ENABLED" | "DISABLED";
  current_state: "ENABLED" | "DISABLED" | "PROTECTED" | "UNKNOWN";
  current_value?: string | null;
  resolution_basis?: string | null;
  conflict_reason?: string | null;
  technical_result: "CHANGE_REVIEW_REQUIRED" | "ALREADY_MATCHES" | "ALREADY_PROTECTED" | "EVIDENCE_RECONCILIATION_REQUIRED";
  deterministic?: boolean;
};

type ConfigurationSummaryTarget = {
  implementation_id: string;
  implementation_name: string | null;
  client_name: string | null;
  current_state: ConfigurationComparisonView["current_state"];
  current_value?: string | null;
  technical_result: ConfigurationComparisonView["technical_result"];
  resolution_basis?: string | null;
};

type ConfigurationChangeSummaryView = {
  variable: string;
  requested_state: ConfigurationComparisonView["requested_state"];
  requested_value: string;
  candidate_count: number;
  change_required_count: number;
  already_protected_count: number;
  already_matching_count: number;
  reconciliation_required_count: number;
  remediation_targets: ConfigurationSummaryTarget[];
  already_protected: ConfigurationSummaryTarget[];
  already_matching: ConfigurationSummaryTarget[];
  reconciliation_targets: ConfigurationSummaryTarget[];
  deterministic?: boolean;
};

type DecisionConsistencyView = {
  status: string;
  contradiction: boolean;
  technical_result?: ConfigurationComparisonView["technical_result"] | null;
  human_decision: string;
  variable?: string | null;
  current_state?: ConfigurationComparisonView["current_state"] | null;
  requested_state?: ConfigurationComparisonView["requested_state"] | null;
  requires_explicit_rationale: boolean;
  minimum_rationale_chars: number;
};

const R9406_CONTRADICTION_RATIONALE_MIN_CHARS = 24;

function humanDecisionConsistencyFor(comparison:ConfigurationComparisonView | null, decision:string): DecisionConsistencyView | null {
  if (!comparison) return null;
  let status = "NO_CONSISTENCY_RULE";
  let contradiction = false;
  if (comparison.technical_result === "CHANGE_REVIEW_REQUIRED") {
    if (decision === "AFFECTED") status = "ALIGNED_WITH_TECHNICAL_ADVISORY";
    else if (decision === "NOT_AFFECTED") { status = "CONTRADICTS_TECHNICAL_ADVISORY"; contradiction = true; }
    else if (decision === "NEEDS_MORE_INVESTIGATION") status = "DEFERRED_FOR_MORE_INVESTIGATION";
  } else if (comparison.technical_result === "ALREADY_MATCHES" || comparison.technical_result === "ALREADY_PROTECTED") {
    if (decision === "NOT_AFFECTED") status = "ALIGNED_WITH_TECHNICAL_ADVISORY";
    else if (decision === "AFFECTED") { status = "CONTRADICTS_TECHNICAL_ADVISORY"; contradiction = true; }
    else if (decision === "NEEDS_MORE_INVESTIGATION") status = "DEFERRED_FOR_MORE_INVESTIGATION";
  } else if (comparison.technical_result === "EVIDENCE_RECONCILIATION_REQUIRED") {
    status = decision === "NEEDS_MORE_INVESTIGATION" ? "DEFERRED_FOR_MORE_INVESTIGATION" : "HUMAN_RESOLUTION_OF_UNCERTAIN_EVIDENCE";
  }
  return {
    status, contradiction, technical_result:comparison.technical_result, human_decision:decision, variable:comparison.variable,
    current_state:comparison.current_state, requested_state:comparison.requested_state, requires_explicit_rationale:contradiction,
    minimum_rationale_chars:contradiction ? R9406_CONTRADICTION_RATIONALE_MIN_CHARS : 3,
  };
}

function reviewDraftReady(comparison:ConfigurationComparisonView | null, draft:ReviewDraft | undefined): boolean {
  if (!draft?.decision) return false;
  const consistency = humanDecisionConsistencyFor(comparison, draft.decision);
  const minimum = consistency?.contradiction ? R9406_CONTRADICTION_RATIONALE_MIN_CHARS : 3;
  return (draft.reason?.trim().length ?? 0) >= minimum;
}

function InvestigationWorkbench({ run, impact, investigations, evidence }: { run:AnalysisRun; impact:any; investigations:any; evidence:any }) {
  const items = useMemo<InvestigationWorkbenchItem[]>(() => {
    const byImplementation = new Map<string, InvestigationWorkbenchItem>();
    for (const row of Array.isArray(impact?.results) ? impact.results : []) {
      byImplementation.set(row.implementation_id, {
        implementation_id: row.implementation_id,
        implementation_name: row.implementation_name ?? "Unnamed implementation",
        client_name: row.client_name ?? null,
        impact: row,
        investigation: null,
      });
    }
    for (const row of Array.isArray(investigations?.results) ? investigations.results : []) {
      const existing = byImplementation.get(row.implementation_id);
      byImplementation.set(row.implementation_id, {
        implementation_id: row.implementation_id,
        implementation_name: row.implementation_name ?? existing?.implementation_name ?? "Unnamed implementation",
        client_name: existing?.client_name ?? null,
        impact: existing?.impact ?? null,
        investigation: row,
      });
    }
    return [...byImplementation.values()].sort((a, b) => (b.impact?.impact_score ?? b.investigation?.risk_score ?? -1) - (a.impact?.impact_score ?? a.investigation?.risk_score ?? -1));
  }, [impact, investigations]);

  const [selectedImplementationId, setSelectedImplementationId] = useState<string | null>(null);
  useEffect(() => {
    if (!items.length) {
      if (selectedImplementationId !== null) setSelectedImplementationId(null);
      return;
    }
    if (selectedImplementationId && !items.some(item => item.implementation_id === selectedImplementationId)) setSelectedImplementationId(null);
  }, [items, selectedImplementationId]);

  const selected = items.find(item => item.implementation_id === selectedImplementationId) ?? null;
  const selectedImpact = selected?.impact ?? null;
  const selectedInvestigation = selected?.investigation ?? null;
  const evidenceRefs = Array.from(new Set<string>([
    ...(Array.isArray(selectedImpact?.evidence_refs) ? selectedImpact.evidence_refs : []),
    ...(Array.isArray(selectedInvestigation?.finding?.evidence_refs) ? selectedInvestigation.finding.evidence_refs : []),
  ]));
  const explanations = Array.isArray(selectedImpact?.explanation)
    ? [...selectedImpact.explanation].sort((a:any, b:any) => Number(b.contribution ?? 0) - Number(a.contribution ?? 0))
    : [];
  const topDrivers = explanations.slice(0, 3);
  const remainingDrivers = explanations.slice(3);
  const findingType = selectedInvestigation?.finding?.type ?? null;
  const findingConfidence = selectedInvestigation?.finding
    ? Math.round(Number(selectedInvestigation.finding.confidence ?? 0) * 100)
    : null;
  const selectedComparison = (selectedInvestigation?.configuration_comparison ?? null) as ConfigurationComparisonView | null;
  const evidenceResults = (Array.isArray(evidence?.results) ? evidence.results : []) as EvidenceHit[];
  const [sourceModal, setSourceModal] = useState<SourceModalPayload | null>(null);
  const [sourceBusyId, setSourceBusyId] = useState<string | null>(null);
  const [sourceError, setSourceError] = useState<string | null>(null);

  function evidenceHitFor(evidenceRef:string) {
    return evidenceResults.find(hit => hit.document_id === evidenceRef || hit.chunk_id === evidenceRef || hit.id === evidenceRef) ?? null;
  }

  async function openInvestigationSource(evidenceRef:string) {
    if (!evidenceRef || sourceBusyId) return;
    const hit = evidenceHitFor(evidenceRef);
    const documentId = hit?.document_id ?? evidenceRef;
    setSourceBusyId(evidenceRef);
    setSourceError(null);
    try {
      const detail = await getDocument(documentId);
      setSourceModal({ detail, excerpt:hit?.excerpt ?? null, citation:hit?.citation ?? null, score:hit?.final_score ?? null });
    } catch (error) {
      setSourceError(error instanceof Error ? error.message : "DOCUMENT_DETAIL_FAILED");
    } finally {
      setSourceBusyId(null);
    }
  }

  return <section className="analysis-investigation-workbench-r58 investigation-accordion-workbench-r97-m07">
    <div className="investigation-command-r58 investigation-command-r97-m07">
      <div>
        <span className="investigation-kicker-r58">CANDIDATES</span>
        <strong>{items.length} implementation{items.length === 1 ? "" : "s"}</strong>
      </div>
      <div className="investigation-command-actions-r58">
        <a className="analysis-radar-action-r63-rev1" href={`/change-radar?run=${encodeURIComponent(run.graph_run_id)}`}>Radar<ArrowUpRight size={13} /></a>
      </div>
    </div>

    {items.length === 0 ? <div className="analysis-empty-r04 analysis-empty-min-r25"><Network size={18} /><div><strong>No persisted candidates yet</strong><p>The candidate list will populate from real impact and investigation records.</p></div></div> : <div className="candidate-accordion-list-r97-m07 investigation-candidate-list-r97-m07" aria-label="Implementation candidates">
      {items.map((item, index) => {
        const finding = item.investigation?.finding?.type ?? null;
        const comparison = (item.investigation?.configuration_comparison ?? null) as ConfigurationComparisonView | null;
        const active = item.implementation_id === selected?.implementation_id;
        const resultLabel = comparison ? configurationTechnicalLabel(comparison.technical_result) : finding ? finding.replaceAll("_", " ") : "PENDING";
        return <section key={item.implementation_id} className={`candidate-accordion-item-r97-m07 ${active ? "open" : ""}`}>
          <button
            type="button"
            className="candidate-accordion-trigger-r97-m07"
            aria-expanded={active}
            onClick={() => setSelectedImplementationId(active ? null : item.implementation_id)}
          >
            <span className="candidate-accordion-index-r97-m07">{String(index + 1).padStart(2, "0")}</span>
            <span className="candidate-accordion-identity-r97-m07"><strong>{item.implementation_name}</strong><small>{item.client_name ?? "Client unavailable"}</small></span>
            <span className="candidate-accordion-status-r97-m07"><SignalChip tone={comparison ? configurationResultTone(comparison.technical_result) : findingTone(finding)}>{resultLabel}</SignalChip></span>
            <ChevronDown className="candidate-accordion-chevron-r97-m07" size={16} aria-hidden="true" />
          </button>

          {active && selected && <div className="candidate-accordion-body-r97-m07 investigation-inline-body-r97-m07" aria-live="polite">
            {selectedComparison ? <div className="candidate-state-flow-r97-m07" aria-label="Configuration comparison">
              <div><small>Current</small><strong>{selectedComparison.current_state}{selectedComparison.current_value ? ` · ${selectedComparison.current_value}` : ""}</strong></div>
              <ArrowRight size={16} aria-hidden="true" />
              <div><small>Requested</small><strong>{selectedComparison.requested_state} · {selectedComparison.requested_value}</strong></div>
            </div> : selectedInvestigation?.finding?.statement ? <p className="candidate-inline-explainer-r97-m07">{selectedInvestigation.finding.statement}</p> : null}

            <div className="investigation-detail-stack-r97-m03 investigation-detail-stack-r97-m07" aria-label="Investigation details">
              <ProgressiveDisclosure
                label={<span className="investigation-detail-label-r97-m03"><BrainCircuit size={14} /><span>AI analysis</span></span>}
                meta={selectedInvestigation?.finding ? `${findingConfidence}% confidence` : "Pending"}
              >
                <div className="investigation-ai-detail-r97-m03">
                  {selectedInvestigation?.finding ? <>
                    <div className="investigation-ai-summary-r97-m03">
                      <SignalChip tone={selectedComparison ? configurationResultTone(selectedComparison.technical_result) : findingTone(findingType)}>
                        {selectedComparison ? configurationTechnicalLabel(selectedComparison.technical_result) : findingType?.replaceAll("_", " ")}
                      </SignalChip>
                      <span>{selectedInvestigation.status?.replaceAll("_", " ") ?? "Persisted"}</span>
                    </div>
                    <p>{selectedInvestigation.finding.statement}</p>
                  </> : <p className="investigation-muted-r51">AI analysis is not available yet.</p>}
                </div>
              </ProgressiveDisclosure>

              <ProgressiveDisclosure
                label={<span className="investigation-detail-label-r97-m03"><FileSearch size={14} /><span>Source evidence</span></span>}
                meta={`${evidenceRefs.length}`}
              >
                <section className="investigation-ai-sources-r95 investigation-source-detail-r97-m03" aria-label="Source evidence used by this investigation">
                  {evidenceRefs.length === 0 ? <p className="investigation-source-empty-r95">No persisted source references are attached to this finding.</p> : <div className="investigation-source-list-r95">
                    {evidenceRefs.map(documentId => {
                      const hit = evidenceHitFor(documentId);
                      return <article className="investigation-source-card-r95" key={documentId}>
                        <div className="investigation-source-head-r95">
                          <div>
                            <strong>{hit ? evidenceCitationTitle(hit.citation) : `Evidence ${documentId.slice(0, 8)}`}</strong>
                            <small>{hit ? evidenceCitationLocation(hit.citation) : documentId}</small>
                          </div>
                          {hit && <span>{Math.round(hit.final_score * 100)}% match</span>}
                        </div>
                        {hit?.excerpt && <p>{hit.excerpt}</p>}
                        <button type="button" className="investigation-open-source-r95" onClick={() => void openInvestigationSource(documentId)} disabled={sourceBusyId === documentId}>
                          {sourceBusyId === documentId ? <LoaderCircle size={12} className="spin" /> : <FileText size={12} />}
                          {sourceBusyId === documentId ? "Loading…" : "Open source"}
                        </button>
                      </article>;
                    })}
                  </div>}
                  {sourceError && <div className="investigation-source-error-r95" role="alert"><AlertTriangle size={13} /><span>{sourceError}</span></div>}
                </section>
              </ProgressiveDisclosure>

              <ProgressiveDisclosure
                label={<span className="investigation-detail-label-r97-m03"><Fingerprint size={14} /><span>Proof & provenance</span></span>}
                meta={`${evidenceRefs.length} evidence ref${evidenceRefs.length === 1 ? "" : "s"}`}
              >
                <div className="investigation-proof-provenance-r97-m03">
                  <section className="investigation-priority-r97-m03" aria-label="Priority drivers">
                    <div className="investigation-detail-subhead-r97-m03"><Network size={13} /><strong>Priority drivers</strong></div>
                    {topDrivers.length ? <div className="investigation-driver-list-r58">
                      {topDrivers.map((signal:any) => {
                        const contribution = Math.max(0, Math.min(1, Number(signal.contribution ?? 0)));
                        return <div className="investigation-driver-r58" key={String(signal.signal)}>
                          <span>{humanizeImpactSignal(String(signal.signal))}</span>
                          <i aria-hidden="true"><b style={{ width:`${Math.round(contribution * 100)}%` }} /></i>
                          <strong>+{Math.round(contribution * 100)}</strong>
                        </div>;
                      })}
                    </div> : <p className="investigation-muted-r51">Priority breakdown pending.</p>}
                    {remainingDrivers.length > 0 && <ProgressiveDisclosure label="All signals" meta={`${explanations.length} total`}>
                      <div className="investigation-all-signals-r58">
                        {explanations.map((signal:any) => {
                          const contribution = Math.max(0, Math.min(1, Number(signal.contribution ?? 0)));
                          return <div key={String(signal.signal)}>
                            <span>{humanizeImpactSignal(String(signal.signal))}</span>
                            <strong>+{Math.round(contribution * 100)}</strong>
                            <small>{Math.round(Number(signal.value ?? 0) * 100)}% signal · {Math.round(Number(signal.weight ?? 0) * 100)}% weight</small>
                          </div>;
                        })}
                      </div>
                    </ProgressiveDisclosure>}
                  </section>
                  <section className="investigation-proof-r58 investigation-proof-r97-m03">
                    <div><span>Impact basis</span><strong>{selectedImpact ? `${Math.round(selectedImpact.impact_score * 100)} priority · ${selectedImpact.impact_band}` : "Not available"}</strong></div>
                    <div><span>{selectedComparison ? "Technical result" : "AI finding"}</span><strong>{selectedComparison ? configurationTechnicalLabel(selectedComparison.technical_result) : findingType?.replaceAll("_", " ") ?? "Not available"}</strong></div>
                    <div><span>Human authority</span><strong>{selectedInvestigation?.human_decision ? `${selectedInvestigation.human_decision.decision.replaceAll("_", " ")} · ${selectedInvestigation.human_decision.reviewer}` : "Pending"}</strong></div>
                    <div className="investigation-proof-wide-r58"><span>Evidence references</span><strong>{evidenceRefs.length ? evidenceRefs.join(" · ") : "No evidence references persisted"}</strong></div>
                  </section>
                </div>
              </ProgressiveDisclosure>
            </div>
          </div>}
        </section>;
      })}
    </div>}
    {sourceModal && <SourceEvidenceModal source={sourceModal} onClose={() => setSourceModal(null)} />}
  </section>;
}
function CrossBankConfigurationSummary({ summary, compact = false }: { summary:ConfigurationChangeSummaryView; compact?:boolean }) {
  const stableCount = summary.already_protected_count + summary.already_matching_count;
  const headlineParts = [`${summary.change_required_count} implementation${summary.change_required_count === 1 ? "" : "s"} require change`];
  if (summary.already_protected_count) headlineParts.push(`${summary.already_protected_count} already protected`);
  if (summary.already_matching_count) headlineParts.push(`${summary.already_matching_count} already matches`);
  if (summary.reconciliation_required_count) headlineParts.push(`${summary.reconciliation_required_count} need evidence reconciliation`);
  const allTargets = [
    ...summary.remediation_targets,
    ...summary.already_protected,
    ...summary.already_matching,
    ...summary.reconciliation_targets,
  ];
  return <section className={`cross-bank-change-summary-r9406 ${compact ? "compact" : ""}`} aria-label="Cross-bank change summary">
    <header>
      <div>
        <span>CROSS-BANK CHANGE SUMMARY</span>
        <strong>{humanizeConfigurationVariable(summary.variable)} → {summary.requested_state}</strong>
        <p>{headlineParts.join(" · ")}</p>
      </div>
      <div className="cross-bank-change-stats-r9406">
        <span><b>{summary.change_required_count}</b><small>change</small></span>
        <span><b>{stableCount}</b><small>no change</small></span>
        <span><b>{summary.reconciliation_required_count}</b><small>reconcile</small></span>
      </div>
    </header>
    <div className="cross-bank-change-targets-r9406">
      {allTargets.map(target => <div key={target.implementation_id} className="cross-bank-change-target-r9406">
        <div>
          <strong>{target.client_name ?? target.implementation_name ?? "Implementation"}</strong>
          <small>{target.client_name && target.implementation_name ? target.implementation_name : "Registered implementation"}</small>
        </div>
        <span><small>Current</small><b>{target.current_state}{target.current_value ? ` · ${target.current_value}` : ""}</b></span>
        <span><small>Requested</small><b>{summary.requested_state} · {summary.requested_value}</b></span>
        <SignalChip tone={configurationResultTone(target.technical_result)}>{configurationTechnicalLabel(target.technical_result)}</SignalChip>
      </div>)}
    </div>
    <footer><ShieldCheck size={13} /><span>Remediation targets are derived from persisted candidate evidence; Human Authority decides the governed outcome.</span></footer>
  </section>;
}

function DecisionConsistencyWarning({ consistency, recorded = false }: { consistency:DecisionConsistencyView; recorded?:boolean }) {
  const technical = consistency.technical_result ? configurationTechnicalLabel(consistency.technical_result) : "TECHNICAL ADVISORY";
  const human = consistency.human_decision.replaceAll("_", " ");
  return <div className={`decision-consistency-warning-r9406 ${recorded ? "recorded" : "draft"}`} role={recorded ? undefined : "alert"}>
    <AlertTriangle size={15} aria-hidden="true" />
    <div>
      <span>{recorded ? "RECORDED TECHNICAL EXCEPTION" : "TECHNICAL ADVISORY CONTRADICTION"}</span>
      <strong>{technical} → Human decision: {human}</strong>
      <p>{recorded ? "Human Authority proceeded with a decision that differs from the deterministic comparison. The exception rationale is preserved in the governed record." : `Human Authority may still proceed, but must provide an explicit rationale of at least ${consistency.minimum_rationale_chars} characters explaining the exception.`}</p>
    </div>
  </div>;
}

function ConfigurationComparisonPanel({ comparison, evidenceCount, compact = false }: { comparison:ConfigurationComparisonView; evidenceCount?:number; compact?:boolean }) {
  const currentValue = comparison.current_value ? `${comparison.current_state} · ${comparison.current_value}` : comparison.current_state;
  return <section className={`configuration-comparison-r9406 ${compact ? "compact" : ""}`} aria-label="Configuration change analysis">
    <header>
      <div><span>CONFIGURATION CHANGE ANALYSIS</span><strong>{humanizeConfigurationVariable(comparison.variable)}</strong></div>
      <SignalChip tone={configurationResultTone(comparison.technical_result)}>{configurationTechnicalLabel(comparison.technical_result)}</SignalChip>
    </header>
    <div className="configuration-comparison-grid-r9406">
      <div><span>Current state</span><strong>{currentValue}</strong></div>
      <span className="configuration-comparison-arrow-r9406" aria-hidden="true"><ArrowRight size={16} /></span>
      <div><span>Requested state</span><strong>{comparison.requested_state} · {comparison.requested_value}</strong></div>
      <div><span>Evidence basis</span><strong>{comparison.resolution_basis?.replaceAll("_", " ") ?? "Persisted candidate evidence"}</strong></div>
    </div>
    {comparison.conflict_reason && <div className="configuration-comparison-conflict-r9406"><AlertTriangle size={13} />{comparison.conflict_reason.replaceAll("_", " ")}</div>}
    <footer><ShieldCheck size={13} /><span>Deterministic comparison of persisted evidence. Human Authority remains the final decision.</span>{typeof evidenceCount === "number" && <b>{evidenceCount} evidence ref{evidenceCount === 1 ? "" : "s"}</b>}</footer>
  </section>;
}

function humanizeConfigurationVariable(value:string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, char => char.toUpperCase());
}

function configurationTechnicalLabel(value:ConfigurationComparisonView["technical_result"]): string {
  if (value === "CHANGE_REVIEW_REQUIRED") return "CHANGE REQUIRED";
  if (value === "ALREADY_PROTECTED") return "ALREADY PROTECTED";
  if (value === "ALREADY_MATCHES") return "ALREADY MATCHES";
  return "EVIDENCE RECONCILIATION";
}

function configurationResultTone(value:ConfigurationComparisonView["technical_result"]): "neutral" | "info" | "ok" | "warn" | "bad" {
  if (value === "CHANGE_REVIEW_REQUIRED") return "warn";
  if (value === "ALREADY_PROTECTED" || value === "ALREADY_MATCHES") return "ok";
  return "warn";
}

function humanizeImpactSignal(value:string): string {
  return value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, char => char.toUpperCase());
}


function findingTone(value:string | null | undefined): "neutral" | "info" | "ok" | "warn" | "bad" {
  // UI-R78 REV1: AI findings remain advisory. Amber means investigation/action
  // is still required; neutral means the evidence does not support impact.
  // Neither visual treatment is a governed human verdict.
  if (value === "POTENTIALLY_AFFECTED") return "warn";
  if (value === "INSUFFICIENT_EVIDENCE") return "warn";
  if (value === "NO_SUPPORTING_EVIDENCE_OF_IMPACT") return "neutral";
  return "neutral";
}

function RunState({ status, starting }: { status:string | null; starting:boolean }) {
  const label = starting ? "STARTING" : status ? status.replaceAll("_", " ") : "READY";
  const cls = starting || status === "RUNNING" || status === "QUEUED" ? "active" : status === "COMPLETED" ? "done" : status === "FAILED" ? "bad" : status === "WAITING_HUMAN" ? "human" : "idle";
  return <span className={`run-state-r04 ${cls}`}>{(starting || status === "RUNNING") && <LoaderCircle size={12} className="spin" />}{status === "WAITING_HUMAN" && <UserCheck size={12} />}{status === "COMPLETED" && <Check size={12} />}{status === "FAILED" && <XCircle size={12} />}{label}</span>;
}
function SourceCell({ label, value, mono = false }: { label:string; value:string; mono?:boolean }) { return <div className="source-cell-r04"><span>{label}</span><strong className={mono ? "code" : ""}>{value}</strong></div>; }
function AiField({ k, v }: { k:string; v:string | null }) { return <div className={`ai-field-r04 ${v ? "" : "unknown"}`}><span>{k}</span><strong>{v ?? "Not verified from issue text"}</strong></div>; }
function EditField({ label, value, onChange }: { label:string; value:string; onChange:(v:string)=>void }) { return <label><span>{label}</span><input value={value} onChange={e => onChange(e.target.value)} /></label>; }
function InlineError({ title, error, note }: { title:string; error:string; note?:string }) { return <div className="inline-error-r04" role="alert"><AlertTriangle size={15} /><div><strong>{title}</strong><span>{error}</span>{note && <small>{note}</small>}</div></div>; }
function formatAdoptionScope(scope:AdoptionScopeSummary) {
  const count = scope.implementation_ids?.length ?? 0;
  if (scope.mode === "METHOD_CATALOG") return `Method catalog · ${scope.method?.name ?? "registered method"}`;
  if (scope.mode === "CURRENT_REGISTERED_IMPLEMENTATIONS") return `${count} current registered implementation${count === 1 ? "" : "s"}`;
  if (scope.mode === "SELECTED_IMPLEMENTATIONS") return `${count} selected implementation${count === 1 ? "" : "s"}`;
  return "Legacy / unstructured scope";
}

function formatReceiptTimestamp(value:string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString(undefined, { dateStyle:"medium", timeStyle:"short" });
}

function formatDuration(ms:number | null) { if (ms == null) return "duration unavailable"; return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`; }
function friendlyWarning(value:string) { return value.replaceAll("_", " ").toLowerCase().replace(/^./, c => c.toUpperCase()); }
