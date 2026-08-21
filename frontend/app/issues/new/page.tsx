import { AppShell } from "@/components/app-shell";
import { IssueCapsuleForm, type IssueCapsuleInitialValues } from "@/components/issue-capsule-form";
import { getClients, getHealth } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function NewIssuePage({ searchParams }: { searchParams: Promise<{ demo?: string }> }) {
  const params = await searchParams;
  const [health, clients] = await Promise.all([getHealth(), getClients().catch(() => [])]);
  const atlas = clients.find(client => client.name === "Atlas Bank");
  const demoValues: IssueCapsuleInitialValues | undefined = params.demo === "1" ? {
    ticket: "SUP-PTP-001",
    clientId: atlas?.id ?? "",
    title: "Network retry replays Promise-to-Pay event",
    description: "Atlas Bank reports that a network retry can replay the same Promise-to-Pay event. The repeated event appears to apply another collection-state transition. The issue occurs when the original request times out and the upstream system retries the same event. Please investigate whether the event-processing method is idempotent and whether the same implementation approach has been reused for other clients.",
    issueType: "BUG",
    severity: "HIGH",
    demoLoaded: true,
  } : undefined;
  return (
    <AppShell health={health} active="Issues" breadcrumbs={[{ label: "Issues", href: "/issues" }, { label: "New issue" }]}>
      <div className="page"><IssueCapsuleForm clients={clients} initialValues={demoValues} /></div>
    </AppShell>
  );
}
