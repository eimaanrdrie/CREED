"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  CircleAlert,
  FileCheck2,
  Fingerprint,
  GitBranch,
  History,
  Network,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  UserRoundCheck,
  X,
} from "lucide-react";
import { AppShell } from "./app-shell";
import { KnowledgeSourcePreview } from "./knowledge-workspace";
import {
  getDocument,
  getDocuments,
  getHealth,
  getHumanAuthorities,
  getIssue,
  getIssues,
  getMethodVersions,
  getRecalls,
  revokeMethodVersion,
  type EvidenceDocument,
  type EvidenceDocumentDetail,
  type HealthResponse,
  type HumanAuthorityRecord,
  type MethodVersionRecord,
  type RecallRecord,
  type SupportIssue,
  type SupportIssueDetail,
} from "@/lib/api";

type RecallView = "active" | "revoked" | "history";
type RecallEvidenceMode = "issue" | "repository";

function fmtDate(value?: string) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-MY", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

function shortHash(hash?: string) {
  if (!hash) return "—";
  return `${hash.slice(0, 12)}…${hash.slice(-8)}`;
}

export function RecallsWorkspace() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [rows, setRows] = useState<RecallRecord[]>([]);
  const [versions, setVersions] = useState<MethodVersionRecord[]>([]);
  const [issues, setIssues] = useState<SupportIssue[]>([]);
  const [documents, setDocuments] = useState<EvidenceDocument[]>([]);
  const [authorities, setAuthorities] = useState<HumanAuthorityRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<RecallView>("active");
  const [showRecall, setShowRecall] = useState(false);
  const [versionId, setVersionId] = useState("");
  const [issueId, setIssueId] = useState("");
  const [issueDetail, setIssueDetail] = useState<SupportIssueDetail | null>(null);
  const [evidenceMode, setEvidenceMode] = useState<RecallEvidenceMode>("repository");
  const [selectedEvidenceIds, setSelectedEvidenceIds] = useState<string[]>([]);
  const [previewDetail, setPreviewDetail] = useState<EvidenceDocumentDetail | null>(null);
  const [previewBusyId, setPreviewBusyId] = useState<string | null>(null);
  const [reviewer, setReviewer] = useState("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<RecallRecord | null>(null);

  const reload = async () => {
    setLoading(true);
    try {
      const [h, r, v, i, d, a] = await Promise.all([getHealth(), getRecalls(), getMethodVersions(), getIssues(), getDocuments(), getHumanAuthorities()]);
      setHealth(h);
      setRows(r);
      setVersions(v);
      setIssues(i);
      setDocuments(d);
      setAuthorities(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : "RECALL_WORKSPACE_LOAD_FAILED");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void reload(); }, []);

  const approvedVersions = useMemo(() => versions.filter((item) => item.status === "APPROVED"), [versions]);
  const revokedVersions = useMemo(() => versions.filter((item) => item.status === "REVOKED"), [versions]);
  const recallAuthorities = useMemo(() => authorities.filter((item) => item.active && item.can_authorize_recall), [authorities]);
  const activeRows = useMemo(() => rows.filter((row) => row.status === "ACTIVE"), [rows]);

  useEffect(() => {
    if (reviewer && recallAuthorities.some((item) => item.principal === reviewer)) return;
    setReviewer(recallAuthorities[0]?.principal ?? "");
  }, [recallAuthorities, reviewer]);

  useEffect(() => {
    let cancelled = false;
    setIssueDetail(null);
    if (!issueId) return;
    void getIssue(issueId).then((detail) => { if (!cancelled) setIssueDetail(detail); }).catch(() => { if (!cancelled) setIssueDetail(null); });
    return () => { cancelled = true; };
  }, [issueId]);

  const selectedVersion = approvedVersions.find((item) => item.id === versionId);
  const selectedIssue = issues.find((item) => item.id === issueId);
  const issueEvidenceIds = issueDetail?.attachments.map((item) => item.document_id) ?? [];
  const activeEvidenceIds = evidenceMode === "issue" ? issueEvidenceIds : selectedEvidenceIds;
  const selectedPolicyReady = !selectedVersion?.adoption_policy?.enforced || selectedVersion.adoption_policy.reason === "READY";
  const canSubmit = Boolean(versionId && issueId && activeEvidenceIds.length > 0 && reviewer.trim().length >= 2 && reason.trim().length >= 3 && selectedPolicyReady && !submitting);

  const toggleEvidence = (documentId: string) => {
    setSelectedEvidenceIds((current) => current.includes(documentId) ? current.filter((id) => id !== documentId) : [...current, documentId]);
  };

  const openEvidencePreview = async (documentId: string) => {
    setPreviewBusyId(documentId);
    setError(null);
    try {
      setPreviewDetail(await getDocument(documentId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "SOURCE_PREVIEW_FAILED");
    } finally {
      setPreviewBusyId(null);
    }
  };

  const versionLabel = (versionIdToResolve: string) => {
    const version = versions.find((item) => item.id === versionIdToResolve);
    return version ? { method: version.method_name ?? "Delivery method", version: version.version } : { method: "Approved knowledge", version: versionIdToResolve };
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      // Backend endpoint retains the domain operation name for compatibility; the user-facing action is Recall.
      const result = await revokeMethodVersion(versionId, { source_issue_id: issueId, evidence_document_ids: activeEvidenceIds, reviewer: reviewer.trim(), reason: reason.trim() }, reviewer.trim());
      setCreated(result);
      setShowRecall(false);
      setVersionId("");
      setIssueId("");
      setIssueDetail(null);
      setEvidenceMode("repository");
      setSelectedEvidenceIds([]);
      setReason("");
      setView("active");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "RECALL_AUTHORIZATION_FAILED");
    } finally {
      setSubmitting(false);
    }
  };

  const recallRows = view === "active" ? activeRows : rows;

  return (
    <AppShell health={health} active="Knowledge Recall">
      <div className="page knowledge-recall-page-r99-m02">
        <header className="knowledge-recall-hero-r99-m02">
          <div>
            <h1>Knowledge Recall</h1>
            <p>Withdraw approved knowledge through Human Authority and route only governed adopters for review.</p>
          </div>
          <button className="primary-btn" type="button" onClick={() => { setShowRecall(true); setCreated(null); setError(null); }} disabled={approvedVersions.length === 0}>
            <RotateCcw size={16} /> Start recall
          </button>
        </header>

        <nav className="knowledge-recall-tabs-r99-m02" aria-label="Knowledge Recall views">
          <button type="button" className={view === "active" ? "active" : ""} onClick={() => setView("active")}>Active recalls <span>{activeRows.length}</span></button>
          <button type="button" className={view === "revoked" ? "active" : ""} onClick={() => setView("revoked")}>Revoked knowledge <span>{revokedVersions.length}</span></button>
          <button type="button" className={view === "history" ? "active" : ""} onClick={() => setView("history")}>History <span>{rows.length}</span></button>
        </nav>

        {created && (
          <section className="knowledge-recall-success-r99-m02" aria-live="polite">
            <CheckCircle2 size={17} />
            <div><strong>Recall authorized</strong><span>{created.cases.length} in-scope adopter{created.cases.length === 1 ? "" : "s"} routed · resulting knowledge status: REVOKED</span></div>
            <a href={`/recalls/${encodeURIComponent(created.id)}`}>Open Signed Recall Notice <ArrowRight size={14} /></a>
          </section>
        )}

        {error && <div className="recall-error-r07" role="alert"><CircleAlert size={14} /><span>{error.replaceAll("_", " ")}</span></div>}

        {view === "revoked" ? (
          <section className="knowledge-recall-list-r99-m02" aria-label="Revoked knowledge">
            {loading ? <div className="knowledge-recall-empty-r99-m02"><History size={18}/><span>Loading knowledge status…</span></div> : revokedVersions.length === 0 ? (
              <div className="knowledge-recall-empty-r99-m02"><ShieldCheck size={22}/><strong>No revoked knowledge</strong><p>No approved knowledge has reached the REVOKED outcome.</p></div>
            ) : revokedVersions.map((version, index) => {
              const notice = rows.find((row) => row.revoked_version_id === version.id);
              return (
                <details className="knowledge-recall-row-r99-m02" key={version.id}>
                  <summary>
                    <span className="knowledge-recall-index-r99-m02">{String(index + 1).padStart(2, "0")}</span>
                    <span className="knowledge-recall-copy-r99-m02"><strong>{version.method_name ?? "Delivery method"}</strong><small>{version.version}</small></span>
                    <span className="knowledge-recall-status-r99-m02 revoked">REVOKED</span>
                    <ChevronDown size={15}/>
                  </summary>
                  <div className="knowledge-recall-detail-r99-m02">
                    {notice ? <>
                      <p>{notice.reason}</p>
                      <div className="knowledge-recall-facts-r99-m02">
                        <div><span>Recall Authority</span><strong>{notice.approved_by}</strong></div>
                        <div><span>Authorized</span><strong>{fmtDate(notice.created_at)}</strong></div>
                        <div><span>Routed adopters</span><strong>{notice.cases.length}</strong></div>
                        <div><span>Integrity</span><strong>{notice.integrity}</strong></div>
                      </div>
                      <a className="knowledge-recall-notice-link-r99-m02" href={`/recalls/${encodeURIComponent(notice.id)}`}><FileCheck2 size={14}/> Signed Recall Notice</a>
                    </> : <p>The method version is registered as REVOKED. No recall notice was returned in the current workspace response.</p>}
                  </div>
                </details>
              );
            })}
          </section>
        ) : (
          <section className="knowledge-recall-list-r99-m02" aria-label={view === "active" ? "Active recalls" : "Recall history"}>
            {loading ? <div className="knowledge-recall-empty-r99-m02"><History size={18}/><span>Loading recall records…</span></div> : recallRows.length === 0 ? (
              <div className="knowledge-recall-empty-r99-m02"><History size={22}/><strong>{view === "active" ? "No active recalls" : "No recall history"}</strong><p>{view === "active" ? "No approved knowledge currently has an active recall." : "No Signed Recall Notice has been created."}</p></div>
            ) : recallRows.map((row, index) => {
              const resolved = versionLabel(row.revoked_version_id);
              return (
                <details className="knowledge-recall-row-r99-m02" key={row.id}>
                  <summary>
                    <span className="knowledge-recall-index-r99-m02">{String(index + 1).padStart(2, "0")}</span>
                    <span className="knowledge-recall-copy-r99-m02"><strong>{resolved.method}</strong><small>{resolved.version} · {row.id}</small></span>
                    <span className={`knowledge-recall-status-r99-m02 ${row.integrity === "VALID" ? "valid" : "invalid"}`}>{row.status}</span>
                    <span className="knowledge-recall-routed-r99-m02"><Network size={13}/>{row.cases.length} routed</span>
                    <ChevronDown size={15}/>
                  </summary>
                  <div className="knowledge-recall-detail-r99-m02">
                    <p>{row.reason}</p>
                    <div className="knowledge-recall-facts-r99-m02">
                      <div><span>Recall Authority</span><strong>{row.approved_by}</strong></div>
                      <div><span>Authorized</span><strong>{fmtDate(row.created_at)}</strong></div>
                      <div><span>Source issue</span><strong>{row.source_issue_id}</strong></div>
                      <div><span>Integrity</span><strong>{row.integrity}</strong></div>
                    </div>
                    <details className="knowledge-recall-proof-r99-m02">
                      <summary><span><Fingerprint size={14}/> Proof & routing</span><ChevronDown size={14}/></summary>
                      <div className="knowledge-recall-proof-body-r99-m02">
                        <span>Recall scope <strong>{row.routing_scope.enforced ? (row.routing_scope.mode ?? "SIGNED SCOPE") : "EXPLICIT A-BOM"}</strong></span>
                        <span>Excluded edges <strong>{row.routing_scope.blocked_count}</strong></span>
                        <span>Evidence <strong>{row.evidence.length}</strong></span>
                        <span>SHA-256 <code>{shortHash(row.content_hash)}</code></span>
                      </div>
                    </details>
                    <a className="knowledge-recall-notice-link-r99-m02" href={`/recalls/${encodeURIComponent(row.id)}`}><FileCheck2 size={14}/> Signed Recall Notice</a>
                  </div>
                </details>
              );
            })}
          </section>
        )}

        <details className="knowledge-recall-rules-r99-m02">
          <summary>Governance rules <ChevronDown size={14}/></summary>
          <div>
            <p><UserRoundCheck size={15}/><span><strong>Recall is the governed action.</strong> Only an active Recall Authority can authorize it; Qwen cannot perform this action.</span></p>
            <p><GitBranch size={15}/><span><strong>REVOKED is the resulting knowledge status.</strong> It is not presented as a separate user action.</span></p>
            <p><Network size={15}/><span><strong>Only governed explicit adopters are routed.</strong> Signed adoption scope is enforced before review obligations are created.</span></p>
          </div>
        </details>

        {showRecall && (
          <div className="recall-drawer-backdrop-r07" role="presentation" onMouseDown={(event) => { if (event.currentTarget === event.target && !submitting) setShowRecall(false); }}>
            <section className="recall-drawer-r28" role="dialog" aria-modal="true" aria-labelledby="recall-title-r99-m02">
              <div className="recall-drawer-head-r28">
                <div><span>HUMAN AUTHORITY</span><h2 id="recall-title-r99-m02">Start knowledge recall</h2></div>
                <button type="button" onClick={() => setShowRecall(false)} disabled={submitting} aria-label="Close recall form"><X size={18}/></button>
              </div>

              <div className="revoke-flow-r28" aria-label="Recall workflow">
                <span><RotateCcw size={15}/> Recall</span><ArrowRight size={13}/><span><Network size={15}/> Route</span><ArrowRight size={13}/><span><UserRoundCheck size={15}/> Review</span>
              </div>

              <div className="recall-warning-r28"><AlertTriangle size={17}/><span>Authorization creates a Signed Recall Notice, changes the selected approved knowledge to REVOKED, and routes only in-scope explicit adopters for review. Out-of-scope legacy edges are recorded but do not become review obligations.</span></div>

              <form className="recall-form-r28" onSubmit={submit}>
                <label><span>Approved knowledge</span><select value={versionId} onChange={(e) => setVersionId(e.target.value)} required><option value="">Select approved knowledge…</option>{approvedVersions.map((item) => <option value={item.id} key={item.id}>{item.method_name ?? "Delivery method"} · {item.version}</option>)}</select></label>
                {selectedVersion && <div className="recall-selection-r28"><GitBranch size={15}/><div><strong>{selectedVersion.method_name ?? "Delivery method"}</strong><span>{selectedVersion.version} · {selectedVersion.status}</span></div></div>}
                {selectedVersion?.adoption_policy?.enforced && (
                  <div className="recall-selection-r28"><ShieldCheck size={15}/><div><strong>Signed adoption boundary</strong><span>{selectedVersion.adoption_policy.scope_mode ?? "Unavailable"} · receipt {selectedVersion.adoption_policy.receipt_integrity ?? "UNKNOWN"}</span>{selectedVersion.adoption_policy.reason !== "READY" && <small>{selectedVersion.adoption_policy.reason.replaceAll("_", " ")}</small>}</div></div>
                )}

                <label><span>Source issue</span><select value={issueId} onChange={(e) => { setIssueId(e.target.value); setSelectedEvidenceIds([]); }} required><option value="">Select source issue…</option>{issues.map((item) => <option value={item.id} key={item.id}>{item.external_ticket_id ?? item.id} · {item.title}</option>)}</select></label>
                {selectedIssue && <div className="recall-selection-r28"><FileCheck2 size={15}/><div><strong>{selectedIssue.title}</strong><span>{selectedIssue.client_name ?? "Unknown client"} · recall context</span></div></div>}

                <fieldset className="recall-evidence-source-r99-m04">
                  <legend>Source evidence</legend>
                  <div className="recall-evidence-modes-r99-m04" role="tablist" aria-label="Recall evidence source">
                    <button type="button" role="tab" aria-selected={evidenceMode === "issue"} className={evidenceMode === "issue" ? "active" : ""} onClick={() => setEvidenceMode("issue")}>Issue evidence <span>{issueEvidenceIds.length}</span></button>
                    <button type="button" role="tab" aria-selected={evidenceMode === "repository"} className={evidenceMode === "repository" ? "active" : ""} onClick={() => setEvidenceMode("repository")}>Evidence Repository <span>{documents.length}</span></button>
                  </div>

                  {evidenceMode === "issue" ? (
                    !issueId ? <p className="recall-evidence-empty-r99-m04">Select a source issue first.</p> : issueDetail === null ? <p className="recall-evidence-empty-r99-m04">Loading issue evidence…</p> : issueDetail.attachments.length === 0 ? <p className="recall-evidence-empty-r99-m04">This issue has no directly linked evidence. Use Evidence Repository instead.</p> : <div className="recall-evidence-list-r99-m04">{issueDetail.attachments.map((item) => <div className="recall-evidence-row-r99-m04 selected" key={item.document_id}><div><strong>{item.title}</strong><span>{item.document_type} · linked to source issue</span></div><button type="button" onClick={() => void openEvidencePreview(item.document_id)} disabled={previewBusyId === item.document_id}>{previewBusyId === item.document_id ? "Loading…" : "Preview source"}</button></div>)}</div>
                  ) : (
                    documents.length === 0 ? <p className="recall-evidence-empty-r99-m04">No governed evidence documents are available.</p> : <div className="recall-evidence-list-r99-m04">{documents.map((item) => { const checked = selectedEvidenceIds.includes(item.id); return <div className={`recall-evidence-row-r99-m04 ${checked ? "selected" : ""}`} key={item.id}><label><input type="checkbox" checked={checked} onChange={() => toggleEvidence(item.id)} /><div><strong>{item.title}</strong><span>{item.document_type}{item.version ? ` · v${item.version}` : ""} · {item.index_status}</span></div></label><button type="button" onClick={() => void openEvidencePreview(item.id)} disabled={previewBusyId === item.id}>{previewBusyId === item.id ? "Loading…" : "Preview source"}</button></div>})}</div>
                  )}
                  <small className="recall-evidence-count-r99-m04">{activeEvidenceIds.length} evidence document{activeEvidenceIds.length === 1 ? "" : "s"} will be sealed into the Signed Recall Notice.</small>
                </fieldset>

                <label className="recall-authority-field-r85"><span>Recall Authority</span>{recallAuthorities.length ? <select value={reviewer} onChange={(e) => setReviewer(e.target.value)} required><option value="">Select Recall Authority…</option>{recallAuthorities.map((item) => <option value={item.principal} key={item.id}>{item.display_name} · {item.principal}</option>)}</select> : <div className="recall-authority-empty-r85"><AlertTriangle size={14}/><span>No active Recall Authority. <a href="/authority">Configure authority</a>.</span></div>}</label>
                <label><span>Recall reason</span><textarea value={reason} onChange={(e) => setReason(e.target.value)} required minLength={3} placeholder="Why should this approved knowledge be recalled?"/></label>

                <div className="recall-human-boundary-r28"><UserRoundCheck size={16}/><span><strong>Enforced human attestation.</strong> CREED verifies the selected principal is active and has Recall Authority before the recall can be authorized.</span></div>
                <div className="recall-form-actions-r07"><button type="button" className="ghost-btn" onClick={() => setShowRecall(false)} disabled={submitting}>Cancel</button><button type="submit" className="danger-governed-btn-r07" disabled={!canSubmit}>{submitting ? <RotateCcw size={15} className="spin"/> : <ShieldAlert size={15}/>} {submitting ? "Authorizing…" : "Authorize recall"}</button></div>
              </form>
            </section>
          </div>
        )}
      </div>
      {previewDetail && <KnowledgeSourcePreview detail={previewDetail} onClose={() => setPreviewDetail(null)} />}
    </AppShell>
  );
}
