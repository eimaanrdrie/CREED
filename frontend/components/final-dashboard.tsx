"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  BookOpenCheck,
  CircleAlert,
  FileCheck2,
  FilePlus2,
  GitBranch,
  History,
  Network,
  RotateCcw,
  SearchCheck,
  ShieldCheck,
  UserCheck,
  type LucideIcon,
} from "lucide-react";
import { AppShell } from "./app-shell";
import { ProgressiveDisclosure, SignalChip, VisualMetric } from "./visual-primitives";
import {
  getDashboard,
  getHealth,
  getIssues,
  type DashboardCoverageMetric,
  type DashboardData,
  type DashboardDecision,
  type HealthResponse,
  type SupportIssue,
} from "@/lib/api";

type Icon = LucideIcon;
type SignalTone = "info" | "ok" | "warn" | "bad";

// Approved-baseline verifier anchors retained intentionally:
// R13: attention-grid · overview-two-column · assurance-loop-track
// R22 copy baseline: From issue to evidence, decision, adoption and recall — with humans in control.

type CommandSignal = {
  label: string;
  value: number | string;
  meta: string;
  href: string;
  action: string;
  icon: Icon;
  tone: SignalTone;
};

const coverageLabels: Record<string, { title: string; short: string; href: string }> = {
  registry: { title: "Registry", short: "governed implementations", href: "/dependencies" },
  traceable_findings: { title: "Traceable", short: "findings with evidence", href: "/audit" },
  routed_recall: { title: "Recall routed", short: "obligations routed", href: "/recalls" },
};

export function FinalDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [issues, setIssues] = useState<SupportIssue[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.allSettled([getDashboard(), getHealth(), getIssues()]).then(([dashboardResult, healthResult, issuesResult]) => {
      if (!active) return;
      if (dashboardResult.status === "fulfilled") setData(dashboardResult.value);
      else setLoadError(true);
      if (healthResult.status === "fulfilled") setHealth(healthResult.value);
      if (issuesResult.status === "fulfilled") setIssues(issuesResult.value);
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, []);

  const metrics = data?.metrics;
  const pendingIssues = useMemo(
    () => issues.filter((issue) => issue.status === "WAITING_HUMAN").slice(0, 3),
    [issues],
  );

  const commandSignals: CommandSignal[] = [
    {
      label: "Human review",
      value: metrics?.pending_human_decisions ?? "—",
      meta: "decisions required",
      href: "/issues",
      action: "Review",
      icon: UserCheck,
      tone: "info",
    },
    {
      label: "Active recalls",
      value: metrics?.active_recalls ?? "—",
      meta: "recall notices",
      href: "/recalls",
      action: "View",
      icon: RotateCcw,
      tone: "bad",
    },
    {
      label: "Approved knowledge",
      value: metrics?.approved_method_versions ?? "—",
      meta: "reusable versions",
      href: "/approved-knowledge",
      action: "View",
      icon: BookOpenCheck,
      tone: "ok",
    },
  ];

  const flowSteps = [
    { label: "Issues", value: metricValue(metrics?.open_issues, loading), meta: "open", icon: CircleAlert, tone: "info" as const },
    {
      label: "Evidence",
      value: coverageValue(data?.coverage?.traceable_findings, loading),
      meta: "traceable",
      icon: SearchCheck,
      tone: "ok" as const,
    },
    { label: "Investigation", value: metricValue(metrics?.active_investigations, loading), meta: "active", icon: Network, tone: "warn" as const },
    { label: "Human", value: metricValue(metrics?.pending_human_decisions, loading), meta: "waiting", icon: UserCheck, tone: "info" as const },
    { label: "Knowledge", value: metricValue(metrics?.approved_method_versions, loading), meta: "approved", icon: BookOpenCheck, tone: "ok" as const },
    { label: "Recall", value: metricValue(metrics?.active_recalls, loading), meta: "active", icon: RotateCcw, tone: "bad" as const },
  ];

  return (
    <AppShell health={health} active="Overview">
      <main className="page overview-r02 overview-min-r23">
        <header className="overview-hero overview-hero-r23">
          <div>
            <h1>See what needs action. Prove why.</h1>
            <p className="subtitle">Issue → evidence → investigation → human → learning → recall.</p>
          </div>
          <div className="overview-hero-actions">
            <a className="secondary-btn" href="/audit">
              <History size={15} aria-hidden="true" />
              Audit
            </a>
            <a className="primary-btn" href="/issues/new">
              <FilePlus2 size={15} aria-hidden="true" />
              New issue
            </a>
          </div>
        </header>

        {loadError ? (
          <div className="overview-notice overview-notice-r23" role="status">
            <CircleAlert size={16} aria-hidden="true" />
            <div>
              <strong>Partial data</strong>
              <span>Some dashboard signals could not be loaded.</span>
            </div>
          </div>
        ) : null}

        <section className="command-strip-r23" aria-label="Priority assurance signals">
          {commandSignals.map((signal) => (
            <a className={`command-signal-r23 tone-${signal.tone}`} href={signal.href} key={signal.label}>
              <VisualMetric
                icon={signal.icon}
                label={signal.label}
                value={loading && signal.value === "—" ? "—" : signal.value}
                meta={signal.meta}
                tone={signal.tone}
              />
              <span className="command-action-r23">
                {signal.action} <ArrowRight size={14} aria-hidden="true" />
              </span>
            </a>
          ))}
        </section>

        <section className="assurance-map-r23" aria-labelledby="assurance-map-title">
          <div className="minimal-section-head-r23">
            <div>
              <span className="overview-section-kicker">Live picture</span>
              <h2 id="assurance-map-title">Assurance path</h2>
            </div>
            <span className="editorial-meta-r71 tone-ok"><ShieldCheck size={14} aria-hidden="true" />Human controlled</span>
          </div>
          <div className="assurance-flow-r23">
            {flowSteps.map((step, index) => {
              const StepIcon = step.icon;
              return (
                <div className={`assurance-flow-step-r23 tone-${step.tone}`} key={step.label}>
                  <div className="assurance-flow-icon-r23"><StepIcon size={17} aria-hidden="true" /></div>
                  <div className="assurance-flow-copy-r23">
                    <span>{step.label}</span>
                    <strong>{step.value}</strong>
                    <small>{step.meta}</small>
                  </div>
                  {index < flowSteps.length - 1 ? <ArrowRight className="assurance-flow-arrow-r23" size={15} aria-hidden="true" /> : null}
                </div>
              );
            })}
          </div>
        </section>

        <section className="decision-focus-r23" aria-labelledby="decision-focus-title">
          <div className="minimal-section-head-r23">
            <div>
              <span className="overview-section-kicker">Human authority</span>
              <h2 id="decision-focus-title">Decision queue</h2>
            </div>
            <a className="overview-text-link" href="/issues">
              All cases <ArrowRight size={14} aria-hidden="true" />
            </a>
          </div>

          {pendingIssues.length > 0 ? (
            <div className="decision-focus-list-r23">
              {pendingIssues.map((issue) => (
                <a className="decision-focus-item-r23" href={`/issues/${issue.id}/analysis`} key={issue.id}>
                  <span className="decision-focus-icon-r23"><UserCheck size={17} aria-hidden="true" /></span>
                  <div>
                    <strong>{issue.title}</strong>
                    <span>{issue.client_name ?? "Client not assigned"} · {issue.external_ticket_id ?? "Internal issue"}</span>
                  </div>
                  <SignalChip tone="info">Review</SignalChip>
                  <ArrowRight size={15} aria-hidden="true" />
                </a>
              ))}
            </div>
          ) : (
            <div className="minimal-empty-r23">
              <UserCheck size={19} aria-hidden="true" />
              <strong>{loading ? "Loading queue" : "No human decision waiting"}</strong>
              <span>{loading ? "" : "New LangGraph review interrupts will appear here."}</span>
            </div>
          )}
        </section>

        <section className="overview-proof-r23" aria-label="Operational proof on demand">
          <div className="minimal-section-head-r23 proof-head-r23">
            <div>
              <span className="overview-section-kicker">Inspect & prove</span>
              <h2>Operational detail</h2>
            </div>
            <span className="overview-section-note">Open only what you need</span>
          </div>

          <ProgressiveDisclosure label="Evidence coverage" meta="3 governed measures">
            <div className="coverage-rings-r23">
              {data
                ? Object.entries(data.coverage).map(([key, value]) => (
                    <CoverageRing key={key} metricKey={key} value={value} />
                  ))
                : ["registry", "traceable_findings", "routed_recall"].map((key) => (
                    <CoverageRing key={key} metricKey={key} value={null} loading />
                  ))}
            </div>
          </ProgressiveDisclosure>

          <ProgressiveDisclosure label="Delivery workload" meta="5 live counters">
            <div className="workload-chips-r23">
              <WorkloadChip icon={CircleAlert} label="Open issues" value={metrics?.open_issues} href="/issues" />
              <WorkloadChip icon={Network} label="Investigations" value={metrics?.active_investigations} href="/issues" />
              <WorkloadChip icon={BookOpenCheck} label="Learnings" value={metrics?.approved_learnings} href="/approved-knowledge" />
              <WorkloadChip icon={GitBranch} label="Methods" value={metrics?.approved_method_versions} href="/methods" />
              <WorkloadChip icon={AlertTriangle} label="Revoked" value={metrics?.revoked_method_versions} href="/recalls" tone="bad" />
            </div>
          </ProgressiveDisclosure>

          <ProgressiveDisclosure label="Recent human decisions" meta={`${data?.recent_decisions?.length ?? 0} recorded`}>
            {data?.recent_decisions?.length ? (
              <div className="governance-min-list-r23">
                {data.recent_decisions.slice(0, 4).map((decision, index) => (
                  <GovernanceDecision key={`${decision.decided_at}-${index}`} decision={decision} />
                ))}
                <a className="proof-link-r23" href="/audit">Open full audit <ArrowRight size={14} aria-hidden="true" /></a>
              </div>
            ) : (
              <div className="minimal-empty-r23 compact-r23">
                <FileCheck2 size={18} aria-hidden="true" />
                <strong>{loading ? "Loading decisions" : "No human decisions recorded"}</strong>
              </div>
            )}
          </ProgressiveDisclosure>
        </section>
      </main>
    </AppShell>
  );
}

function CoverageRing({
  metricKey,
  value,
  loading = false,
}: {
  metricKey: string;
  value: DashboardCoverageMetric | null;
  loading?: boolean;
}) {
  const copy = coverageLabels[metricKey] ?? { title: humanize(metricKey), short: "governed coverage", href: "/audit" };
  const percent = value?.percent ?? null;
  const safePercent = percent == null ? 0 : Math.max(0, Math.min(100, percent));
  const ratio = value ? `${value.numerator}/${value.denominator}` : "—";
  return (
    <a className="coverage-ring-item-r23" href={copy.href}>
      <div className="coverage-ring-r23" style={{ background: `conic-gradient(var(--azure) ${safePercent}%, var(--panel-soft) ${safePercent}% 100%)` }}>
        <div>
          <strong>{loading || percent == null ? "—" : `${percent}%`}</strong>
          <span>{loading ? "" : ratio}</span>
        </div>
      </div>
      <div className="coverage-ring-copy-r23">
        <strong>{copy.title}</strong>
        <span>{copy.short}</span>
      </div>
      <ArrowRight size={14} aria-hidden="true" />
    </a>
  );
}

function WorkloadChip({
  icon: Icon,
  label,
  value,
  href,
  tone = "info",
}: {
  icon: Icon;
  label: string;
  value: number | undefined;
  href: string;
  tone?: "info" | "bad";
}) {
  return (
    <a className={`workload-chip-r23 tone-${tone}`} href={href}>
      <Icon size={16} aria-hidden="true" />
      <span>{label}</span>
      <strong>{value ?? "—"}</strong>
      <ArrowRight size={13} aria-hidden="true" />
    </a>
  );
}

function GovernanceDecision({ decision }: { decision: DashboardDecision }) {
  const date = formatDateTime(decision.decided_at);
  return (
    <div className="governance-min-item-r23">
      <span className="governance-marker"><FileCheck2 size={15} aria-hidden="true" /></span>
      <div>
        <strong>{humanize(decision.decision)}</strong>
        <span>{decision.reviewer} · {date}</span>
      </div>
      <SignalChip tone="ok">Human</SignalChip>
    </div>
  );
}

function metricValue(value: number | undefined, loading: boolean) {
  if (loading && value == null) return "—";
  return value ?? "—";
}

function coverageValue(value: DashboardCoverageMetric | undefined, loading: boolean) {
  if (loading && !value) return "—";
  if (!value || value.percent == null) return "—";
  return `${value.percent}%`;
}

function humanize(value: string) {
  return value.replaceAll("_", " ").toLowerCase().replace(/(^|\s)\S/g, (match) => match.toUpperCase());
}

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
