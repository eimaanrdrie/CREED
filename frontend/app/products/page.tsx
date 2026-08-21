import { AppShell } from "@/components/app-shell";
import { ProductRegistryWorkspace } from "@/components/product-registry-workspace";
import { getHealth, getProducts } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ProductsPage() {
  const [health, productResult] = await Promise.all([
    getHealth(),
    getProducts()
      .then(products => ({ products, loadError: false }))
      .catch(() => ({ products: [], loadError: true })),
  ]);

  return (
    <AppShell health={health} active="Products">
      <ProductRegistryWorkspace initialProducts={productResult.products} loadError={productResult.loadError} />
    </AppShell>
  );
}
