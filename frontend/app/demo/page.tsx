import { AppShell } from "@/components/app-shell";
import { DemoReadinessWorkspace } from "@/components/demo-readiness-workspace";
import { getDemoReadiness, getHealth } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DemoReadinessPage() {
  const [health, readiness] = await Promise.all([
    getHealth(),
    getDemoReadiness(false).catch(() => null),
  ]);
  return (
    <AppShell
      health={health}
      active="Overview"
      breadcrumbs={[{ label: "Overview", href: "/" }, { label: "Demo readiness" }]}
    >
      <DemoReadinessWorkspace initial={readiness} />
    </AppShell>
  );
}
