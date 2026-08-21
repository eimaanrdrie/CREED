// R15 semantic contract: Human-supplied source record
import {
  ArrowRight,
  BrainCircuit,
  CalendarClock,
  CircleDot,
  FileText,
  FolderSearch2,
  Paperclip,
  ShieldCheck,
  Tag,
  UserRound,
} from "lucide-react";
import type { AnalysisRun, IssueUnderstanding, SupportIssueDetail } from "@/lib/api";

export function IssueDetailWorkspace({
  issue,
  run,
  understanding,
}: {
  issue: SupportIssueDetail;
  run: AnalysisRun | null;
  understanding: IssueUnderstanding | null;
}) {
  const runLabel = run ? run.status.replaceAll("_", " ") : "NOT STARTED";
  const sourceId = issue.external_ticket_id ?? issue.id.slice(0, 8).toUpperCase();

  return (
    <div className="page issue-detail-r04">
      <header className="case-hero-r04">
        <div className="case-hero-copy-r04">
          <h1>{issue.title}</h1>
          <p className="subtitle">Human-supplied source. AI interpretation stays separate.</p>
          <div className="case-hero-meta-r71"><span>Case record</span><strong>{sourceId}</strong></div>
          <div className="case-chip-row-r04">
            <CaseChip icon={<UserRound size={13} />} label={issue.client_name ?? "Client not selected"} />
            <CaseChip icon={<Tag size={13} />} label={issue.issue_type.replaceAll("_", " ")} />
            <CaseChip icon={<ShieldCheck size={13} />} label={issue.severity} tone={severityTone(issue.severity)} />
            <CaseChip icon={<CircleDot size={13} />} label={issue.status.replaceAll("_", " ")} />
          </div>
        </div>
        <div className="case-hero-action-r04">
          <div className="case-analysis-state-r04">
            <span>ASSURANCE WORKFLOW</span>
            <strong>{runLabel}</strong>
            <small>{run ? run.graph_run_id : "No LangGraph analysis run exists for this issue yet."}</small>
          </div>
          <a className="primary-btn" href={`/issues/${issue.id}/analysis`}>
            {run ? "Open analysis workspace" : "Start analysis workspace"}<ArrowRight size={14} />
          </a>
        </div>
      </header>

      <div className="case-overview-grid-r04">
        <section className="card case-source-r04">
          <div className="section-label-r04"><FileText size={14} /><span>01 · SOURCE OBSERVATION</span><b>HUMAN INPUT</b></div>
          <div className="case-source-copy-r04">{issue.description}</div>
          <div className="case-source-meta-r04">
            <MetaItem icon={<CalendarClock size={13} />} label="Created" value={formatDate(issue.created_at)} />
            <MetaItem icon={<CalendarClock size={13} />} label="Updated" value={formatDate(issue.updated_at)} />
            <MetaItem icon={<Paperclip size={13} />} label="Evidence" value={`${issue.attachment_count} linked`} />
          </div>
        </section>

        <section className="card case-readiness-r04">
          <div className="section-label-r04"><BrainCircuit size={14} /><span>02 · ANALYSIS READINESS</span></div>
          <ReadinessRow label="Source record" value="CAPTURED" tone="ok" />
          <ReadinessRow label="Evidence linked" value={issue.attachment_count > 0 ? `${issue.attachment_count} ITEMS` : "NONE"} tone={issue.attachment_count > 0 ? "ok" : "warn"} />
          <ReadinessRow label="Qwen understanding" value={understanding ? understanding.status.replaceAll("_", " ") : "NOT RUN"} tone={understanding ? "ok" : "neutral"} />
          <ReadinessRow label="LangGraph run" value={runLabel} tone={run?.status === "FAILED" ? "bad" : run ? "ok" : "neutral"} />
        </section>
      </div>

      <section className="card case-evidence-r04">
        <div className="panel-head">
          <div><h2>Linked evidence</h2><span>Source artefacts before AI</span></div>
          <span><FolderSearch2 size={13} /> {issue.attachment_count} DOCUMENT{issue.attachment_count === 1 ? "" : "S"}</span>
        </div>
        {issue.attachments.length === 0 ? (
          <div className="case-evidence-empty-r04"><Paperclip size={17} /><div><strong>No evidence linked</strong><p>The case can continue, but findings remain evidence-limited.</p></div></div>
        ) : (
          <div className="case-evidence-ledger-r04">
            {issue.attachments.map((a, index) => (
              <a href="/knowledge" key={a.id} className="case-evidence-row-r04">
                <span className="case-evidence-index-r04">{String(index + 1).padStart(2, "0")}</span>
                <FileText size={15} />
                <div><strong>{a.title}</strong><span>{a.original_filename ?? "Stored evidence"} · {a.document_type}</span></div>
                <b className={a.index_status === "INDEXED" ? "ok" : ""}>{a.index_status.replaceAll("_", " ")}</b>
                <ArrowRight size={13} />
              </a>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function CaseChip({ icon, label, tone = "" }: { icon: React.ReactNode; label: string; tone?: string }) {
  return <span className={`case-chip-r04 ${tone}`}>{icon}{label}</span>;
}
function MetaItem({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return <div className="case-meta-item-r04">{icon}<span>{label}</span><strong>{value}</strong></div>;
}
function ReadinessRow({ label, value, tone }: { label: string; value: string; tone: string }) {
  return <div className="case-readiness-row-r04"><span>{label}</span><b className={tone}>{value}</b></div>;
}
function severityTone(value: string) { return value === "CRITICAL" ? "bad" : value === "HIGH" ? "warn" : ""; }
function formatDate(value: string) { return new Intl.DateTimeFormat("en-MY", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value)); }
