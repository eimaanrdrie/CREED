import { ChevronDown, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export type SignalTone = "neutral" | "info" | "ok" | "warn" | "bad";

export function VisualMetric({
  icon: Icon,
  label,
  value,
  meta,
  tone = "neutral",
}: {
  icon?: LucideIcon;
  label: string;
  value: ReactNode;
  meta?: ReactNode;
  tone?: SignalTone;
}) {
  return (
    <div className={`visual-metric tone-${tone}`}>
      <div className="visual-metric-head">
        {Icon ? <span className="visual-metric-icon"><Icon size={15} aria-hidden="true" /></span> : null}
        <span>{label}</span>
      </div>
      <strong className="visual-metric-value">{value}</strong>
      {meta ? <small className="visual-metric-meta">{meta}</small> : null}
    </div>
  );
}

export function SignalChip({
  icon: Icon,
  children,
  tone = "neutral",
}: {
  icon?: LucideIcon;
  children: ReactNode;
  tone?: SignalTone;
}) {
  return (
    <span className={`signal-chip tone-${tone}`}>
      {Icon ? <Icon size={13} aria-hidden="true" /> : null}
      <span>{children}</span>
    </span>
  );
}

export function ProgressiveDisclosure({
  label,
  children,
  meta,
  defaultOpen = false,
}: {
  label: ReactNode;
  children: ReactNode;
  meta?: ReactNode;
  defaultOpen?: boolean;
}) {
  return (
    <details className="progressive-disclosure" open={defaultOpen}>
      <summary>
        <span className="progressive-disclosure-label">{label}</span>
        <span className="progressive-disclosure-meta">{meta}</span>
        <ChevronDown className="progressive-disclosure-chevron" size={15} aria-hidden="true" />
      </summary>
      <div className="progressive-disclosure-body">{children}</div>
    </details>
  );
}
