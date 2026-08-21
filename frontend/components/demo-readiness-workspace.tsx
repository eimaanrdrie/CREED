"use client";

import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  CircleAlert,
  Database,
  ExternalLink,
  FileText,
  Network,
  Play,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import { getDemoReadiness, resetDemoBaseline, type DemoReadiness } from "@/lib/api";
import { SignalChip } from "@/components/visual-primitives";

function CheckIcon({ status }: { status: "PASS" | "BLOCKED" | "WARN" }) {
  if (status === "PASS") return <CheckCircle2 size={17} aria-hidden="true" />;
  if (status === "WARN") return <AlertTriangle size={17} aria-hidden="true" />;
  return <CircleAlert size={17} aria-hidden="true" />;
}

export function DemoReadinessWorkspace({ initial }: { initial: DemoReadiness | null }) {
  const [data, setData] = useState(initial);
  const [busy, setBusy] = useState<"refresh" | "reset" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    if (busy) return;
    setBusy("refresh");
    setError(null);
    try {
      setData(await getDemoReadiness(true));
    } catch (err) {
      setError(err instanceof Error ? err.message : "DEMO_READINESS_FAILED");
    } finally {
      setBusy(null);
    }
  }

  async function reset() {
    if (busy) return;
    if (!window.confirm("Reset the synthetic judging dataset? Existing demo issues, decisions, learnings and recalls will be removed.")) return;
    setBusy("reset");
    setError(null);
    try {
      await resetDemoBaseline();
      setData(await getDemoReadiness(true));
    } catch (err) {
      setError(err instanceof Error ? err.message : "DEMO_RESET_FAILED");
    } finally {
      setBusy(null);
    }
  }

  const dataset = data?.dataset;
  const ready = Boolean(data?.ready);

  return (
    <main className="page demo-control-page-r94m11">
      <header className="page-header demo-control-header-r94m11">
        <div>
          <span className="eyebrow">R94-M11 · operator-only route</span>
          <h1>Demo readiness</h1>
          <p>One deterministic gate before the judging flow. This route is intentionally not added to the sidebar.</p>
        </div>
        <SignalChip tone={ready ? "ok" : "warn"} icon={ready ? ShieldCheck : CircleAlert}>
          {ready ? "READY TO START" : "BLOCKED"}
        </SignalChip>
      </header>

      {error ? <div className="alert error"><CircleAlert size={16} />{error}</div> : null}

      <section className="demo-control-actions-r94m11" aria-label="Demo controls">
        <button className="ghost-btn" type="button" onClick={refresh} disabled={Boolean(busy)}>
          <RefreshCw size={15} className={busy === "refresh" ? "spin-r94m11" : ""} />
          {busy === "refresh" ? "Checking runtime…" : "Refresh readiness"}
        </button>
        <button className="ghost-btn" type="button" onClick={reset} disabled={Boolean(busy)}>
          <RotateCcw size={15} />
          {busy === "reset" ? "Resetting…" : "Reset synthetic baseline"}
        </button>
        <a className={`primary-btn ${ready ? "" : "disabled-link-r94m11"}`} href={ready ? "/issues/new?demo=1" : undefined} aria-disabled={!ready}>
          <Play size={15} />Start live issue
        </a>
      </section>

      <section className="demo-readiness-summary-r94m11">
        <div className="card demo-stat-r94m11"><Users size={17} /><span>Clients / implementations</span><strong>{dataset ? `${dataset.clients} / ${dataset.implementations}` : "—"}</strong></div>
        <div className="card demo-stat-r94m11"><FileText size={17} /><span>Knowledge indexed</span><strong>{dataset ? `${dataset.indexed_documents}/${dataset.documents}` : "—"}</strong></div>
        <div className="card demo-stat-r94m11"><Network size={17} /><span>A-BOM edges</span><strong>{dataset?.dependency_edges ?? "—"}</strong></div>
        <div className="card demo-stat-r94m11"><Database size={17} /><span>Authorities / ownership</span><strong>{dataset ? `${dataset.active_authorities} / ${dataset.ownership_assignments}` : "—"}</strong></div>
      </section>

      <section className="card demo-readiness-card-r94m11">
        <div className="card-header">
          <div><span className="eyebrow">Fail-closed checks</span><h2>Pre-flight gate</h2></div>
          <small>{data?.blocking_checks.length ?? 0} blocker(s)</small>
        </div>
        <div className="demo-check-list-r94m11">
          {(data?.checks ?? []).map(check => (
            <div className={`demo-check-row-r94m11 tone-${check.status.toLowerCase()}`} key={check.key}>
              <span className="demo-check-icon-r94m11"><CheckIcon status={check.status} /></span>
              <div><strong>{check.label}</strong><span>{check.detail}</span></div>
              <b>{check.status}</b>
            </div>
          ))}
          {!data ? <div className="demo-empty-r94m11"><CircleAlert size={18} /><span>Readiness endpoint unavailable. Refresh after the backend is running.</span></div> : null}
        </div>
      </section>

      <section className="demo-live-case-r94m11">
        <div className="card demo-live-copy-r94m11">
          <span className="eyebrow">Enter only during the live demo</span>
          <h2>{data?.live_issue.title ?? "Network retry replays Promise-to-Pay event"}</h2>
          <p>{data?.live_issue.client ?? "Atlas Bank"} · {data?.live_issue.ticket ?? "SUP-PTP-001"} · BUG · HIGH</p>
          <div className="demo-boundary-r94m11"><Sparkles size={16} /><span>After Save & analyse, Qwen, retrieval, impact and agent status must come from real execution.</span></div>
        </div>
        <div className="card demo-live-steps-r94m11">
          <strong>Judge path</strong>
          <ol>
            <li>Save the live issue.</li>
            <li>Show Evidence → Candidates → Investigation.</li>
            <li>Submit Human Decision.</li>
            <li>Enter Human Correction and generate the Qwen proposal.</li>
            <li>Approve learning and verify the Adoption Receipt.</li>
            <li>Register any intended v2 adoption in Dependencies before demonstrating Recall.</li>
          </ol>
          <a className="overview-text-link" href="/ai-runtime">Open AI Runtime <ExternalLink size={13} /></a>
        </div>
      </section>
    </main>
  );
}
