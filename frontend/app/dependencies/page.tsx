import { AppShell } from "@/components/app-shell";
import { DependencyRegistryWorkspace } from "@/components/dependency-registry-workspace";
import {
  getDocuments,
  getHealth,
  getImplementationMethodDependencies,
  getImplementations,
  getRegisteredMethodVersions,
} from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DependenciesPage() {
  const [health, dependencyResult, catalogResult] = await Promise.all([
    getHealth(),
    getImplementationMethodDependencies()
      .then(dependencies => ({ dependencies, loadError: false }))
      .catch(() => ({ dependencies: [], loadError: true })),
    Promise.all([getImplementations(), getRegisteredMethodVersions(), getDocuments()])
      .then(([implementations, methodVersions, documents]) => ({
        implementations,
        methodVersions,
        documents,
        catalogError: false,
      }))
      .catch(() => ({ implementations: [], methodVersions: [], documents: [], catalogError: true })),
  ]);

  return (
    <AppShell health={health} active="Dependencies">
      <DependencyRegistryWorkspace
        initialDependencies={dependencyResult.dependencies}
        implementations={catalogResult.implementations}
        methodVersions={catalogResult.methodVersions}
        documents={catalogResult.documents}
        loadError={dependencyResult.loadError}
        catalogError={catalogResult.catalogError}
      />
    </AppShell>
  );
}
