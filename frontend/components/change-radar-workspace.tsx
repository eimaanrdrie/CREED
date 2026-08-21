"use client";

// R16 semantic contracts: Priority is not a final impact decision. Routing means review is required; it does not declare that an implementation is defective.
import { memo, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BookOpenCheck,
  CircleDot,
  FileText,
  Filter,
  GitBranch,
  Network,
  Radar,
  RotateCcw,
  SearchCheck,
  ShieldAlert,
  ShieldCheck,
  X,
} from "lucide-react";
import { AppShell } from "./app-shell";
import { ProgressiveDisclosure, SignalChip, VisualMetric } from "./visual-primitives";
import {
  getDocument,
  getHealth,
  getImpact,
  getRunInvestigations,
  getRecall,
  type EvidenceDocumentDetail,
  type HealthResponse,
  type ImpactData,
} from "@/lib/api";

type RadarMode = "impact" | "recall";
type RadarBand = "REPORTED_SOURCE" | "HIGH" | "MEDIUM" | "LOW" | "QUEUED" | "ACTIVE" | "REVOKED" | string;

type RadarNodeData = {
  label: string;
  eyebrow: string;
  kind: "issue" | "method" | "implementation" | "recall";
  band?: RadarBand;
  score?: number | null;
  selected?: boolean;
  actionState?: "active" | "muted" | "neutral";
  verdict?: string | null;
};

type CreedRadarNode = Node<RadarNodeData, "creedRadar">;
type ImpactResult = ImpactData["results"][number];
type RecallCase = {
  id: string;
  implementation_id: string;
  implementation_name?: string | null;
  client_name?: string | null;
  investigation_id?: string | null;
  status: string;
  dependency_edge_id?: string | null;
};

const SIGNAL_LABELS: Record<string, { label: string; description: string }> = {
  method: { label: "Method version", description: "Same governed delivery method/version dependency." },
  module: { label: "Module", description: "Shared product/module context with the reported issue." },
  fsd: { label: "Shared FSD", description: "Specification evidence linked to the same method context." },
  configuration: { label: "Configuration", description: "Configuration similarity after documented protection signals." },
  history: { label: "Historical issue", description: "Similarity to earlier support issues for this client." },
  semantic: { label: "Semantic evidence", description: "Retrieved evidence similarity for the candidate implementation." },
};

function bandLabel(value?: string) {
  return (value || "UNASSESSED").replaceAll("_", " ");
}

function technicalVerdictLabel(value?: string | null) {
  const normalized = String(value || "").toUpperCase();
  if (normalized === "CHANGE_REVIEW_REQUIRED") return "CHANGE REQUIRED";
  if (normalized === "ALREADY_MATCHES") return "ALREADY MATCHES";
  if (normalized === "ALREADY_PROTECTED") return "ALREADY PROTECTED";
  if (normalized === "EVIDENCE_RECONCILIATION_REQUIRED") return "RECONCILE EVIDENCE";
  return normalized ? bandLabel(normalized) : null;
}

function implementationActionState(investigation: any, impact: any): "active" | "muted" | "neutral" {
  const humanDecision = String(investigation?.human_decision?.decision || "").toUpperCase();
  if (humanDecision === "NOT_AFFECTED") return "muted";
  if (humanDecision === "AFFECTED") return "active";
  if (humanDecision === "NEEDS_MORE_INVESTIGATION") return "neutral";

  const technicalResult = String(investigation?.configuration_comparison?.technical_result || "").toUpperCase();
  if (technicalResult === "ALREADY_MATCHES" || technicalResult === "ALREADY_PROTECTED") return "muted";
  if (technicalResult === "CHANGE_REVIEW_REQUIRED") return "active";
  if (technicalResult === "EVIDENCE_RECONCILIATION_REQUIRED") return "neutral";

  return impact?.reported_source ? "active" : "neutral";
}

function implementationVerdict(investigation: any): string | null {
  const humanDecision = String(investigation?.human_decision?.decision || "").toUpperCase();
  if (humanDecision === "AFFECTED") return "AFFECTED";
  if (humanDecision === "NOT_AFFECTED") return "NOT AFFECTED";
  if (humanDecision === "NEEDS_MORE_INVESTIGATION") return "MORE INVESTIGATION";
  return technicalVerdictLabel(investigation?.configuration_comparison?.technical_result);
}

function nodeIcon(kind: RadarNodeData["kind"]) {
  if (kind === "issue") return ShieldAlert;
  if (kind === "method") return GitBranch;
  if (kind === "recall") return RotateCcw;
  return Network;
}

const RadarNode = memo(function RadarNode({ data }: NodeProps<CreedRadarNode>) {
  const Icon = nodeIcon(data.kind);
  const score = typeof data.score === "number" ? Math.round(data.score * 100) : null;
  const hasTarget = data.kind !== "issue" && data.kind !== "recall";
  const hasSource = data.kind !== "implementation";

  return (
    <div className={`creed-radar-node node-${data.kind} band-${String(data.band || "neutral").toLowerCase()} action-${data.actionState || "neutral"} ${data.selected ? "selected" : ""}`}>
      {hasTarget && <Handle className="creed-radar-handle" type="target" position={Position.Left} />}
      <div className="creed-radar-node-icon"><Icon size={15} strokeWidth={1.8} /></div>
      <div className="creed-radar-node-copy">
        <span>{data.eyebrow}</span>
        <strong>{data.label}</strong>
        {(data.verdict || data.band) && <small>{data.verdict || bandLabel(data.band)}</small>}
      </div>
      {score !== null && <div className="creed-radar-score"><b>{score}</b><span>PRIORITY</span></div>}
      {hasSource && <Handle className="creed-radar-handle" type="source" position={Position.Right} />}
    </div>
  );
});

const nodeTypes = { creedRadar: RadarNode };

function evidenceUnion(results: ImpactResult[]) {
  return Array.from(new Set(results.flatMap((result) => result.evidence_refs ?? [])));
}

function MiniLegend({ mode }: { mode: RadarMode }) {
  return (
    <div className="radar-legend" aria-label="Change Radar legend">
      {mode === "impact" ? (
        <>
          <span><i className="legend-dot source" />Reported source</span>
          <span><i className="legend-dot action" />Action required</span>
          <span><i className="legend-dot muted" />No change needed</span>
          <span><i className="legend-line active" />Active relationship</span>
          <span><i className="legend-line muted" />No-change relationship</span>
        </>
      ) : (
        <>
          <span><i className="legend-dot revoked" />Revoked knowledge</span>
          <span><i className="legend-dot queued" />Routed for review</span>
        </>
      )}
    </div>
  );
}

export function ChangeRadarWorkspace({ run, recall }: { run?: string; recall?: string }) {
  const router = useRouter();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [data, setData] = useState<any>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [bandFilter, setBandFilter] = useState<string>("ALL");
  const [evidenceDetail, setEvidenceDetail] = useState<EvidenceDocumentDetail | null>(null);
  const [evidenceBusy, setEvidenceBusy] = useState<string | null>(null);
  const [evidenceError, setEvidenceError] = useState("");

  const mode: RadarMode = recall ? "recall" : "impact";

  useEffect(() => {
    getHealth().then(setHealth);
    setError("");
    const request = recall
      ? getRecall(recall).then((result: any) => ({ results: result.cases, graph: result.graph, recall: result }))
      : run
        ? getImpact(run).then(async (impact) => {
            try {
              const investigations = await getRunInvestigations(run);
              return { ...impact, investigations: investigations?.results ?? [] };
            } catch {
              return { ...impact, investigations: [] };
            }
          })
        : Promise.resolve(null);
    request.then((result) => {
      setData(result);
      setSelectedNodeId(null);
    }).catch((cause) => setError(cause instanceof Error ? cause.message : String(cause)));
  }, [run, recall]);

  const impactResults: ImpactResult[] = mode === "impact" ? (data?.results ?? []) : [];
  const recallCases: RecallCase[] = mode === "recall" ? (data?.results ?? []) : [];
  const graph = data?.graph;
  const investigationRows: any[] = mode === "impact" ? (data?.investigations ?? []) : [];

  const investigationByImplementation = useMemo(() => {
    const map = new Map<string, any>();
    investigationRows.forEach((row: any) => map.set(String(row.implementation_id), row));
    return map;
  }, [investigationRows]);

  const resultByImplementation = useMemo(() => {
    const map = new Map<string, ImpactResult | RecallCase>();
    const rows = mode === "impact" ? impactResults : recallCases;
    rows.forEach((row: any) => map.set(String(row.implementation_id), row));
    return map;
  }, [mode, impactResults, recallCases]);

  const visibleImplementationIds = useMemo(() => {
    if (bandFilter === "ALL") return new Set(Array.from(resultByImplementation.keys()));
    const ids = new Set<string>();
    resultByImplementation.forEach((row: any, implementationId) => {
      const state = mode === "impact" ? row.impact_band : row.status;
      if (state === bandFilter) ids.add(implementationId);
    });
    return ids;
  }, [bandFilter, mode, resultByImplementation]);

  const graphNodes = useMemo<CreedRadarNode[]>(() => {
    if (!graph?.nodes) return [];
    const implementations = (graph.nodes as any[]).filter((node) => node.type === "implementation" && visibleImplementationIds.has(String(node.id).split(":")[1]));
    const nonImplementations = (graph.nodes as any[]).filter((node) => node.type !== "implementation");
    const rows = [...nonImplementations, ...implementations];
    const implIndex = new Map(implementations.map((node, index) => [String(node.id), index]));

    return rows.map((node: any) => {
      const kind = (node.type === "issue" || node.type === "method" || node.type === "recall") ? node.type : "implementation";
      const implementationId = kind === "implementation" ? String(node.id).split(":")[1] : null;
      const row: any = implementationId ? resultByImplementation.get(implementationId) : null;
      const investigation = implementationId ? investigationByImplementation.get(implementationId) : null;
      const band = mode === "impact" ? (row?.impact_band ?? node.band) : kind === "method" ? "REVOKED" : (row?.status ?? node.status);
      const score = mode === "impact" ? (row?.impact_score ?? node.score ?? null) : null;
      const actionState = kind === "implementation" && mode === "impact" ? implementationActionState(investigation, row) : "neutral";
      const verdict = kind === "implementation" && mode === "impact" ? implementationVerdict(investigation) : null;
      const y = kind === "implementation" ? ((implIndex.get(String(node.id)) ?? 0) - (implementations.length - 1) / 2) * 150 : 0;
      const x = kind === "issue" || kind === "recall" ? 0 : kind === "method" ? 360 : 760;
      return {
        id: String(node.id),
        type: "creedRadar",
        position: { x, y },
        draggable: false,
        selectable: true,
        data: {
          label: node.label ?? node.client_name ?? node.id,
          eyebrow: kind === "issue" ? "SOURCE ISSUE" : kind === "recall" ? "ASSURANCE RECALL" : kind === "method" ? (mode === "recall" ? "REVOKED METHOD" : "METHOD VERSION") : (row?.implementation_name ?? "IMPLEMENTATION"),
          kind,
          band,
          score,
          actionState,
          verdict,
          selected: selectedNodeId === String(node.id),
        },
      };
    });
  }, [graph, visibleImplementationIds, resultByImplementation, investigationByImplementation, mode, selectedNodeId]);

  const visibleNodeIds = useMemo(() => new Set(graphNodes.map((node) => node.id)), [graphNodes]);

  const graphEdges = useMemo<Edge[]>(() => {
    if (!graph?.edges) return [];
    const nodeMap = new Map(graphNodes.map((node) => [node.id, node]));
    return (graph.edges as any[])
      .filter((edge) => visibleNodeIds.has(String(edge.source)) && visibleNodeIds.has(String(edge.target)))
      .map((edge, index) => {
        const targetNode = nodeMap.get(String(edge.target));
        const isImplementationEdge = targetNode?.data.kind === "implementation";
        const targetAction = targetNode?.data.actionState || "neutral";
        const isMuted = mode === "impact" && isImplementationEdge && targetAction === "muted";
        const isActive = mode === "impact" && isImplementationEdge && targetAction === "active";
        const stroke = isMuted ? "#606b76" : isActive ? "#d7ad68" : "#76a9c2";
        return {
          id: `radar-edge-${index}-${edge.source}-${edge.target}`,
          source: String(edge.source),
          target: String(edge.target),
          label: String(edge.relationship || "").replaceAll("_", " "),
          type: "smoothstep",
          animated: false,
          className: isMuted ? "radar-edge-muted" : isActive ? "radar-edge-active" : "radar-edge-context",
          markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14, color: stroke },
          style: {
            stroke,
            strokeWidth: isActive ? 2.2 : 1.8,
            strokeDasharray: isMuted ? "7 6" : undefined,
            opacity: isMuted ? 0.62 : 0.92,
          },
          labelStyle: { fontSize: 11, letterSpacing: ".055em", fill: isMuted ? "#7f8b96" : undefined },
          labelBgPadding: [4, 2] as [number, number],
          labelBgBorderRadius: 2,
        } as Edge;
      });
  }, [graph, visibleNodeIds, graphNodes, mode]);

  const selectedNode = useMemo(() => graphNodes.find((node) => node.id === selectedNodeId) ?? null, [graphNodes, selectedNodeId]);
  const selectedImplementationId = selectedNode?.data.kind === "implementation" ? selectedNode.id.split(":")[1] : null;
  const selectedResult: any = selectedImplementationId ? resultByImplementation.get(selectedImplementationId) : null;

  const summary = useMemo(() => {
    if (mode === "impact") {
      const nonSource = impactResults.filter((result) => !result.reported_source);
      return {
        primary: { label: "CANDIDATES", value: nonSource.length, note: "Non-source implementations" },
        secondary: { label: "HIGH PRIORITY", value: nonSource.filter((result) => result.impact_band === "HIGH").length, note: "Investigate first" },
        tertiary: { label: "EVIDENCE REFS", value: evidenceUnion(impactResults).length, note: "Across scored candidates" },
      };
    }
    return {
      primary: { label: "ROUTED", value: recallCases.length, note: "Explicit adopters" },
      secondary: { label: "QUEUED", value: recallCases.filter((item) => item.status === "QUEUED").length, note: "Awaiting review" },
      tertiary: { label: "INTEGRITY", value: data?.recall?.integrity ?? "—", note: "Recall notice seal" },
    };
  }, [mode, impactResults, recallCases, data]);

  const filters = useMemo(() => mode === "impact"
    ? ["ALL", "REPORTED_SOURCE", "HIGH", "MEDIUM", "LOW"]
    : ["ALL", ...Array.from(new Set(recallCases.map((row) => row.status)))], [mode, recallCases]);

  const selectImplementation = useCallback((implementationId: string) => setSelectedNodeId(`implementation:${implementationId}`), []);

  async function openEvidence(id: string) {
    setEvidenceError("");
    setEvidenceBusy(id);
    try {
      setEvidenceDetail(await getDocument(id));
    } catch (cause) {
      setEvidenceError(cause instanceof Error ? cause.message : "DOCUMENT_DETAIL_FAILED");
    } finally {
      setEvidenceBusy(null);
    }
  }

  return (
    <AppShell health={health} active="Change Radar">
      <div className="page radar-r05">
        <header className="radar-r05-hero">
          <div>
            <h1>{mode === "recall" ? "Assurance Recall Radar" : "Change Radar"}</h1>
            <p className="subtitle">
              {mode === "recall"
                ? "Trace explicit adopters of revoked knowledge. Routing means review — not defect."
                : "See where delivery knowledge was reused and what needs investigation. Priority is not a verdict."}
            </p>
          </div>
          <div className="radar-hero-actions-r99-m06">
            <button className="secondary-btn radar-back-r99-m06" type="button" onClick={() => router.back()}>
              <ArrowLeft size={15} aria-hidden="true" />
              Back
            </button>
            <div className={`radar-mode-seal ${mode}`}>
              {mode === "impact" ? <Radar size={17} /> : <RotateCcw size={17} />}
              <div><span>RADAR MODE</span><strong>{mode === "impact" ? "IMPACT PRIORITY" : "ASSURANCE RECALL"}</strong></div>
            </div>
          </div>
        </header>

        {!run && !recall && (
          <section className="card radar-entry-empty">
            <Radar size={22} />
            <div><strong>No radar context selected</strong><p>Open Radar from a persisted analysis run or recall notice.</p></div>
          </section>
        )}

        {error && <div className="alert error" role="alert"><AlertTriangle size={15} />{error}</div>}

        {graph && (
          <>
            <section className="radar-glance-r26" aria-label="Radar signals">
              <VisualMetric
                icon={Network}
                label={summary.primary.label}
                value={summary.primary.value}
                meta={summary.primary.note}
                tone="info"
              />
              <VisualMetric
                icon={mode === "impact" ? ShieldAlert : SearchCheck}
                label={summary.secondary.label}
                value={summary.secondary.value}
                meta={summary.secondary.note}
                tone={mode === "impact" && Number(summary.secondary.value) > 0 ? "warn" : "neutral"}
              />
              <VisualMetric
                icon={mode === "impact" ? BookOpenCheck : ShieldCheck}
                label={summary.tertiary.label}
                value={summary.tertiary.value}
                meta={summary.tertiary.note}
                tone={mode === "impact" ? "ok" : "neutral"}
              />
              <div className="radar-glance-boundary-r26">
                <SignalChip icon={mode === "impact" ? ShieldAlert : ShieldCheck} tone={mode === "impact" ? "warn" : "info"}>
                  {mode === "impact" ? "Priority ≠ verdict" : "Route = review obligation"}
                </SignalChip>
              </div>
            </section>

            <section className="radar-stage-r26">
              <div className="radar-stage-head-r26">
                <div className="radar-stage-title-r26">
                  <div><Network size={16} /><strong>{mode === "impact" ? "Reuse map" : "Recall dependency map"}</strong></div>
                  <span>{graphNodes.length} nodes · {graphEdges.length} relationships</span>
                </div>
                <div className="radar-filter-group radar-filter-r26" role="group" aria-label={mode === "impact" ? "Impact band filter" : "Recall status filter"}>
                  <Filter size={14} aria-hidden="true" />
                  {filters.map((filter) => (
                    <button key={filter} type="button" className={bandFilter === filter ? "active" : ""} onClick={() => setBandFilter(filter)}>
                      {bandLabel(filter)}
                    </button>
                  ))}
                </div>
              </div>

              <div className="radar-flow-canvas radar-flow-canvas-r26">
                <ReactFlow
                  nodes={graphNodes}
                  edges={graphEdges}
                  nodeTypes={nodeTypes}
                  fitView
                  fitViewOptions={{ padding: 0.24, minZoom: 0.55, maxZoom: 1.15 }}
                  minZoom={0.35}
                  maxZoom={1.6}
                  nodesDraggable={false}
                  nodesConnectable={false}
                  elementsSelectable
                  onNodeClick={(_, node) => setSelectedNodeId(node.id)}
                  onPaneClick={() => setSelectedNodeId(null)}
                  colorMode="dark"
                  proOptions={{ hideAttribution: true }}
                >
                  <Background gap={30} size={1} />
                  <MiniMap
                    pannable
                    zoomable
                    nodeStrokeWidth={2}
                    nodeColor={(node) => {
                      const nodeData = node.data as RadarNodeData;
                      if (nodeData?.actionState === "muted") return "#59636e";
                      if (nodeData?.actionState === "active") return "#d7ad68";
                      const band = String(nodeData?.band || "").toUpperCase();
                      if (band === "REVOKED") return "#e87878";
                      if (band === "QUEUED") return "#e8b85f";
                      return "#5aa2ff";
                    }}
                  />
                  <Controls showInteractive={false} />
                </ReactFlow>
              </div>

              <div className="radar-stage-foot-r26">
                <span className="radar-select-hint-r26"><CircleDot size={13} />{selectedNode ? "Selection ready to inspect" : "Select a node to inspect"}</span>
                <ProgressiveDisclosure label="Legend" meta={mode === "impact" ? "4 states" : "2 states"}>
                  <MiniLegend mode={mode} />
                </ProgressiveDisclosure>
              </div>

              {selectedNode && (
                <section className="radar-selection-r26" aria-label={`Selected node ${selectedNode.data.label}`}>
                  <div className="radar-selection-head-r26">
                    <div>
                      <span>{selectedNode.data.eyebrow}</span>
                      <h2>{selectedNode.data.label}</h2>
                    </div>
                    <button type="button" className="icon-btn" onClick={() => setSelectedNodeId(null)} aria-label="Clear selected node"><X size={16} /></button>
                  </div>

                  {selectedNode.data.kind !== "implementation" && (
                    <div className="radar-context-r26">
                      <SignalChip icon={nodeIcon(selectedNode.data.kind)} tone={selectedNode.data.kind === "recall" ? "warn" : "info"}>{bandLabel(selectedNode.data.band)}</SignalChip>
                      <p>{selectedNode.data.kind === "issue" ? "Human-supplied source of this blast-radius analysis." : selectedNode.data.kind === "recall" ? "Human-authorised recall that initiated dependency routing." : mode === "impact" ? "Governed method version reused across candidate implementations." : "Revoked method version whose adopters require review."}</p>
                    </div>
                  )}

                  {selectedNode.data.kind === "implementation" && mode === "impact" && selectedResult && (
                    <div className="radar-selection-grid-r26">
                      <div className="radar-priority-r26">
                        <span>INVESTIGATION PRIORITY</span>
                        <strong>{Math.round(selectedResult.impact_score * 100)}</strong>
                        <SignalChip tone={selectedResult.impact_band === "HIGH" ? "bad" : selectedResult.impact_band === "MEDIUM" ? "warn" : "ok"}>{bandLabel(selectedResult.impact_band)}</SignalChip>
                        <small>Not a final affected / not-affected decision.</small>
                      </div>

                      <div className="radar-why-r26">
                        <div className="radar-mini-title-r26"><Filter size={13} /><span>WHY</span></div>
                        {(selectedResult.explanation ?? []).map((item: any) => {
                          const meta = SIGNAL_LABELS[item.signal] ?? { label: item.signal, description: "Deterministic impact signal." };
                          const contribution = Math.round(Number(item.contribution || 0) * 100);
                          return (
                            <div className="radar-signal-r26" key={item.signal} title={meta.description}>
                              <div><strong>{meta.label}</strong><b>+{contribution}</b></div>
                              <div className="radar-signal-track-r26"><i style={{ width: `${Math.min(100, Math.max(0, Number(item.value || 0) * 100))}%` }} /></div>
                            </div>
                          );
                        })}
                      </div>

                      <div className="radar-proof-r26">
                        <div className="radar-mini-title-r26"><BookOpenCheck size={13} /><span>PROOF</span></div>
                        <strong>{(selectedResult.evidence_refs ?? []).length}</strong>
                        <span>evidence refs</span>
                        <ProgressiveDisclosure label="Inspect evidence" meta={`${(selectedResult.evidence_refs ?? []).length} refs`}>
                          {(selectedResult.evidence_refs ?? []).length === 0 ? <p className="radar-inline-empty">No evidence references attached to this score.</p> : (
                            <div className="radar-evidence-list radar-evidence-list-r26">
                              {(selectedResult.evidence_refs ?? []).map((id: string) => (
                                <button key={id} type="button" onClick={() => openEvidence(id)} disabled={evidenceBusy === id}>
                                  <FileText size={13} /><span>{id}</span><ArrowRight size={13} />
                                </button>
                              ))}
                            </div>
                          )}
                        </ProgressiveDisclosure>
                      </div>
                    </div>
                  )}

                  {selectedNode.data.kind === "implementation" && mode === "recall" && selectedResult && (
                    <div className="radar-recall-selection-r26">
                      <VisualMetric icon={SearchCheck} label="Review obligation" value={bandLabel(selectedResult.status)} meta="Explicit adopter" tone="warn" />
                      <VisualMetric icon={Network} label="Client" value={selectedResult.client_name ?? "—"} meta={selectedResult.implementation_name ?? "Implementation"} />
                      <VisualMetric icon={ShieldCheck} label="Investigation" value={selectedResult.investigation_id ?? "—"} meta="Governed review case" tone="info" />
                      <ProgressiveDisclosure label="Dependency proof" meta="Local A-BOM">
                        <dl className="radar-definition-list radar-definition-r26">
                          <div><dt>Dependency edge</dt><dd>{selectedResult.dependency_edge_id ?? "—"}</dd></div>
                          <div><dt>Meaning</dt><dd>Explicit USES_METHOD_VERSION dependency. Routing creates a review obligation, not a defect verdict.</dd></div>
                        </dl>
                      </ProgressiveDisclosure>
                    </div>
                  )}
                </section>
              )}
            </section>

            <section className="radar-ledger-min-r26">
              <ProgressiveDisclosure
                label={mode === "impact" ? "Implementation list" : "Routed adopters"}
                meta={mode === "impact" ? `${impactResults.length} scored` : `${recallCases.length} routed`}
              >
                <div className="radar-ledger-table radar-ledger-table-r26">
                  {(mode === "impact" ? impactResults : recallCases).map((row: any, index: number) => {
                    const state = mode === "impact" ? row.impact_band : row.status;
                    const filteredOut = bandFilter !== "ALL" && state !== bandFilter;
                    if (filteredOut) return null;
                    return (
                      <button key={row.id ?? row.implementation_id} type="button" className={`radar-ledger-row ${selectedImplementationId === String(row.implementation_id) ? "selected" : ""}`} onClick={() => selectImplementation(String(row.implementation_id))}>
                        <span className="radar-ledger-rank">{String(index + 1).padStart(2, "0")}</span>
                        <span className="radar-ledger-client" data-label="Client / implementation"><strong>{row.client_name ?? "Unknown client"}</strong><small>{row.implementation_name ?? "Implementation"}</small></span>
                        <span className={`radar-band band-${String(state || "neutral").toLowerCase()}`} data-label={mode === "impact" ? "Priority band" : "Recall state"}>{bandLabel(state)}</span>
                        {mode === "impact" ? <span className="radar-ledger-score" data-label="Priority score"><b>{Math.round(Number(row.impact_score || 0) * 100)}</b><small>priority</small></span> : <span className="radar-ledger-score" data-label="Review obligation"><SearchCheck size={15} /><small>review</small></span>}
                        <ArrowRight size={14} />
                      </button>
                    );
                  })}
                </div>
              </ProgressiveDisclosure>
            </section>
          </>
        )}
      </div>

      {evidenceDetail && (
        <div className="document-modal-backdrop" role="presentation" onMouseDown={() => setEvidenceDetail(null)}>
          <section className="document-modal card" role="dialog" aria-modal="true" aria-label={`Evidence document ${evidenceDetail.title}`} onMouseDown={(event) => event.stopPropagation()}>
            <div className="document-modal-head">
              <div><span>{evidenceDetail.document_type} · {evidenceDetail.source}</span><h2>{evidenceDetail.title}</h2><p>{evidenceDetail.original_filename ?? evidenceDetail.id} · SHA-256 {evidenceDetail.content_hash.slice(0, 16)}…</p></div>
              <button className="ghost-btn" type="button" onClick={() => setEvidenceDetail(null)}>Close</button>
            </div>
            <div className="document-preview"><div className="preview-label">EXTRACTED EVIDENCE · {evidenceDetail.char_count.toLocaleString()} CHARACTERS</div><pre>{evidenceDetail.extracted_text}</pre></div>
          </section>
        </div>
      )}
      {evidenceError && <div className="radar-toast-error" role="alert"><AlertTriangle size={14} /><span>{evidenceError}</span><button type="button" onClick={() => setEvidenceError("")} aria-label="Dismiss evidence error"><X size={13} /></button></div>}
    </AppShell>
  );
}
