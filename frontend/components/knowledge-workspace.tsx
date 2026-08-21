"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowUpRight,
  BookOpenCheck,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  Copy,
  Database,
  File,
  FileCheck2,
  FileCode2,
  FileSearch2,
  FileText,
  Filter,
  Fingerprint,
  HardDrive,
  Hash,
  Layers3,
  Library,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  UploadCloud,
  X,
  XCircle,
} from "lucide-react";
import {
  EvidenceDocument,
  EvidenceDocumentDetail,
  getDocument,
  getDocumentOriginalUrl,
  getDocuments,
  uploadDocument,
} from "@/lib/api";
import { ProgressiveDisclosure, SignalChip, VisualMetric } from "@/components/visual-primitives";

const ALLOWED = ".pdf,.docx,.txt,.md,.json";
type WorkspaceMode = "find" | "upload";

function prettyBytes(value: number | null) {
  if (value === null) return "—";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function sourceLabel(value: string) {
  if (value === "LOCAL_DEMO") return "LOCAL REPOSITORY";
  return value.replaceAll("_", " ");
}

function docIcon(type: string) {
  if (type === "JSON") return FileCode2;
  if (type === "TXT" || type === "MARKDOWN") return FileText;
  return File;
}

function statusClass(value: string) {
  const normalized = value.toUpperCase();
  if (["INDEXED", "PARSED", "READY", "COMPLETED"].includes(normalized)) return "ok";
  if (["FAILED", "ERROR", "REJECTED"].includes(normalized)) return "bad";
  return "warn";
}


function previewKind(detail: EvidenceDocumentDetail): "pdf" | "text" | "docx" | "binary" {
  const mime=(detail.mime_type??"").toLowerCase();
  const name=(detail.original_filename??"").toLowerCase();
  if (mime==="application/pdf" || name.endsWith(".pdf")) return "pdf";
  if (mime.startsWith("text/") || mime==="application/json" || /\.(txt|md|json)$/.test(name)) return "text";
  if (mime==="application/vnd.openxmlformats-officedocument.wordprocessingml.document" || name.endsWith(".docx")) return "docx";
  return "binary";
}

export function KnowledgeSourcePreview({detail,onClose}:{detail:EvidenceDocumentDetail;onClose:()=>void}) {
  const [activeView,setActiveView]=useState<"original"|"extracted">("original");
  const [blobUrl,setBlobUrl]=useState<string|null>(null);
  const [rawText,setRawText]=useState<string|null>(null);
  const [error,setError]=useState<string|null>(null);
  const [verified,setVerified]=useState(false);
  const kind=previewKind(detail);
  useEffect(()=>{
    const controller=new AbortController(); let local:string|null=null;
    setActiveView("original"); setBlobUrl(null); setRawText(null); setError(null); setVerified(false);
    void fetch(getDocumentOriginalUrl(detail.id),{cache:"no-store",signal:controller.signal}).then(async r=>{
      if(!r.ok) throw new Error(`ORIGINAL_SOURCE_${r.status}`);
      const ok=r.headers.get("X-CREED-Original-Verified");
      const hash=r.headers.get("X-CREED-Content-SHA256");
      if(ok!=="true" || !hash || hash.toLowerCase()!==detail.content_hash.toLowerCase()) throw new Error("ORIGINAL_SOURCE_VERIFICATION_FAILED");
      const blob=await r.blob(); setVerified(true);
      if(kind==="text") setRawText(await blob.text()); else { local=URL.createObjectURL(blob); setBlobUrl(local); }
    }).catch(e=>{ if(!(e instanceof DOMException && e.name==="AbortError")) setError(e instanceof Error?e.message:"ORIGINAL_SOURCE_UNAVAILABLE") });
    return ()=>{controller.abort(); if(local) URL.revokeObjectURL(local)};
  },[detail.id,detail.content_hash,kind]);
  useEffect(()=>{const h=(e:KeyboardEvent)=>{if(e.key==="Escape")onClose()};window.addEventListener("keydown",h);return()=>window.removeEventListener("keydown",h)},[onClose]);
  return <div className="knowledge-preview-layer-r98-m08" onMouseDown={onClose}>
    <section className="knowledge-preview-modal-r98-m08" role="dialog" aria-modal="true" onMouseDown={e=>e.stopPropagation()}>
      <header><div><span>SOURCE PREVIEW</span><h2>{detail.title}</h2><p>{detail.original_filename??detail.document_type}</p></div><button type="button" onClick={onClose}><X size={16}/>Close</button></header>
      <div className="knowledge-preview-meta-r98-m08"><span>{detail.document_type}{detail.version?` · v${detail.version}`:""}</span><span>{sourceLabel(detail.source)}</span><span className="ok"><ShieldCheck size={13}/>{verified?"SHA-256 verified":"Verifying original"}</span></div>
      <div className="knowledge-preview-tabs-r98-m09" role="tablist" aria-label="Source preview mode">
        <button type="button" role="tab" aria-selected={activeView==="original"} className={activeView==="original"?"active":""} onClick={()=>setActiveView("original")}><Fingerprint size={13}/>Original preview</button>
        <button type="button" role="tab" aria-selected={activeView==="extracted"} className={activeView==="extracted"?"active":""} onClick={()=>setActiveView("extracted")}><FileSearch2 size={13}/>Extracted text</button>
      </div>
      <div className="knowledge-preview-body-r98-m08">
        {activeView==="extracted" ? <div className="knowledge-preview-extracted-r98-m09"><div className="knowledge-preview-extracted-head-r98-m09"><span>EXTRACTED TEXT</span><small>Parser-derived representation used for indexing and retrieval.</small></div><pre>{detail.extracted_text}</pre></div> : error ? <div className="knowledge-preview-state-r98-m08 bad"><CircleAlert size={16}/>{error.replaceAll("_"," ")}</div> : !verified ? <div className="knowledge-preview-state-r98-m08">Verifying and loading original stored file…</div> : kind==="pdf" && blobUrl ? <iframe src={`${blobUrl}#view=FitH`} title={`Original PDF — ${detail.title}`} /> : kind==="text" && rawText!=null ? <pre>{rawText}</pre> : kind==="docx" && blobUrl ? <div className="knowledge-preview-docx-r98-m08"><FileText size={28}/><strong>Verified original DOCX</strong><p>Word layout is not browser-native. CREED verified the original bytes. Use Extracted text for a readable parser-derived representation.</p><a href={blobUrl} target="_blank" rel="noreferrer"><ArrowUpRight size={14}/>Open original file</a></div> : blobUrl ? <div className="knowledge-preview-docx-r98-m08"><File size={28}/><strong>Verified original file</strong><a href={blobUrl} target="_blank" rel="noreferrer"><ArrowUpRight size={14}/>Open original file</a></div> : null}
      </div>
      <footer><Fingerprint size={13}/><code>{detail.content_hash}</code></footer>
    </section>
  </div>;
}

export function KnowledgeWorkspace({ initialDocuments }: { initialDocuments: EvidenceDocument[] }) {
  const [documents, setDocuments] = useState(initialDocuments);
  const [mode, setMode] = useState<WorkspaceMode>("find");
  const [selected, setSelected] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [version, setVersion] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{kind:"ok"|"error"; text:string}|null>(null);
  const [detail, setDetail] = useState<EvidenceDocumentDetail | null>(null);
  const [detailBusy, setDetailBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [registryQuery, setRegistryQuery] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [versionFilter, setVersionFilter] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const totalBytes = useMemo(() => documents.reduce((sum, doc) => sum + (doc.file_size ?? 0), 0), [documents]);
  const sources = useMemo(() => Array.from(new Set(documents.map(d=>d.source))).sort(), [documents]);
  const types = useMemo(() => Array.from(new Set(documents.map(d=>d.document_type))).sort(), [documents]);
  const versions = useMemo(() => Array.from(new Set(documents.map(d=>d.version).filter((v): v is string => Boolean(v)))).sort(), [documents]);
  const indexedChunks = useMemo(() => documents.reduce((sum, doc) => sum + doc.chunk_count, 0), [documents]);
  const indexedDocuments = useMemo(() => documents.filter(d => d.index_status.toUpperCase() === "INDEXED").length, [documents]);
  const degradedDocuments = useMemo(() => documents.filter(d => d.embedding_degraded).length, [documents]);
  const activeFilterCount = [sourceFilter, typeFilter, versionFilter].filter(Boolean).length;
  const registryDocuments = useMemo(() => {
    const term = registryQuery.trim().toLowerCase();
    return documents.filter(doc => {
      const textMatch = !term || [doc.title, doc.original_filename, doc.document_type, doc.version, sourceLabel(doc.source)]
        .filter(Boolean).join(" ").toLowerCase().includes(term);
      return textMatch
        && (!sourceFilter || doc.source === sourceFilter)
        && (!typeFilter || doc.document_type === typeFilter)
        && (!versionFilter || doc.version === versionFilter);
    });
  }, [documents, registryQuery, sourceFilter, typeFilter, versionFilter]);

  async function openDocument(id: string) {
    setDetailBusy(true);
    setMessage(null);
    try {
      setDetail(await getDocument(id));
      setPreviewOpen(true);
      setCopied(false);
    } catch {
      setMessage({kind:"error", text:"DOCUMENT_DETAIL_FAILED"});
    } finally {
      setDetailBusy(false);
    }
  }

  async function copyHash() {
    if (!detail?.content_hash || !navigator.clipboard) return;
    await navigator.clipboard.writeText(detail.content_hash);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  async function submit() {
    if (!selected || busy) return;
    setBusy(true);
    setMessage(null);
    const form = new FormData();
    form.set("file", selected);
    form.set("source", "LOCAL_DEMO");
    if (title.trim()) form.set("title", title.trim());
    if (version.trim()) form.set("version", version.trim());
    try {
      const created = await uploadDocument(form);
      setDocuments(await getDocuments());
      setSelected(null);
      setTitle("");
      setVersion("");
      if (inputRef.current) inputRef.current.value = "";
      setMessage({kind:"ok", text:`${created.title} parsed, sealed and indexed · ${created.char_count.toLocaleString()} characters extracted`});
      setDetail(created);
    } catch (error) {
      setMessage({kind:"error", text:error instanceof Error ? error.message : "UPLOAD_FAILED"});
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page knowledge-page-r06 knowledge-page-r27">
      <header className="knowledge-hero-r06 knowledge-hero-r27">
        <div>
          <h1>Evidence Repository</h1>
          <p className="subtitle">Browse and upload governed source evidence with provenance intact.</p>
        </div>
        <span className={`editorial-meta-r71 ${documents.length ? "tone-ok" : "tone-warn"}`}>
          <HardDrive size={14} aria-hidden="true" />
          LOCAL REPOSITORY · {documents.length ? "READY" : "EMPTY"}
        </span>
      </header>

      <nav className="knowledge-command-r27" aria-label="Evidence repository modes">
        <button className={mode === "find" ? "active" : ""} type="button" onClick={()=>setMode("find")}>
          <Library size={17}/><span>Repository</span>
        </button>
        <button className={mode === "upload" ? "active" : ""} type="button" onClick={()=>setMode("upload")}>
          <UploadCloud size={17}/><span>Upload</span>
        </button>
      </nav>

      <section className="knowledge-glance-r27" aria-label="Repository signals">
        <VisualMetric icon={Database} label="Documents" value={documents.length} meta={`${indexedDocuments} indexed`} tone="info" />
        <VisualMetric icon={Layers3} label="Chunks" value={indexedChunks.toLocaleString()} meta="retrievable" />
        <VisualMetric icon={Sparkles} label="Embeddings" value={degradedDocuments ? `${degradedDocuments} degraded` : "Local"} meta={degradedDocuments ? "fallback present" : "primary path"} tone={degradedDocuments ? "warn" : "ok"} />
      </section>

      {message && <div className={`knowledge-message-r06 ${message.kind}`}>
        {message.kind === "ok" ? <CheckCircle2 size={15}/> : <XCircle size={15}/>}<span>{message.text}</span>
      </div>}

      {mode === "find" && <main className="knowledge-find-r27 knowledge-find-r98-m07">
        <section className="knowledge-library-r98-m07" aria-label="Evidence repository documents">
          <div className="knowledge-library-head-r98-m07">
            <div>
              <span>REPOSITORY</span>
              <h2>Evidence documents</h2>
            </div>
            <span className="knowledge-library-count-r98-m07">{registryDocuments.length}/{documents.length}</span>
          </div>
          <div className="knowledge-library-tools-r98-m07">
            <div className="registry-search-r06 knowledge-library-search-r98-m07"><Search size={14}/><input value={registryQuery} onChange={e=>setRegistryQuery(e.target.value)} placeholder="Filter documents…" /></div>
            <button type="button" className={`secondary-btn compact ${showFilters ? "active" : ""}`} aria-expanded={showFilters} onClick={()=>setShowFilters(v=>!v)}>
              <SlidersHorizontal size={14}/> Filters {activeFilterCount ? <b>{activeFilterCount}</b> : null}
            </button>
          </div>
          {showFilters && <div className="knowledge-filter-row-r06 knowledge-filters-r27 knowledge-library-filters-r98-m07">
            <Filter size={13}/>
            <label><span>Source</span><select value={sourceFilter} onChange={e=>setSourceFilter(e.target.value)}><option value="">All sources</option>{sources.map(v=><option key={v} value={v}>{sourceLabel(v)}</option>)}</select></label>
            <label><span>Type</span><select value={typeFilter} onChange={e=>setTypeFilter(e.target.value)}><option value="">All types</option>{types.map(v=><option key={v} value={v}>{v}</option>)}</select></label>
            <label><span>Version</span><select value={versionFilter} onChange={e=>setVersionFilter(e.target.value)}><option value="">All versions</option>{versions.map(v=><option key={v} value={v}>{v}</option>)}</select></label>
          </div>}
          {registryDocuments.length === 0 ? <div className="knowledge-library-empty-r98-m07"><Library size={20}/><strong>No matching documents</strong></div> : <div className="knowledge-library-list-r98-m07">
            {registryDocuments.map((doc,index) => {
              const Icon = docIcon(doc.document_type);
              return <button key={doc.id} type="button" className="knowledge-library-row-r98-m07" onClick={()=>openDocument(doc.id)} disabled={detailBusy}>
                <span className="knowledge-library-index-r98-m07">{String(index+1).padStart(2,"0")}</span>
                <span className="knowledge-library-icon-r98-m07"><Icon size={15}/></span>
                <span className="knowledge-library-copy-r98-m07"><strong>{doc.title}</strong><small>{doc.document_type}{doc.version ? ` · v${doc.version}` : ""} · {sourceLabel(doc.source)}</small></span>
                <span className={`knowledge-library-state-r98-m07 ${statusClass(doc.index_status)}`}>{doc.index_status}</span>
                <ChevronRight size={15} aria-hidden="true"/>
              </button>;
            })}
          </div>}
        </section>

      </main>}

      {mode === "upload" && <main className="knowledge-ingest-r27">
        <section className="card ingest-min-r27">
          <div className="ingest-min-head-r27">
            <div><span>NEW EVIDENCE</span><h2>Upload project evidence</h2></div>
            <SignalChip icon={FileCheck2}>PDF · DOCX · TXT · MD · JSON</SignalChip>
          </div>

          <div className="ingest-min-grid-r27">
            <div className={`dropzone-r06 dropzone-r27 ${selected ? "selected" : ""}`}>
              <input ref={inputRef} hidden type="file" accept={ALLOWED} onChange={e=>{setSelected(e.target.files?.[0]??null);setMessage(null)}} />
              <UploadCloud size={30}/>
              <strong>{selected ? selected.name : "Choose evidence"}</strong>
              <span>{selected ? prettyBytes(selected.size) : "Supported files · maximum 20 MB"}</span>
              <div className="dropzone-actions-r06">
                <button type="button" className="secondary-btn compact" onClick={()=>inputRef.current?.click()}>{selected ? "Replace" : "Choose file"}</button>
                {selected && <button type="button" className="ghost-btn compact" onClick={()=>{setSelected(null);if(inputRef.current)inputRef.current.value=""}}><X size={13}/> Remove</button>}
              </div>
            </div>

            <div className="ingest-fields-r06 ingest-fields-r27">
              <label><span>TITLE <em>OPTIONAL</em></span><input value={title} onChange={e=>setTitle(e.target.value)} placeholder="Defaults to filename" /></label>
              <label><span>VERSION <em>OPTIONAL</em></span><input value={version} onChange={e=>setVersion(e.target.value)} placeholder="e.g. 1.4" /></label>
              <label><span>SOURCE</span><div className="locked-field-r06"><HardDrive size={13}/><strong>LOCAL REPOSITORY</strong><small>Configured evidence source</small></div></label>
            </div>
          </div>

          <div className="ingest-flow-r27" aria-label="Upload processing stages">
            <div><FileSearch2 size={17}/><span>Parse</span></div><ChevronRight size={14}/>
            <div><Fingerprint size={17}/><span>Seal</span></div><ChevronRight size={14}/>
            <div><Layers3 size={17}/><span>Chunk</span></div><ChevronRight size={14}/>
            <div><Database size={17}/><span>Index</span></div>
          </div>

          <div className="ingest-submit-r27">
            <SignalChip icon={ShieldCheck}>Human-supplied evidence</SignalChip>
            <button type="button" className="primary-btn" disabled={!selected || busy} onClick={submit}>{busy ? "Parsing & indexing…" : "Upload evidence"}</button>
          </div>

          <ProgressiveDisclosure label="Upload rules" meta="Provenance & validation">
            <div className="ingest-rules-r27">
              <div><Fingerprint size={15}/><span>Content is sealed with SHA-256.</span></div>
              <div><FileSearch2 size={15}/><span>Unsupported or unparseable files do not enter the registry.</span></div>
              <div><Database size={15}/><span>Duplicate source evidence is rejected by the backend.</span></div>
              <p>Upload stores source material. It does not approve or validate the document's business meaning.</p>
            </div>
          </ProgressiveDisclosure>

          {detail && message?.kind === "ok" && <div className="ingest-complete-r27"><button className="secondary-btn" type="button" onClick={()=>setPreviewOpen(true)}><FileSearch2 size={14}/> Preview uploaded source</button></div>}
        </section>
      </main>}

      {previewOpen && detail && <KnowledgeSourcePreview detail={detail} onClose={()=>setPreviewOpen(false)} />}
    </div>
  );
}
