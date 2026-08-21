import { AppShell } from "@/components/app-shell";
import { OwnershipRegistryWorkspace } from "@/components/ownership-registry-workspace";
import {
  getDeliveryMethods,
  getHealth,
  getHumanAuthorities,
  getImplementations,
  getModules,
  getOwnershipAssignments,
  getProducts,
} from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function OwnershipPage() {
  const [health, registryResult, catalogResult] = await Promise.all([
    getHealth(),
    getOwnershipAssignments()
      .then(assignments => ({ assignments, loadError: false }))
      .catch(() => ({ assignments: [], loadError: true })),
    Promise.all([getProducts(), getModules(), getImplementations(), getDeliveryMethods(), getHumanAuthorities()])
      .then(([products, modules, implementations, methods, authorities]) => ({
        products, modules, implementations, methods, authorities, catalogError: false,
      }))
      .catch(() => ({ products: [], modules: [], implementations: [], methods: [], authorities: [], catalogError: true })),
  ]);

  return (
    <AppShell health={health} active="Ownership">
      <OwnershipRegistryWorkspace
        initialAssignments={registryResult.assignments}
        products={catalogResult.products}
        modules={catalogResult.modules}
        implementations={catalogResult.implementations}
        methods={catalogResult.methods}
        authorities={catalogResult.authorities}
        loadError={registryResult.loadError}
        catalogError={catalogResult.catalogError}
      />
    </AppShell>
  );
}
