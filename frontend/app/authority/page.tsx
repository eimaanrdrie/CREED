import { AppShell } from "@/components/app-shell";
import { HumanAuthorityWorkspace } from "@/components/human-authority-workspace";
import { getHealth, getHumanAuthorities } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function AuthorityPage() {
  const [health, registryResult] = await Promise.all([
    getHealth(),
    getHumanAuthorities()
      .then(authorities => ({ authorities, loadError: false }))
      .catch(() => ({ authorities: [], loadError: true })),
  ]);

  return (
    <AppShell health={health} active="Authority">
      <HumanAuthorityWorkspace
        initialAuthorities={registryResult.authorities}
        loadError={registryResult.loadError}
      />
    </AppShell>
  );
}
