import { AppShell } from "@/components/app-shell";
import { KnowledgeWorkspace } from "@/components/knowledge-workspace";
import { getDocuments, getHealth } from "@/lib/api";
export const dynamic = "force-dynamic";
export default async function KnowledgePage() {
  const [health, documents] = await Promise.all([getHealth(), getDocuments().catch(() => [])]);
  return <AppShell health={health} active="Evidence Repository"><KnowledgeWorkspace initialDocuments={documents} /></AppShell>;
}
