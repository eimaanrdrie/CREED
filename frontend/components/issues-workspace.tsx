"use client";

import { useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowUpRight,
  CircleDot,
  FileWarning,
  Filter,
  Paperclip,
  Plus,
  Search,
  ShieldAlert,
  SlidersHorizontal,
  X,
} from "lucide-react";
import type { SupportIssue } from "@/lib/api";
import { SignalChip } from "@/components/visual-primitives";

const CLOSED = new Set(["RESOLVED", "CLOSED"]);
const SEVERITY_ORDER: Record<string, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, UNKNOWN: 4 };

function humanize(value: string) {
  return value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, letter => letter.toUpperCase());
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "2-digit" }).format(date);
}

function statusTone(status: string) {
  if (["RESOLVED", "CLOSED", "COMPLETED"].includes(status)) return "ok";
  if (["FAILED", "BLOCKED", "REVOKED"].includes(status)) return "bad";
  if (["WAITING_HUMAN", "PENDING", "ANALYSING"].includes(status)) return "warn";
  return "neutral";
}

function severityTone(severity: string): "neutral" | "warn" | "bad" {
  if (["CRITICAL", "HIGH"].includes(severity)) return "bad";
  if (severity === "MEDIUM") return "warn";
  return "neutral";
}

export function IssuesWorkspace({ issues }: { issues: SupportIssue[] }) {
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("ALL");
  const [status, setStatus] = useState("ALL");
  const [type, setType] = useState("ALL");

  const severities = useMemo(() => Array.from(new Set(issues.map(issue => issue.severity))).sort((a, b) => (SEVERITY_ORDER[a] ?? 9) - (SEVERITY_ORDER[b] ?? 9)), [issues]);
  const statuses = useMemo(() => Array.from(new Set(issues.map(issue => issue.status))).sort(), [issues]);
  const types = useMemo(() => Array.from(new Set(issues.map(issue => issue.issue_type))).sort(), [issues]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return [...issues]
      .filter(issue => severity === "ALL" || issue.severity === severity)
      .filter(issue => status === "ALL" || issue.status === status)
      .filter(issue => type === "ALL" || issue.issue_type === type)
      .filter(issue => {
        if (!needle) return true;
        return [issue.title, issue.client_name, issue.external_ticket_id, issue.description]
          .filter(Boolean)
          .some(value => String(value).toLowerCase().includes(needle));
      })
      .sort((a, b) => {
        const severityDelta = (SEVERITY_ORDER[a.severity] ?? 9) - (SEVERITY_ORDER[b.severity] ?? 9);
        if (severityDelta !== 0) return severityDelta;
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
      });
  }, [issues, query, severity, status, type]);

  const open = issues.filter(issue => !CLOSED.has(issue.status)).length;
  const highPriority = issues.filter(issue => !CLOSED.has(issue.status) && ["CRITICAL", "HIGH"].includes(issue.severity)).length;
  const waitingHuman = issues.filter(issue => issue.status === "WAITING_HUMAN").length;
  const withEvidence = issues.filter(issue => issue.attachment_count > 0).length;
  const activeFilterCount = [severity, status, type].filter(value => value !== "ALL").length + (query.trim() ? 1 : 0);

  function clearFilters() {
    setQuery("");
    setSeverity("ALL");
    setStatus("ALL");
    setType("ALL");
  }

  return (
    <div className="page issues-page issues-min-r24">
      <div className="title-row issues-title-row issues-title-r24">
        <div>
          <h1>Issues</h1>
          <p className="subtitle">Search, triage and open governed delivery cases.</p>
        </div>
        <a className="primary-btn" href="/issues/new"><Plus size={16} />New issue</a>
      </div>

      <section className="issue-command-strip issue-command-r24" aria-label="Issue workload summary">
        <IssueSignal icon={FileWarning} label="Open" value={open} note="Unresolved" />
        <IssueSignal icon={ShieldAlert} label="High priority" value={highPriority} note="Critical / high" tone={highPriority ? "bad" : "neutral"} />
        <IssueSignal icon={CircleDot} label="Human review" value={waitingHuman} note="Awaiting authority" tone={waitingHuman ? "warn" : "neutral"} />
        <IssueSignal icon={Paperclip} label="Evidence" value={withEvidence} note={`${withEvidence}/${issues.length || 0} attached`} />
      </section>

      <section className="card issue-ledger issue-ledger-r24">
        <div className="issue-ledger-head issue-ledger-head-r24">
          <div>
            <h2>Cases</h2>
            <span className="editorial-meta-r71">{filtered.length} visible</span>
          </div>
          {activeFilterCount > 0 && <button type="button" className="ghost-btn compact" onClick={clearFilters}><X size={14} />Clear {activeFilterCount}</button>}
        </div>

        <div className="issue-filter-bar issue-filter-bar-r24">
          <label className="issue-search issue-search-r24">
            <Search size={16} aria-hidden="true" />
            <input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search cases" aria-label="Search issues" />
            {query && <button type="button" aria-label="Clear search" onClick={() => setQuery("")}><X size={14} /></button>}
          </label>
          <details className="issue-filter-disclosure-r24" open={activeFilterCount > (query.trim() ? 1 : 0)}>
            <summary>
              <Filter size={15} aria-hidden="true" />
              <span>Filters</span>
              {activeFilterCount > (query.trim() ? 1 : 0) && <strong>{activeFilterCount - (query.trim() ? 1 : 0)}</strong>}
            </summary>
            <div className="issue-filter-group" aria-label="Issue filters">
              <FilterSelect icon={AlertTriangle} label="Severity" value={severity} onChange={setSeverity} options={severities} />
              <FilterSelect icon={CircleDot} label="Status" value={status} onChange={setStatus} options={statuses} />
              <FilterSelect icon={SlidersHorizontal} label="Type" value={type} onChange={setType} options={types} />
            </div>
          </details>
        </div>

        {issues.length === 0 ? (
          <div className="issue-empty-state">
            <FileWarning size={25} />
            <strong>No cases yet</strong>
            <a className="secondary-btn" href="/issues/new"><Plus size={14} />Create issue</a>
          </div>
        ) : filtered.length === 0 ? (
          <div className="issue-empty-state">
            <Filter size={24} />
            <strong>No matches</strong>
            <button type="button" className="secondary-btn" onClick={clearFilters}><X size={14} />Clear filters</button>
          </div>
        ) : (
          <div className="issue-ledger-table issue-case-list-r24" role="table" aria-label="Issue registry">
            <div className="issue-ledger-columns" role="row">
              <span>Case</span><span>Client / ticket</span><span>Classification</span><span>Evidence</span><span>Updated</span><span>Status</span><span aria-hidden="true" />
            </div>
            {filtered.map(issue => (
              <a className={`issue-ledger-row issue-case-row-r24 severity-${issue.severity.toLowerCase()}`} href={`/issues/${issue.id}`} key={issue.id} role="row">
                <div className="issue-ledger-case issue-ledger-case-r33" role="cell">
                  <span className="issue-row-priority" aria-hidden="true" />
                  <div>
                    <strong>{issue.title}</strong>
                    <span className="issue-case-signals-r24 issue-case-signals-r33">
                      <SignalChip tone={severityTone(issue.severity)}>{humanize(issue.severity)}</SignalChip>
                      <SignalChip>{humanize(issue.issue_type)}</SignalChip>
                      <SignalChip icon={Paperclip} tone={issue.attachment_count ? "info" : "neutral"}>{issue.attachment_count}</SignalChip>
                    </span>
                  </div>
                </div>
                <div className="issue-ledger-client" role="cell" data-label="Client / ticket"><strong>{issue.client_name ?? "Unassigned"}</strong><span>{issue.external_ticket_id ?? "No ticket"}</span></div>
                <div className="issue-ledger-classification" role="cell" data-label="Classification"><span className={`severity-badge severity-${issue.severity.toLowerCase()}`}>{issue.severity}</span><small>{humanize(issue.issue_type)}</small></div>
                <div className="issue-ledger-evidence" role="cell" data-label="Evidence"><Paperclip size={14} /><strong>{issue.attachment_count}</strong></div>
                <time className="issue-ledger-date" dateTime={issue.updated_at} role="cell" data-label="Updated">{formatDate(issue.updated_at)}</time>
                <div className="issue-ledger-status" role="cell" data-label="Status"><span className={`issue-status-badge ${statusTone(issue.status)}`}>{humanize(issue.status)}</span></div>
                <ArrowUpRight className="issue-ledger-open" size={16} aria-hidden="true" />
              </a>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function IssueSignal({ icon: Icon, label, value, note, tone = "neutral" }: { icon: typeof FileWarning; label: string; value: number; note: string; tone?: "neutral" | "warn" | "bad" }) {
  return <div className={`issue-signal issue-signal-r24 ${tone}`}><span className="issue-signal-icon"><Icon size={16} /></span><div><span>{label}</span><strong>{value}</strong><small>{note}</small></div></div>;
}

function FilterSelect({ icon: Icon, label, value, onChange, options }: { icon: typeof Filter; label: string; value: string; onChange: (value: string) => void; options: string[] }) {
  return <label className="issue-filter-select"><Icon size={14} aria-hidden="true" /><span>{label}</span><select value={value} onChange={event => onChange(event.target.value)} aria-label={`Filter by ${label.toLowerCase()}`}><option value="ALL">All</option>{options.map(option => <option value={option} key={option}>{humanize(option)}</option>)}</select></label>;
}
