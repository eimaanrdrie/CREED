import { AppShell } from "@/components/app-shell";
import { ClientRegistryWorkspace } from "@/components/client-registry-workspace";
import { getClients, getHealth } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ClientsPage() {
  const [health, clientResult] = await Promise.all([
    getHealth(),
    getClients()
      .then(clients => ({ clients, loadError: false }))
      .catch(() => ({ clients: [], loadError: true })),
  ]);

  return (
    <AppShell health={health} active="Clients">
      <ClientRegistryWorkspace initialClients={clientResult.clients} loadError={clientResult.loadError} />
    </AppShell>
  );
}
