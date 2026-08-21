import { AppShell } from "@/components/app-shell";
import { ApprovedKnowledgeWorkspace } from "@/components/approved-knowledge-workspace";
import {
  getAdoptionReceipt,
  getHealth,
  getImplementationMethodDependencies,
  getRegisteredMethodVersions,
  type AdoptionReceiptSummary,
} from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ApprovedKnowledgePage() {
  const [health, versions, dependencies] = await Promise.all([
    getHealth(),
    getRegisteredMethodVersions().catch(() => []),
    getImplementationMethodDependencies().catch(() => []),
  ]);

  const receiptIds = [...new Set(versions.map((version) => version.adoption_policy?.receipt_id).filter((id): id is string => Boolean(id)))];
  const receiptPairs = await Promise.all(receiptIds.map(async (id) => {
    try { return [id, await getAdoptionReceipt(id)] as const; }
    catch { return [id, null] as const; }
  }));
  const receipts = Object.fromEntries(receiptPairs) as Record<string, AdoptionReceiptSummary | null>;

  return (
    <AppShell health={health} active="Approved Knowledge">
      <ApprovedKnowledgeWorkspace versions={versions} dependencies={dependencies} receipts={receipts} />
    </AppShell>
  );
}
