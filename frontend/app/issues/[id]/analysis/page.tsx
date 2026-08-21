import { notFound } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { AnalysisShell } from "@/components/analysis-shell";
import { getHealth, getIssue, getIssueUnderstanding, getLatestAnalysisRun } from "@/lib/api";
export const dynamic = "force-dynamic";
export default async function AnalysisPage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<{ run?: string }> }) {
  const { id } = await params;
  const { run } = await searchParams;
  const [health, issue, understanding, analysisRun] = await Promise.all([
    getHealth(),
    getIssue(id).catch(() => null),
    getIssueUnderstanding(id).catch(() => null),
    getLatestAnalysisRun(id).catch(() => null),
  ]);
  if (!issue) notFound();
  return <AppShell health={health} active="Issues" breadcrumbs={[{ label: "Issues", href: "/issues" }, { label: issue.external_ticket_id ?? "Issue", href: `/issues/${id}` }, { label: "Analysis" }]}><AnalysisShell issue={issue} initialUnderstanding={understanding} initialRun={analysisRun} autoRun={run === "1"} /></AppShell>;
}
