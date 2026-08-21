import { AppShell } from "@/components/app-shell";
import { IssuesWorkspace } from "@/components/issues-workspace";
import { getHealth, getIssues } from "@/lib/api";
export const dynamic = "force-dynamic";
export default async function IssuesPage() {
  const [health, issues] = await Promise.all([getHealth(), getIssues().catch(() => [])]);
  return <AppShell health={health} active="Issues"><IssuesWorkspace issues={issues} /></AppShell>;
}
