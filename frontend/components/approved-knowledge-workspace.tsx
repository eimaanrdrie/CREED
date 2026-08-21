import {
  CheckCircle2,
  ChevronDown,
  Fingerprint,
  GitBranch,
  Network,
  ShieldCheck,
  UsersRound,
} from "lucide-react";
import type {
  AdoptionReceiptSummary,
  ImplementationMethodDependencyRecord,
  RegisteredMethodVersionRecord,
} from "@/lib/api";

type ReceiptMap = Record<string, AdoptionReceiptSummary | null>;

function scopeLabel(version: RegisteredMethodVersionRecord) {
  const policy = version.adoption_policy;
  if (!policy?.enforced) return "Baseline approval";
  if (policy.scope_mode === "METHOD_CATALOG") return "Method catalog";
  if (policy.scope_mode === "CURRENT_REGISTERED_IMPLEMENTATIONS") return "Current registered adopters";
  if (policy.scope_mode === "SELECTED_IMPLEMENTATIONS") return "Selected implementations";
  return "Governed scope";
}

function displayDate(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function ApprovedKnowledgeWorkspace({
  versions,
  dependencies,
  receipts,
}: {
  versions: RegisteredMethodVersionRecord[];
  dependencies: ImplementationMethodDependencyRecord[];
  receipts: ReceiptMap;
}) {
  const approved = [...versions]
    .filter((version) => version.status === "APPROVED")
    .sort((a, b) => a.method_name.localeCompare(b.method_name) || b.version.localeCompare(a.version));

  return (
    <div className="page approved-knowledge-page-r99-m01">
      <header className="approved-knowledge-hero-r99-m01">
        <div>
          <h1>Approved Knowledge</h1>
          <p className="subtitle">Human-approved reusable delivery knowledge and its current adoption.</p>
        </div>
        <span className="editorial-meta-r71 tone-ok"><ShieldCheck size={14}/> GOVERNED · {approved.length} APPROVED</span>
      </header>

      <section className="approved-knowledge-list-r99-m01" aria-label="Approved knowledge versions">
        {approved.length === 0 ? (
          <div className="approved-knowledge-empty-r99-m01">
            <CheckCircle2 size={22}/><strong>No approved knowledge yet</strong>
            <p>Approved baseline or learned method versions will appear here after Human Authority approval.</p>
          </div>
        ) : approved.map((version, index) => {
          const inUse = dependencies.filter((edge) => edge.method_version_id === version.id);
          const receiptId = version.adoption_policy?.receipt_id ?? null;
          const receipt = receiptId ? receipts[receiptId] ?? null : null;
          const learned = Boolean(version.adoption_policy?.enforced);
          return (
            <details className="approved-knowledge-row-r99-m01" key={version.id}>
              <summary>
                <span className="approved-knowledge-index-r99-m01">{String(index + 1).padStart(2, "0")}</span>
                <span className="approved-knowledge-copy-r99-m01">
                  <strong>{version.method_name}</strong>
                  <small>{version.version} · {learned ? "Governed learning" : "Approved baseline"}</small>
                </span>
                <span className="approved-knowledge-status-r99-m01"><CheckCircle2 size={12}/> APPROVED</span>
                <span className="approved-knowledge-use-r99-m01"><UsersRound size={13}/>{inUse.length} in use</span>
                <ChevronDown size={15} className="approved-knowledge-chevron-r99-m01"/>
              </summary>
              <div className="approved-knowledge-detail-r99-m01">
                <div className="approved-knowledge-facts-r99-m01">
                  <div><span>Method</span><strong>{version.method_name}</strong></div>
                  <div><span>Approved version</span><strong>{version.version}</strong></div>
                  <div><span>Adoption scope</span><strong>{scopeLabel(version)}</strong></div>
                  <div><span>Current explicit use</span><strong>{inUse.length} implementation{inUse.length === 1 ? "" : "s"}</strong></div>
                </div>

                {inUse.length > 0 && (
                  <details className="approved-knowledge-disclosure-r99-m01">
                    <summary><span><Network size={14}/> Implementations using this version</span><span>{inUse.length}</span><ChevronDown size={14}/></summary>
                    <div className="approved-knowledge-adopters-r99-m01">
                      {inUse.map((edge) => <div key={edge.id}><strong>{edge.implementation_name}</strong><span>{edge.client_name} · {edge.implementation_release_version}</span></div>)}
                    </div>
                  </details>
                )}

                {learned && (
                  <details className="approved-knowledge-disclosure-r99-m01">
                    <summary><span><Fingerprint size={14}/> Signed adoption receipt</span><span>{version.adoption_policy?.receipt_integrity ?? "UNKNOWN"}</span><ChevronDown size={14}/></summary>
                    <div className="approved-knowledge-receipt-r99-m01">
                      {receipt ? <>
                        <div><span>Receipt</span><strong className="mono-r08">{receipt.id}</strong></div>
                        <div><span>Approved by</span><strong>{receipt.approved_by}</strong></div>
                        <div><span>Approved at</span><strong>{displayDate(receipt.approved_at)}</strong></div>
                        <div><span>Evidence sealed</span><strong>{receipt.evidence.length}</strong></div>
                        <div className="wide"><span>Approval rationale</span><p>{receipt.approval_reason}</p></div>
                        <div className="wide"><span>SHA-256</span><code>{receipt.content_hash}</code></div>
                      </> : <p>Receipt metadata is registered, but the receipt detail could not be loaded.</p>}
                    </div>
                  </details>
                )}

                <div className="approved-knowledge-boundary-r99-m01"><GitBranch size={14}/><span>Approval and use are shown separately. An approved version is not treated as deployed unless an explicit Registry dependency exists.</span></div>
              </div>
            </details>
          );
        })}
      </section>
    </div>
  );
}
