import type { ServiceState } from "@/lib/api";

export function StatusPill({ state }: { state: ServiceState }) {
  const style = state === "CONNECTED" ? "ok" : state === "UNAVAILABLE" ? "bad" : "warn";
  const label = state.replaceAll("_", " ");
  return <span className={`status-pill ${style}`} role="status" aria-label={`Status: ${label}`}><span className={`status-dot ${style}`} aria-hidden="true" />{label}</span>;
}
