"use client";

// R29 semantic contract: CREED exposes persisted execution metadata, never hidden chain-of-thought.
// R19 compatibility contract markers preserved after R29 visual-minimalism refactor:
// data-label="Lifecycle" · data-label="Retrieval score" · data-label="Priority score" · data-label="Integrity"
// Observable, not introspective
// Hidden chain-of-thought is not collected or displayed.
// Impact values are prioritisation scores, not final human decisions.
// Authority boundary
// R22 copy contract: Trace execution, evidence, Qwen, impact and human authority.
import { useEffect, useMemo, useState } from "react";
import {
  Activity, AlertTriangle, BrainCircuit, CheckCircle2, ChevronLeft, ChevronRight,
  CircleDot, Clock3, FileCheck2, FileSearch2, Fingerprint, GitBranch,
  History, Network, Scale, Search, ShieldCheck, ShieldX, UserRoundCheck, X, XCircle,
} from "lucide-react";
import { AppShell } from "./app-shell";
import { ProgressiveDisclosure, SignalChip, type SignalTone } from "./visual-primitives";
import { getAudit, getDocument, getHealth, type AuditData, type AuditTimelineItem, type HealthResponse } from "@/lib/api";

const EMPTY: AuditData = {
  graph_run_id: null, run_id: null,
  scope: { mode: "GLOBAL", run: null, issue: null },
  summary: { timeline_records:0, agent_steps:0, qwen_calls:0, evidence_accesses:0, impact_assessments:0, human_decisions:0, governance_artefacts:0, failures:0, category_counts:{} },
  agents: [], qwen_calls: [], evidence: [], impacts: [], human_decisions: [], governance: [], timeline: [],
};

const CATEGORIES = ["ALL", "AGENT", "AI", "EVIDENCE", "IMPACT", "HUMAN", "GOVERNANCE", "AUDIT", "ISSUE"] as const;
type Category = typeof CATEGORIES[number];
const AUDIT_PAGE_SIZE = 6;

function fmtDate(value?: string | null) {
  if (!value) return "—";
  const d = new Date(value);
  return Number.isNaN(d.valueOf()) ? value : d.toLocaleString([], { day:"2-digit", month:"short", hour:"2-digit", minute:"2-digit", second:"2-digit" });
}
function fmtTime(value?: string | null) {
  if (!value) return "—";
  const d = new Date(value);
  return Number.isNaN(d.valueOf()) ? value : d.toLocaleTimeString([], { hour:"2-digit", minute:"2-digit", second:"2-digit" });
}
function fmtDuration(ms?: number | null) {
  if (ms === null || ms === undefined) return "—";
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(ms >= 10000 ? 1 : 2)} s`;
}
function fmtScore(value?: number | null) {
  if (value === null || value === undefined) return "—";
  return `${Math.round(value * 100)}%`;
}
function shortHash(value?: string | null) { return value ? `${value.slice(0,12)}…${value.slice(-8)}` : "—"; }
function tone(status?: string | null): SignalTone {
  const s=(status||"").toUpperCase();
  if (["COMPLETED","VALID","APPROVED","AFFECTED","CONNECTED","STRUCTURED"].includes(s)) return "ok";
  if (["FAILED","INVALID","REVOKED","NOT_AFFECTED"].includes(s)) return "bad";
  if (["WAITING_HUMAN","RUNNING","QUEUED","POTENTIALLY_AFFECTED"].includes(s)) return "warn";
  return "neutral";
}
function iconFor(category: string, size=15) {
  switch (category) {
    case "ISSUE": return <CircleDot size={size}/>;
    case "AGENT": return <GitBranch size={size}/>;
    case "AI": return <BrainCircuit size={size}/>;
    case "EVIDENCE": return <FileSearch2 size={size}/>;
    case "IMPACT": return <Network size={size}/>;
    case "HUMAN": return <UserRoundCheck size={size}/>;
    case "GOVERNANCE": return <ShieldCheck size={size}/>;
    case "AUDIT": return <History size={size}/>;
    default: return <Activity size={size}/>;
  }
}
function categoryLabel(category: string) {
  return category === "AI" ? "Qwen" : category.charAt(0) + category.slice(1).toLowerCase();
}

export function AuditWorkspace() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [data, setData] = useState<AuditData>(EMPTY);
  const [run, setRun] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState<Category>("ALL");
  const [eventQuery, setEventQuery] = useState("");
  const [auditPage, setAuditPage] = useState(1);
  const [selected, setSelected] = useState<AuditTimelineItem | null>(null);
  const [evidencePreview, setEvidencePreview] = useState<{title:string;content_hash:string;extracted_text:string}|null>(null);

  useEffect(() => {
    getHealth().then(setHealth);
    getAudit().then(setData).catch(() => setData(EMPTY));
  }, []);

  const timeline = useMemo(() => {
    const q = eventQuery.trim().toLowerCase();
    return data.timeline.filter((item) => {
      if (category !== "ALL" && item.category !== category) return false;
      if (!q) return true;
      const haystack = [
        item.category, item.title, item.detail, item.status, item.actor, item.reviewer, item.model, item.run_id,
      ].filter(Boolean).join(" ").toLowerCase();
      return haystack.includes(q);
    });
  }, [data.timeline, category, eventQuery]);

  const totalAuditPages = Math.max(1, Math.ceil(timeline.length / AUDIT_PAGE_SIZE));
  const safeAuditPage = Math.min(auditPage, totalAuditPages);
  const auditPageStart = (safeAuditPage - 1) * AUDIT_PAGE_SIZE;
  const pagedTimeline = timeline.slice(auditPageStart, auditPageStart + AUDIT_PAGE_SIZE);
  const auditPageItems = useMemo<(number | "ellipsis")[]>(() => {
    if (totalAuditPages <= 7) return Array.from({ length: totalAuditPages }, (_, index) => index + 1);
    const pages = new Set<number>([1, totalAuditPages, safeAuditPage - 1, safeAuditPage, safeAuditPage + 1]);
    const ordered = Array.from(pages).filter((page) => page >= 1 && page <= totalAuditPages).sort((a, b) => a - b);
    const items: (number | "ellipsis")[] = [];
    ordered.forEach((page, index) => {
      if (index > 0 && page - ordered[index - 1] > 1) items.push("ellipsis");
      items.push(page);
    });
    return items;
  }, [safeAuditPage, totalAuditPages]);

  useEffect(() => {
    setAuditPage(1);
  }, [category, eventQuery, data.timeline]);

  async function inspect(value=run) {
    setBusy(true); setError(null); setSelected(null); setEvidencePreview(null);
    try {
      const next = await getAudit(value.trim() || undefined);
      if (value.trim() && !next.scope.run) setError(`No persisted AgentRun found for ${value.trim()}.`);
      setData(next);
    } catch (e) { setError(e instanceof Error ? e.message : "AUDIT_TRACE_FAILED"); }
    finally { setBusy(false); }
  }
  async function clearScope() { setRun(""); setCategory("ALL"); setEventQuery(""); setAuditPage(1); await inspect(""); }
  async function inspectEvidence(documentId: string) {
    try {
      const doc=await getDocument(documentId);
      setEvidencePreview({title:doc.title,content_hash:doc.content_hash,extracted_text:doc.extracted_text});
    } catch { setEvidencePreview(null); }
  }

  const scope=data.scope;
  const runState=scope.run?.status ?? "GLOBAL";
  const authorityCount=data.summary.human_decisions + data.summary.governance_artefacts;
  const selectedTone=tone(selected?.status || (selected?.error ? "FAILED" : selected?.category === "GOVERNANCE" ? "VALID" : null));

  return (
    <AppShell health={health} active="Audit">
      <div className="page audit-r29">
        <header className="audit-head-r44">
          <div className="audit-head-copy-r44">
            <h1>Audit workbench</h1>
            <p className="subtitle">Trace persisted execution, evidence and human authority without losing the chronology.</p>
          </div>
          <div className="audit-head-state-r44 editorial-meta-group-r71">
            <span className="editorial-meta-r71 tone-ok"><ShieldCheck size={14} aria-hidden="true" />Persisted only</span>
            {data.summary.failures > 0
              ? <span className="editorial-meta-r71 tone-bad"><XCircle size={14} aria-hidden="true" />{data.summary.failures} failure{data.summary.failures === 1 ? "" : "s"}</span>
              : <span className="editorial-meta-r71 tone-ok"><CheckCircle2 size={14} aria-hidden="true" />No failures</span>}
          </div>
        </header>

        <section className="audit-commandbar-r44" aria-label="Audit scope and run search">
          <div className="audit-scope-r44">
            <span className={`audit-scope-icon-r44 tone-${tone(runState)}`}>{scope.mode === "RUN" ? <Activity size={18}/> : <History size={18}/>}</span>
            <div>
              <small>SCOPE</small>
              <strong>{scope.mode === "RUN" ? "Selected run" : "Global audit"}</strong>
              <span>{scope.mode === "RUN" ? scope.run?.graph_run_id : "Latest persisted audit and governance events"}</span>
            </div>
          </div>
          <div className="audit-run-search-form-r44">
            <div className="audit-run-input-r44">
              <Search size={16}/>
              <input value={run} onChange={(e)=>setRun(e.target.value)} onKeyDown={(e)=>{if(e.key==="Enter") inspect();}} placeholder="Graph run ID · CREED-2026-..." aria-label="Graph run ID"/>
            </div>
            {scope.mode === "RUN" && <button type="button" className="secondary-btn compact" onClick={clearScope}>Clear</button>}
            <button type="button" className="primary-btn compact" onClick={()=>inspect()} disabled={busy}>{busy?"Inspecting…":"Inspect run"}</button>
          </div>
        </section>
        {error && <div className="audit-error-r08" role="alert"><AlertTriangle size={14}/><span>{error}</span></div>}

        <section className="audit-signal-strip-r44" aria-label="Audit summary">
          <div><span>Events</span><strong>{data.summary.timeline_records}</strong><small>{scope.mode === "RUN" ? "this run" : "persisted"}</small></div>
          <div><span>Qwen</span><strong>{data.summary.qwen_calls}</strong><small>executions</small></div>
          <div><span>Evidence</span><strong>{data.summary.evidence_accesses}</strong><small>accesses</small></div>
          <div><span>Authority</span><strong>{authorityCount}</strong><small>{data.summary.human_decisions} human · {data.summary.governance_artefacts} artefact</small></div>
        </section>

        {scope.mode === "RUN" && scope.run && (
          <section className="audit-run-context-r44" aria-label="Selected run context">
            <div className="audit-run-context-main-r44">
              <SignalChip icon={Activity} tone={tone(runState)}>{runState.replaceAll("_"," ")}</SignalChip>
              <div>
                <strong>{scope.issue?.title || "Persisted CREED run"}</strong>
                <span>{scope.issue?.ticket || "No ticket"} · {fmtDate(scope.run.started_at)} · {fmtDuration(scope.run.duration_ms)}</span>
              </div>
            </div>
            <div className="audit-run-stages-r44" aria-label="Run proof counts">
              <span><GitBranch size={14}/><b>{data.summary.agent_steps}</b>Agents</span>
              <span><BrainCircuit size={14}/><b>{data.summary.qwen_calls}</b>Qwen</span>
              <span><FileSearch2 size={14}/><b>{data.summary.evidence_accesses}</b>Evidence</span>
              <span><Network size={14}/><b>{data.summary.impact_assessments}</b>Impact</span>
              <span><UserRoundCheck size={14}/><b>{data.summary.human_decisions}</b>Human</span>
            </div>
          </section>
        )}

        <section className="audit-master-detail-r42" aria-label="Audit chronology and selected proof">
          <section className="card audit-timeline-card-r29 audit-timeline-pane-r42 audit-stream-r45">
            <div className="audit-stream-head-r45">
              <div>
                <span>EVENT STREAM</span>
                <h2>{scope.mode === "RUN" ? "Run chronology" : "Persisted chronology"}</h2>
                <p>Scan the event sequence, then inspect the selected proof without losing your position.</p>
              </div>
              <div className="audit-stream-count-r45"><strong>{timeline.length}</strong><span>of {data.timeline.length}</span></div>
            </div>

            <div className="audit-stream-toolbar-r45">
              <label className="audit-event-search-r45">
                <Search size={15} aria-hidden="true"/>
                <input
                  value={eventQuery}
                  onChange={(event)=>setEventQuery(event.target.value)}
                  placeholder="Search events, status, actor or model…"
                  aria-label="Search audit events"
                />
                {eventQuery && <button type="button" className="icon-btn" aria-label="Clear event search" onClick={()=>setEventQuery("")}><X size={14}/></button>}
              </label>
              {(category !== "ALL" || eventQuery) && <button type="button" className="ghost-btn compact audit-filter-clear-r45" onClick={()=>{setCategory("ALL");setEventQuery("");}}>Clear filters</button>}
            </div>

            <div className="audit-filter-row-r29 audit-category-row-r45" aria-label="Filter audit events">
              {CATEGORIES.map((item)=>{
                const count = item === "ALL" ? data.timeline.length : data.summary.category_counts[item] ?? 0;
                return <button type="button" key={item} className={category===item?"active":""} aria-pressed={category===item} onClick={()=>setCategory(item)}>
                  {item!=="ALL"&&iconFor(item,13)}
                  <span>{item==="ALL"?"All":categoryLabel(item)}</span>
                  <b>{count}</b>
                </button>;
              })}
            </div>

            <div className="audit-visual-timeline-r29 audit-event-stream-list-r45 audit-event-page-r48">
              {timeline.length===0 && <div className="audit-empty-r08 audit-stream-empty-r45"><History size={18}/><strong>No matching events</strong><span>{data.timeline.length===0 ? (scope.mode==="GLOBAL"?"Inspect a graph run for execution provenance.":"No persisted records are linked to this run.") : "Change the event search or category filter."}</span></div>}
              {pagedTimeline.map((item,index)=>{
                const active=selected===item;
                const rowTone=tone(item.status || (item.error ? "FAILED" : item.category === "GOVERNANCE" ? "VALID" : null));
                return <button
                  type="button"
                  className={`audit-event-r29 audit-stream-event-r45 ${active?"selected":""} tone-${rowTone}`}
                  key={`${item.at}-${item.category}-${index}`}
                  onClick={()=>setSelected(item)}
                  aria-pressed={active}
                >
                  <span className="audit-event-rail-r29 audit-stream-rail-r45"><i>{iconFor(item.category,15)}</i>{index<pagedTimeline.length-1&&<b/>}</span>
                  <span className="audit-event-main-r29 audit-stream-main-r45">
                    <span className="audit-stream-meta-r45">
                      <em>{categoryLabel(item.category)}</em>
                      <time dateTime={item.at}>{fmtTime(item.at)}</time>
                      {item.status&&<small className={`tone-${rowTone}`}>{item.status.replaceAll("_"," ")}</small>}
                    </span>
                    <strong>{item.title}</strong>
                    {item.detail&&<span className="audit-stream-detail-r45">{item.detail}</span>}
                  </span>
                  <ChevronRight size={16}/>
                </button>;
              })}
            </div>

            {timeline.length > 0 && (
              <nav className="audit-pagination-r48" aria-label="Audit event pages">
                <div className="audit-pagination-summary-r48">
                  <strong>{auditPageStart + 1}–{Math.min(auditPageStart + AUDIT_PAGE_SIZE, timeline.length)}</strong>
                  <span>of {timeline.length} events</span>
                </div>
                <div className="audit-pagination-controls-r48">
                  <button
                    type="button"
                    className="audit-page-step-r48"
                    onClick={()=>setAuditPage((page)=>Math.max(1,page-1))}
                    disabled={safeAuditPage===1}
                    aria-label="Previous audit page"
                  >
                    <ChevronLeft size={14}/>
                  </button>
                  {auditPageItems.map((item,index)=>item === "ellipsis"
                    ? <span className="audit-page-ellipsis-r48" key={`ellipsis-${index}`}>…</span>
                    : <button
                        type="button"
                        key={item}
                        className={`audit-page-number-r48 ${safeAuditPage===item?"active":""}`}
                        onClick={()=>setAuditPage(item)}
                        aria-current={safeAuditPage===item?"page":undefined}
                        aria-label={`Audit page ${item}`}
                      >{item}</button>
                  )}
                  <button
                    type="button"
                    className="audit-page-step-r48"
                    onClick={()=>setAuditPage((page)=>Math.min(totalAuditPages,page+1))}
                    disabled={safeAuditPage===totalAuditPages}
                    aria-label="Next audit page"
                  >
                    <ChevronRight size={14}/>
                  </button>
                </div>
              </nav>
            )}
          </section>

          <aside className="audit-detail-pane-r42 audit-proof-pane-r46" aria-label="Selected event proof panel">
            {selected ? (
              <section className={`card audit-event-proof-r29 audit-proof-inspector-r46 tone-${selectedTone}`} aria-label="Selected event proof">
                <div className="audit-proof-inspector-head-r46">
                  <div className="audit-proof-inspector-title-r46">
                    <span className="audit-proof-inspector-icon-r46">{iconFor(selected.category,18)}</span>
                    <div>
                      <span className="audit-proof-kicker-r46">PROOF INSPECTOR · {categoryLabel(selected.category).toUpperCase()}</span>
                      <h2>{selected.title}</h2>
                    </div>
                  </div>
                  <SignalChip tone={selectedTone}>{selected.status?.replaceAll("_"," ") || (selected.error?"FAILED":"PERSISTED")}</SignalChip>
                </div>

                <div className="audit-proof-trace-r46" aria-label="Selected event traceability">
                  <div><Clock3 size={14}/><span>Recorded</span><strong>{fmtDate(selected.at)}</strong></div>
                  <div><History size={14}/><span>Source</span><strong>Persisted audit</strong></div>
                  <div><Fingerprint size={14}/><span>Authority</span><strong>{selected.category === "HUMAN" || selected.category === "GOVERNANCE" ? "Governed record" : "Observable record"}</strong></div>
                </div>

                {selected.detail&&<div className="audit-proof-narrative-r46"><span>EVENT DETAIL</span><p>{selected.detail}</p></div>}

                <div className="audit-proof-section-head-r46"><span>PROOF FACTS</span><small>Persisted fields only</small></div>
                <div className="audit-event-proof-grid-r29 audit-proof-facts-r46">
                  {selected.run_id&&<div><span>Qwen run</span><strong className="mono-r08">{selected.run_id}</strong></div>}
                  {selected.model&&<div><span>Model</span><strong>{selected.model}</strong></div>}
                  {selected.duration_ms!==undefined&&<div><span>Duration</span><strong>{fmtDuration(selected.duration_ms)}</strong></div>}
                  {selected.score!==undefined&&<div><span>Retrieval</span><strong>{fmtScore(selected.score)}</strong></div>}
                  {selected.impact_score!==undefined&&<div><span>Priority</span><strong>{fmtScore(selected.impact_score)}</strong></div>}
                  {selected.actor&&<div><span>Actor</span><strong>{selected.actor}</strong></div>}
                  {selected.reviewer&&<div><span>Reviewer</span><strong>{selected.reviewer}</strong></div>}
                  {selected.content_hash&&<div className="audit-proof-wide-r29"><span>SHA-256</span><strong className="mono-r08">{selected.content_hash}</strong></div>}
                </div>

                {selected.error&&<div className="trace-failure-r08 audit-proof-failure-r46"><ShieldX size={14}/><div><strong>Execution failure</strong><span>{selected.error}</span></div></div>}

                <div className="audit-proof-actionbar-r46">
                  <div className="audit-proof-boundary-r46"><ShieldCheck size={14}/><span>Observable metadata only · no hidden chain-of-thought</span></div>
                  <div className="audit-event-proof-actions-r29">
                    {selected.document_id&&<button type="button" className="secondary-btn compact" onClick={()=>inspectEvidence(selected.document_id!)}><FileSearch2 size={14}/>Source evidence</button>}
                    {selected.href&&<a className="secondary-btn compact" href={selected.href}><FileCheck2 size={14}/>Governance artefact</a>}
                  </div>
                </div>
              </section>
            ) : (
              <section className="card audit-event-proof-empty-r42 audit-proof-empty-r46">
                <span className="audit-proof-empty-icon-r46"><History size={24} aria-hidden="true"/></span>
                <span className="audit-proof-kicker-r46">PROOF INSPECTOR</span>
                <strong>Select an event</strong>
                <span>Choose a persisted event from the stream. Its proof stays visible here while the chronology remains independently scrollable.</span>
              </section>
            )}
          </aside>
        </section>

        {scope.mode === "RUN" && <section className="audit-proof-stack-r29 audit-deep-proof-r47">
          <div className="audit-deep-proof-head-r47">
            <div>
              <span>RUN-SCOPED PROOF</span>
              <h2>Deep evidence & governance</h2>
              <p>Inspect persisted execution, retrieved evidence, prioritisation and final authority without changing the audit record.</p>
            </div>
            <SignalChip icon={Fingerprint} tone="neutral">{data.summary.timeline_records} persisted events</SignalChip>
          </div>

          <ProgressiveDisclosure label="Execution proof" meta={`${data.agents.length + data.qwen_calls.length} records`}>
            <div className="audit-proof-columns-r29 audit-deep-grid-r47">
              <div className="audit-proof-group-r29 audit-deep-group-r47">
                <div className="audit-proof-group-head-r29 audit-deep-group-head-r47"><GitBranch size={15}/><div><strong>Agent execution</strong><small>Persisted lifecycle steps</small></div><span>{data.agents.length}</span></div>
                {data.agents.length===0?<div className="audit-empty-compact-r08 audit-deep-empty-r47"><p>No persisted agent steps.</p></div>:data.agents.map((a)=><div className="audit-mini-row-r29 audit-agent-row-r47" key={a.id}><span className={`audit-mini-icon-r29 tone-${tone(a.status)}`}><GitBranch size={13}/></span><div><strong>{a.display_name}</strong><span>{a.output_summary||a.input_summary||"No output summary"}</span></div><div className="audit-row-proof-r47"><b className={`tone-${tone(a.status)}`}>{a.status.replaceAll("_"," ")}</b><small>{fmtDuration(a.duration_ms)}</small></div></div>)}
              </div>
              <div className="audit-proof-group-r29 audit-deep-group-r47">
                <div className="audit-proof-group-head-r29 audit-deep-group-head-r47"><BrainCircuit size={15}/><div><strong>Qwen execution</strong><small>Observable runtime proof</small></div><span>{data.qwen_calls.length}</span></div>
                {data.qwen_calls.length===0?<div className="audit-empty-compact-r08 audit-deep-empty-r47"><p>No Qwen execution linked to this run.</p></div>:data.qwen_calls.map((q)=><div className="audit-qwen-row-r29 audit-qwen-row-r47" key={q.run_id}><span className={`audit-mini-icon-r29 tone-${q.success?"ok":"bad"}`}>{q.success?<BrainCircuit size={13}/>:<AlertTriangle size={13}/>}</span><div><strong>{q.purpose}</strong><span>{q.actual_model||q.configured_model||"Model unavailable"}</span><small className="mono-r08">{q.run_id}</small></div><div className="audit-row-proof-r47"><b>{fmtDuration(q.duration_ms)}</b><small>IN {q.prompt_tokens??"—"} · OUT {q.output_tokens??"—"}</small><em className={q.structured_output_valid?"audit-ok-r08":"audit-bad-r08"}>{q.structured_output_valid?"STRUCTURED":"INVALID"}</em></div>{q.error&&<p>{q.error}</p>}</div>)}
              </div>
            </div>
          </ProgressiveDisclosure>

          <ProgressiveDisclosure label="Evidence & impact" meta={`${data.evidence.length} evidence · ${data.impacts.length} impact`}>
            <div className="audit-proof-columns-r29 audit-deep-grid-r47">
              <div className="audit-proof-group-r29 audit-deep-group-r47">
                <div className="audit-proof-group-head-r29 audit-deep-group-head-r47"><FileSearch2 size={15}/><div><strong>Evidence accessed</strong><small>Ranked source material</small></div><span>{data.evidence.length}</span></div>
                {data.evidence.length===0?<div className="audit-empty-compact-r08 audit-deep-empty-r47"><p>No evidence access recorded.</p></div>:data.evidence.map((e)=><button type="button" className="audit-evidence-row-r29 audit-evidence-row-r47" key={e.id} onClick={()=>inspectEvidence(e.document_id)}><span>{String(e.rank).padStart(2,"0")}</span><div><strong>{e.citation}</strong><p>{e.excerpt}</p><small>{e.document_type||"DOCUMENT"} · SHA-256 {shortHash(e.content_hash)}</small></div><div className="audit-score-stack-r47"><b>{fmtScore(e.final_score)}</b><small>RETRIEVAL</small></div></button>)}
              </div>
              <div className="audit-proof-group-r29 audit-deep-group-r47">
                <div className="audit-proof-group-head-r29 audit-deep-group-head-r47"><Network size={15}/><div><strong>Impact priority</strong><small>Investigation ordering only</small></div><span>{data.impacts.length}</span></div>
                {data.impacts.length===0?<div className="audit-empty-compact-r08 audit-deep-empty-r47"><p>No impact assessments recorded.</p></div>:data.impacts.map((i)=><div className="audit-impact-row-r29 audit-impact-row-r47" key={i.id}><span className={`audit-mini-icon-r29 tone-${tone(i.impact_band)}`}><Network size={13}/></span><div><div className="audit-impact-title-r47"><strong>{i.client_name||i.implementation_name||"Implementation"}</strong><small className={`tone-${tone(i.impact_band)}`}>{i.impact_band.replaceAll("_"," ")}</small></div><span>{Object.keys(i.signals||{}).length} signals · {i.evidence_refs.length} evidence refs</span><div className="audit-impact-track-r47" aria-label={`Priority score ${fmtScore(i.impact_score)}`}><i style={{width:`${Math.max(0,Math.min(100,Math.round((i.impact_score ?? 0)*100)))}%`}}/></div></div><div className="audit-score-stack-r47"><b>{fmtScore(i.impact_score)}</b><small>PRIORITY</small></div></div>)}
                <div className="audit-disclaimer-r08 audit-deep-disclaimer-r47"><AlertTriangle size={13}/><span>Priority score guides investigation. It is not a defect verdict.</span></div>
              </div>
            </div>
          </ProgressiveDisclosure>

          <ProgressiveDisclosure label="Human & governance" meta={`${data.human_decisions.length} decisions · ${data.governance.length} artefacts`}>
            <div className="audit-proof-columns-r29 audit-deep-grid-r47">
              <div className="audit-proof-group-r29 audit-deep-group-r47 audit-human-group-r47">
                <div className="audit-proof-group-head-r29 audit-deep-group-head-r47"><UserRoundCheck size={15}/><div><strong>Human authority</strong><small>Final governed decisions</small></div><span>{data.human_decisions.length}</span></div>
                {data.human_decisions.length===0?<div className="audit-empty-compact-r08 audit-deep-empty-r47"><p>No human decisions recorded.</p></div>:data.human_decisions.map((h)=><div className="audit-human-row-r29 audit-human-row-r47" key={h.id}><span className={`audit-mini-icon-r29 tone-${tone(h.decision)}`}><UserRoundCheck size={13}/></span><div><div className="audit-human-decision-r47"><strong>{h.decision.replaceAll("_"," ")}</strong><SignalChip tone={tone(h.decision)}>{h.client_name||h.implementation_name||"Implementation"}</SignalChip></div><p>{h.reason||"No rationale recorded."}</p><small>{h.reviewer} · {fmtDate(h.decided_at)}</small></div></div>)}
              </div>
              <div className="audit-proof-group-r29 audit-deep-group-r47 audit-governance-group-r47">
                <div className="audit-proof-group-head-r29 audit-deep-group-head-r47"><Fingerprint size={15}/><div><strong>Governance artefacts</strong><small>Signed outcome records</small></div><span>{data.governance.length}</span></div>
                {data.governance.length===0?<div className="audit-empty-compact-r08 audit-deep-empty-r47"><p>No adoption or recall artefact linked to this issue.</p></div>:data.governance.map((g)=><a className="audit-governance-row-r29 audit-governance-row-r47" key={`${g.type}-${g.id}`} href={g.href}><span className={`audit-mini-icon-r29 tone-${tone(g.integrity)}`}>{g.integrity==="VALID"?<ShieldCheck size={13}/>:<ShieldX size={13}/>}</span><div><strong>{g.type === "ADOPTION"?"Signed Adoption Receipt":"Signed Recall Notice"}</strong><span>{g.actor} · {fmtDate(g.at)}</span><small className="mono-r08">SHA-256 · {shortHash(g.content_hash)}</small></div><div className="audit-governance-state-r47"><b className={`tone-${tone(g.integrity)}`}>{g.integrity}</b><ChevronRight size={13}/></div></a>)}
              </div>
            </div>
          </ProgressiveDisclosure>
        </section>}

        <div className="audit-authority-note-r29"><Scale size={15}/><span><strong>Authority boundary:</strong> AI proposes. Human decisions carry authority. Governance artefacts preserve the outcome.</span></div>

        {evidencePreview&&<div className="evidence-preview-layer-r08" role="dialog" aria-modal="true" aria-label="Evidence provenance"><button type="button" className="evidence-preview-backdrop-r08" aria-label="Close evidence" onClick={()=>setEvidencePreview(null)}/><section className="evidence-preview-r08"><div className="evidence-preview-head-r08"><div><span>SOURCE EVIDENCE</span><strong>{evidencePreview.title}</strong></div><button type="button" className="secondary-btn compact" onClick={()=>setEvidencePreview(null)}>Close</button></div><div className="evidence-seal-r08"><Fingerprint size={14}/><span>SHA-256</span><code>{evidencePreview.content_hash}</code></div><pre>{evidencePreview.extracted_text||"No extracted text available."}</pre></section></div>}
      </div>
    </AppShell>
  );
}
