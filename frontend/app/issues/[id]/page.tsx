import { notFound } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { IssueDetailWorkspace } from "@/components/issue-detail-workspace";
import { getHealth, getIssue, getIssueUnderstanding, getLatestAnalysisRun } from "@/lib/api";
export const dynamic = "force-dynamic";
export default async function IssuePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [health, issue, understanding, run] = await Promise.all([
    getHealth(),
    getIssue(id).catch(() => null),
    getIssueUnderstanding(id).catch(() => null),
    getLatestAnalysisRun(id).catch(() => null),
  ]);
  if (!issue) notFound();
  return <AppShell health={health} active="Issues" breadcrumbs={[{ label: "Issues", href: "/issues" }, { label: issue.external_ticket_id ?? "Issue" }]}><IssueDetailWorkspace issue={issue} understanding={understanding} run={run} /></AppShell>;
}
