import { AppShell } from "@/components/app-shell";
import { ModuleRegistryWorkspace } from "@/components/module-registry-workspace";
import { getHealth, getModules, getProducts } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ModulesPage() {
  const [health, catalogResult] = await Promise.all([
    getHealth(),
    Promise.all([getProducts(), getModules()])
      .then(([products, modules]) => ({ products, modules, loadError: false }))
      .catch(() => ({ products: [], modules: [], loadError: true })),
  ]);

  return (
    <AppShell health={health} active="Modules">
      <ModuleRegistryWorkspace
        initialProducts={catalogResult.products}
        initialModules={catalogResult.modules}
        loadError={catalogResult.loadError}
      />
    </AppShell>
  );
}
