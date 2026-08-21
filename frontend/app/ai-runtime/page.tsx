import { AiRuntimeConsole } from "@/components/ai-runtime-console";
import { AppShell } from "@/components/app-shell";
import { getAiRuntime, getHealth } from "@/lib/api";
export default async function AiRuntimePage() {
  const [health, runtime] = await Promise.all([getHealth(), getAiRuntime(false)]);
  return <AppShell health={health} active="AI Runtime"><div className="page"><AiRuntimeConsole initialRuntime={runtime} /></div></AppShell>;
}
