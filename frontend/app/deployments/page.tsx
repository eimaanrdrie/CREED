import { AppShell } from "@/components/app-shell";
import { DeploymentRegistryWorkspace } from "@/components/deployment-registry-workspace";
import { getClients, getDeployments, getDocuments, getHealth, getImplementations } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DeploymentsPage() {
  const [health, deploymentResult, catalogResult] = await Promise.all([
    getHealth(),
    getDeployments()
      .then(deployments => ({ deployments, loadError: false }))
      .catch(() => ({ deployments: [], loadError: true })),
    Promise.all([getImplementations(), getClients(), getDocuments()])
      .then(([implementations, clients, documents]) => ({ implementations, clients, documents, catalogError: false }))
      .catch(() => ({ implementations: [], clients: [], documents: [], catalogError: true })),
  ]);

  return (
    <AppShell health={health} active="Deployments">
      <DeploymentRegistryWorkspace
        initialDeployments={deploymentResult.deployments}
        implementations={catalogResult.implementations}
        clients={catalogResult.clients}
        documents={catalogResult.documents}
        loadError={deploymentResult.loadError}
        catalogError={catalogResult.catalogError}
      />
    </AppShell>
  );
}
