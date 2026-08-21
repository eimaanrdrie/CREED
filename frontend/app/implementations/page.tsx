import { AppShell } from "@/components/app-shell";
import { ImplementationRegistryWorkspace } from "@/components/implementation-registry-workspace";
import { getClients, getHealth, getImplementations, getModules, getProducts } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ImplementationsPage() {
  const [health, implementationResult, catalogResult] = await Promise.all([
    getHealth(),
    getImplementations()
      .then(implementations => ({ implementations, loadError: false }))
      .catch(() => ({ implementations: [], loadError: true })),
    Promise.all([getClients(), getProducts(), getModules()])
      .then(([clients, products, modules]) => ({ clients, products, modules, catalogError: false }))
      .catch(() => ({ clients: [], products: [], modules: [], catalogError: true })),
  ]);

  return (
    <AppShell health={health} active="Implementations">
      <ImplementationRegistryWorkspace
        initialImplementations={implementationResult.implementations}
        clients={catalogResult.clients}
        products={catalogResult.products}
        modules={catalogResult.modules}
        loadError={implementationResult.loadError}
        catalogError={catalogResult.catalogError}
      />
    </AppShell>
  );
}
