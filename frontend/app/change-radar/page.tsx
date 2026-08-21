import { ChangeRadarWorkspace } from "@/components/change-radar-workspace";
export default async function Page({searchParams}:{searchParams:Promise<{run?:string;recall?:string}>}){const q=await searchParams;return <ChangeRadarWorkspace run={q.run} recall={q.recall}/>}
