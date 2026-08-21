import { AppShell } from "@/components/app-shell";
import { MethodRegistryWorkspace } from "@/components/method-registry-workspace";
import { getDeliveryMethods, getHealth, getHumanAuthorities, getModules, getProducts, getRegisteredMethodVersions } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function MethodsPage() {
  const [health, registryResult, catalogResult, authorityResult] = await Promise.all([
    getHealth(),
    Promise.all([getDeliveryMethods(), getRegisteredMethodVersions()])
      .then(([methods, versions]) => ({ methods, versions, loadError: false }))
      .catch(() => ({ methods: [], versions: [], loadError: true })),
    Promise.all([getProducts(), getModules()])
      .then(([products, modules]) => ({ products, modules, catalogError: false }))
      .catch(() => ({ products: [], modules: [], catalogError: true })),
    getHumanAuthorities()
      .then(authorities => ({ authorities, authorityError: false }))
      .catch(() => ({ authorities: [], authorityError: true })),
  ]);

  return (
    <AppShell health={health} active="Methods">
      <MethodRegistryWorkspace
        initialMethods={registryResult.methods}
        initialVersions={registryResult.versions}
        products={catalogResult.products}
        modules={catalogResult.modules}
        authorities={authorityResult.authorities}
        loadError={registryResult.loadError}
        catalogError={catalogResult.catalogError}
        authorityError={authorityResult.authorityError}
      />
    </AppShell>
  );
}
