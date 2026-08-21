"use client";

import { useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  CircleAlert,
  Clipboard,
  FileCheck2,
  Fingerprint,
  GitBranch,
  History,
  Network,
  Printer,
  ShieldAlert,
  ShieldCheck,
  UserRoundCheck,
} from "lucide-react";
import { AppShell } from "./app-shell";
import { getHealth, getRecall, verifyRecall, type HealthResponse, type RecallRecord, type RecallVerification } from "@/lib/api";

function fmtDate(value?: string) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-MY", { day: "2-digit", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

function shortHash(value?: string) {
  if (!value) return "—";
  return `${value.slice(0, 14)}…${value.slice(-10)}`;
}

export function RecallNoticeWorkspace({ recallId }: { recallId: string }) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [notice, setNotice] = useState<RecallRecord | null>(null);
  const [verification, setVerification] = useState<RecallVerification | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    getHealth().then(setHealth);
    Promise.all([getRecall(recallId), verifyRecall(recallId)])
      .then(([n, v]) => { setNotice(n); setVerification(v); })
      .catch((err) => setError(err instanceof Error ? err.message : "RECALL_NOTICE_LOAD_FAILED"));
  }, [recallId]);

  const copyHash = async () => {
    if (!notice?.content_hash) return;
    await navigator.clipboard.writeText(notice.content_hash);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  return (
    <AppShell health={health} active="Knowledge Recall">
      <div className="page recall-notice-r28">
        <div className="recall-notice-nav-r28">
          <a href="/recalls"><ArrowLeft size={15} /> Knowledge Recall</a>
          <div><button type="button" onClick={() => window.print()}><Printer size={15} /> Print</button></div>
        </div>

        {error && <div className="recall-error-r07" role="alert"><CircleAlert size={14} /><span>{error.replaceAll("_", " ")}</span></div>}
        {!notice ? (
          <div className="recall-loading-r07" role="status" aria-live="polite"><History size={18} /><span>Loading Signed Recall Notice…</span></div>
        ) : (
          <>
            <header className="recall-notice-hero-r28">
              <div className="recall-notice-mark-r28"><ShieldAlert size={25} /></div>
              <div className="recall-notice-title-r28"><span>Signed Recall Notice</span><h1>{notice.revoked_version_id}</h1><p>{notice.id}</p></div>
              <div className={`recall-seal-r28 ${verification?.valid ? "valid" : "invalid"}`}>
                {verification?.valid ? <ShieldCheck size={18} /> : <CircleAlert size={18} />}
                <div><strong>{verification?.status ?? notice.integrity}</strong><span>{verification?.hash_algorithm ?? "SHA-256"}</span></div>
              </div>
            </header>

            <section className="recall-notice-flow-r28" aria-label="Recall routing">
              <div><ShieldAlert size={18} /><span>Knowledge status</span><strong>REVOKED</strong></div>
              <ArrowRight size={16} />
              <div><GitBranch size={18} /><span>Dependencies</span><strong>{notice.cases.length}</strong></div>
              <ArrowRight size={16} />
              <div><UserRoundCheck size={18} /><span>Human review</span><strong>{notice.cases.filter((item) => item.status === "QUEUED").length} pending</strong></div>
            </section>

            <section className="recall-notice-glance-r28">
              <div><Network size={17} /><strong>{notice.cases.length}</strong><span>Routed</span></div>
              <div><FileCheck2 size={17} /><strong>{notice.evidence.length}</strong><span>Evidence</span></div>
              <div><UserRoundCheck size={17} /><strong>{notice.approved_by}</strong><span>Authority</span></div>
              <div><Fingerprint size={17} /><strong>{verification?.valid ? "Verified" : notice.integrity}</strong><span>Integrity</span></div>
            </section>

            <section className="recall-basis-r28">
              <span>RECALL BASIS</span>
              <h2>{notice.reason}</h2>
              <div><span>{notice.source_issue_id}</span><span>{fmtDate(notice.created_at)}</span><span>{notice.status}</span></div>
            </section>

            <section className="recall-routing-r28">
              <div className="recall-section-title-r28"><div><span>ROUTED ADOPTERS</span><h2>Review obligations</h2></div><small>Dependency ≠ defect verdict</small></div>
              <div className="recall-route-grid-r28">
                {notice.cases.map((item, index) => (
                  <article key={item.id}>
                    <div className="recall-route-top-r28" data-label="Review obligation"><span>{String(index + 1).padStart(2, "0")}</span><strong>{item.status}</strong></div>
                    <Network size={20} />
                    <h3>{item.client_name ?? item.implementation_name ?? "Implementation"}</h3>
                    <p>{item.implementation_name ?? item.implementation_id}</p>
                    <span className="recall-investigation-r28">Investigation {item.investigation_id}</span>
                    <a href={`/issues/${encodeURIComponent(notice.source_issue_id)}/analysis`}>Open review <ArrowRight size={14} /></a>
                  </article>
                ))}
              </div>
              <div className="recall-route-boundary-r28"><GitBranch size={16} /><span>{notice.routing_scope.enforced ? "Routed only where current Local A-BOM use intersects the signed adoption scope." : "Routed from current explicit Local A-BOM use."} Routing is a review obligation, not a defect verdict.</span></div>
            </section>

            <div className="recall-proof-stack-r28">
              <details>
                <summary><span><UserRoundCheck size={16} /> Human attestation</span><ChevronDown size={15} /></summary>
                <div className="recall-proof-body-r28">
                  <blockquote>{notice.attestation || `${notice.approved_by} authorised this recall and recall routing.`}</blockquote>
                  <div className="recall-proof-meta-r28"><span>Authority <strong>{notice.approved_by}</strong></span><span>Recall run <strong>{notice.recall_run_id}</strong></span></div>
                </div>
              </details>

              <details>
                <summary><span><FileCheck2 size={16} /> Evidence <b>{notice.evidence.length}</b></span><ChevronDown size={15} /></summary>
                <div className="recall-evidence-grid-r28">
                  {notice.evidence.length === 0 ? <p>No supporting evidence records were returned.</p> : notice.evidence.map((item, index) => (
                    <article key={item.id}><span>{String(index + 1).padStart(2, "0")}</span><div><strong>{item.title}</strong><p>{item.id} · {item.version ?? "version not stated"}</p><code>{shortHash(item.content_hash)}</code></div></article>
                  ))}
                </div>
              </details>

              <details>
                <summary><span><GitBranch size={16} /> Recall scope proof</span><ChevronDown size={15} /></summary>
                <div className="recall-proof-body-r28">
                  <p><strong>Basis:</strong> {notice.routing_scope.basis.replaceAll("_", " ")}</p>
                  <p><strong>Adoption scope:</strong> {notice.routing_scope.enforced ? (notice.routing_scope.mode ?? "SIGNED SCOPE") : "BASELINE / LEGACY EXPLICIT A-BOM"}</p>
                  <p><strong>Explicit dependency edges:</strong> {notice.routing_scope.explicit_dependency_count} · <strong>Routed:</strong> {notice.routing_scope.routed_count} · <strong>Excluded:</strong> {notice.routing_scope.blocked_count}</p>
                  {notice.routing_scope.adoption_receipt_id && <p><strong>Adoption Receipt:</strong> {notice.routing_scope.adoption_receipt_id} · {notice.routing_scope.receipt_integrity}</p>}
                  {notice.routing_scope.blocked_implementations.length > 0 && (
                    <div>{notice.routing_scope.blocked_implementations.map((item) => <p key={`${item.dependency_edge_id}-${item.implementation_id}`}><strong>Excluded:</strong> {item.implementation_id} · {item.reason.replaceAll("_", " ")}</p>)}</div>
                  )}
                </div>
              </details>

              <details>
                <summary><span><Fingerprint size={16} /> Integrity proof</span><ChevronDown size={15} /></summary>
                <div className="recall-integrity-proof-r28">
                  <div><span>Stored SHA-256</span><code>{notice.content_hash}</code><button type="button" onClick={copyHash}>{copied ? <Check size={14} /> : <Clipboard size={14} />}{copied ? "Copied" : "Copy"}</button></div>
                  <div><span>Independent verification</span><strong>{verification?.status ?? notice.integrity}</strong><p>The verifier recomputes the canonical notice payload and compares it with the stored SHA-256 seal.</p></div>
                </div>
              </details>

              <details>
                <summary><span><History size={16} /> Governance history</span><ChevronDown size={15} /></summary>
                <div className="recall-proof-body-r28"><p><strong>Recall does not erase adoption.</strong> Previous adoption remains part of the audit record; this notice records the later withdrawal of that approved knowledge.</p></div>
              </details>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
