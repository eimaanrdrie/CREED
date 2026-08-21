"use client";

import { useMemo, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  Check,
  ClipboardCheck,
  FileText,
  Paperclip,
  ShieldAlert,
  Tag,
  Ticket,
  Upload,
  X,
} from "lucide-react";
import { createIssue, uploadDocument, type ClientRecord, type IssueCreatePayload } from "@/lib/api";
import { ProgressiveDisclosure, SignalChip } from "@/components/visual-primitives";

const STEPS = [
  { id: 1, label: "Context", icon: Building2 },
  { id: 2, label: "Observation", icon: FileText },
  { id: 3, label: "Classify", icon: Tag },
  { id: 4, label: "Review", icon: ClipboardCheck },
] as const;

function humanize(value: string) {
  return value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, letter => letter.toUpperCase());
}

function severityTone(severity: string): "neutral" | "warn" | "bad" | "ok" {
  if (["CRITICAL", "HIGH"].includes(severity)) return "bad";
  if (severity === "MEDIUM") return "warn";
  if (severity === "LOW") return "ok";
  return "neutral";
}

export type IssueCapsuleInitialValues = {
  ticket?: string;
  clientId?: string;
  title?: string;
  description?: string;
  issueType?: NonNullable<IssueCreatePayload["issue_type"]>;
  severity?: NonNullable<IssueCreatePayload["severity"]>;
  demoLoaded?: boolean;
};

export function IssueCapsuleForm({ clients, initialValues }: { clients: ClientRecord[]; initialValues?: IssueCapsuleInitialValues }) {
  const [step, setStep] = useState(1);
  const [maxStep, setMaxStep] = useState(1);
  const [ticket, setTicket] = useState(initialValues?.ticket ?? "");
  const [clientId, setClientId] = useState(initialValues?.clientId ?? "");
  const [title, setTitle] = useState(initialValues?.title ?? "");
  const [description, setDescription] = useState(initialValues?.description ?? "");
  const [issueType, setIssueType] = useState<NonNullable<IssueCreatePayload["issue_type"]>>(initialValues?.issueType ?? "UNKNOWN");
  const [severity, setSeverity] = useState<NonNullable<IssueCreatePayload["severity"]>>(initialValues?.severity ?? "UNKNOWN");
  const [files, setFiles] = useState<File[]>([]);
  const [createdIssueId, setCreatedIssueId] = useState<string | null>(null);
  const [uploadedKeys, setUploadedKeys] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedClient = clients.find(client => client.id === clientId);
  const observationReady = useMemo(() => title.trim().length >= 4 && description.trim().length >= 8, [title, description]);
  const ready = observationReady;

  function next() {
    setError(null);
    if (step === 2 && !observationReady) {
      setError("Add a title and description before continuing.");
      return;
    }
    setStep(current => {
      const target = Math.min(4, current + 1);
      setMaxStep(previous => Math.max(previous, target));
      return target;
    });
  }

  function back() {
    setError(null);
    setStep(current => Math.max(1, current - 1));
  }

  async function submit() {
    if (!ready || busy) return;
    setBusy(true); setError(null);
    let issueId = createdIssueId;
    try {
      if (!issueId) {
        const issue = await createIssue({ external_ticket_id: ticket || null, client_id: clientId || null, title, description, issue_type: issueType, severity });
        issueId = issue.id;
        setCreatedIssueId(issueId);
      }
      for (const file of files) {
        const fileKey = `${file.name}:${file.size}:${file.lastModified}`;
        if (uploadedKeys.includes(fileKey)) continue;
        const form = new FormData();
        form.set("file", file);
        form.set("source", "ISSUE_ATTACHMENT");
        form.set("issue_id", issueId);
        form.set("title", file.name.replace(/\.[^.]+$/, ""));
        await uploadDocument(form);
        setUploadedKeys(previous => previous.includes(fileKey) ? previous : [...previous, fileKey]);
      }
      window.location.href = `/issues/${issueId}/analysis?run=1`;
    } catch (err) {
      setError(`${issueId ? "Issue is saved. " : ""}${err instanceof Error ? err.message : "ISSUE_SUBMISSION_FAILED"}`);
      setBusy(false);
    }
  }

  return (
    <div className="issue-intake-shell issue-intake-min-r24">
      <header className="issue-intake-header issue-intake-header-r24">
        <div>
          <h1>What changed?</h1>
          <p>Capture source facts. AI starts after save.</p>
          {initialValues?.demoLoaded ? <span className="demo-intake-note-r94m11">Judging rehearsal values loaded · review or edit the wording before Save & analyse.</span> : null}
        </div>
        <div className="issue-intake-boundary issue-boundary-r24"><ShieldAlert size={16} /><div><strong>Human source</strong><span>AI after save</span></div></div>
      </header>

      <nav className="issue-stepper issue-stepper-r24" aria-label="Issue intake progress">
        {STEPS.map(item => {
          const Icon = item.icon;
          const complete = step > item.id;
          const active = step === item.id;
          return <button type="button" key={item.id} className={`${active ? "active" : ""} ${complete ? "complete" : ""}`} onClick={() => item.id <= maxStep && setStep(item.id)} disabled={item.id > maxStep} aria-current={active ? "step" : undefined} aria-label={`${item.id}. ${item.label}`}>
            <span className="issue-step-icon">{complete ? <Check size={15} /> : <Icon size={15} />}</span>
            <strong>{item.label}</strong>
          </button>;
        })}
      </nav>

      <div className="issue-intake-grid issue-intake-grid-r24">
        <section className="card issue-intake-panel issue-intake-panel-r24">
          {step === 1 && <StepContext ticket={ticket} setTicket={setTicket} clientId={clientId} setClientId={setClientId} clients={clients} />}
          {step === 2 && <StepObservation title={title} setTitle={setTitle} description={description} setDescription={setDescription} />}
          {step === 3 && <StepClassification issueType={issueType} setIssueType={setIssueType} severity={severity} setSeverity={setSeverity} />}
          {step === 4 && <StepReview clientName={selectedClient?.name} ticket={ticket} title={title} description={description} issueType={issueType} severity={severity} files={files} setFiles={setFiles} />}

          {error && <div className="issue-form-alert" role="alert" aria-live="assertive"><ShieldAlert size={15} /><span>{error}</span></div>}

          <footer className="issue-intake-actions">
            <div>{step > 1 ? <button type="button" className="ghost-btn" onClick={back} disabled={busy}><ArrowLeft size={15} />Back</button> : <a className="ghost-btn" href="/issues"><ArrowLeft size={15} />Cancel</a>}</div>
            {step < 4 ? <button type="button" className="primary-btn" onClick={next}>Continue<ArrowRight size={15} /></button> : <button type="button" className="primary-btn" onClick={submit} disabled={!ready || busy}>{busy ? "Saving…" : "Save & analyse"}<ArrowRight size={15} /></button>}
          </footer>
        </section>

        <aside className="issue-intake-aside issue-intake-aside-r24">
          <section className="card issue-case-preview issue-case-preview-r24">
            <div className="issue-snapshot-r24">
              <span className={`issue-snapshot-severity-r24 tone-${severityTone(severity)}`}>{humanize(severity)}</span>
              <strong>{title.trim() || "Untitled case"}</strong>
              <small>{selectedClient?.name ?? "No client"}{ticket ? ` · ${ticket}` : ""}</small>
            </div>
            <div className="issue-snapshot-signals-r24">
              <SignalChip icon={Tag}>{humanize(issueType)}</SignalChip>
              <SignalChip icon={Paperclip} tone={files.length ? "info" : "neutral"}>{files.length} evidence</SignalChip>
            </div>
          </section>
          <ProgressiveDisclosure label="After save" meta="Qwen + evidence">
            <div className="issue-after-save-r24">
              <span><strong>1</strong>Save source</span>
              <span><strong>2</strong>Start analysis</span>
              <span><strong>3</strong>Human decides</span>
            </div>
          </ProgressiveDisclosure>
        </aside>
      </div>
    </div>
  );
}

function SectionIntro({ index, title, text }: { index: string; title: string; text: string }) {
  return <div className="issue-step-intro issue-step-intro-r24"><span>{index}</span><div><h2>{title}</h2><p>{text}</p></div></div>;
}

function StepContext({ ticket, setTicket, clientId, setClientId, clients }: { ticket: string; setTicket: (value: string) => void; clientId: string; setClientId: (value: string) => void; clients: ClientRecord[] }) {
  return <div className="issue-step-content"><SectionIntro index="01" title="Source context" text="Client and ticket, if known." /><div className="issue-field-grid two"><label className="issue-field"><span><Building2 size={14} />Client</span><select value={clientId} onChange={event => setClientId(event.target.value)}><option value="">Not selected</option>{clients.map(client => <option key={client.id} value={client.id}>{client.name}</option>)}</select><small>Optional</small></label><label className="issue-field"><span><Ticket size={14} />Ticket</span><input value={ticket} onChange={event => setTicket(event.target.value)} placeholder="SUP-2317" maxLength={120} /><small>Optional</small></label></div></div>;
}

function StepObservation({ title, setTitle, description, setDescription }: { title: string; setTitle: (value: string) => void; description: string; setDescription: (value: string) => void }) {
  return <div className="issue-step-content"><SectionIntro index="02" title="What happened?" text="Use the reporter's words." /><label className="issue-field"><span>Case title</span><input value={title} onChange={event => setTitle(event.target.value)} placeholder="Duplicate PTP event changes collection state" maxLength={240} /><small>{title.length}/240 · 4+ required</small></label><label className="issue-field issue-description-field"><span>Observation</span><textarea value={description} onChange={event => setDescription(event.target.value)} placeholder="Paste the support ticket, symptom, requested change or internal discovery…" rows={10} maxLength={20000} /><small>{description.length.toLocaleString()}/20,000 · 8+ required</small></label></div>;
}

function StepClassification({ issueType, setIssueType, severity, setSeverity }: { issueType: NonNullable<IssueCreatePayload["issue_type"]>; setIssueType: (value: NonNullable<IssueCreatePayload["issue_type"]>) => void; severity: NonNullable<IssueCreatePayload["severity"]>; setSeverity: (value: NonNullable<IssueCreatePayload["severity"]>) => void }) {
  return <div className="issue-step-content"><SectionIntro index="03" title="Classify" text="Human-reported labels only." /><div className="issue-classification-grid issue-classification-r24"><ChoiceGroup title="Reported as" value={issueType} options={["UNKNOWN", "BUG", "INCIDENT", "CHANGE_REQUEST", "ENHANCEMENT"]} onChange={value => setIssueType(value as NonNullable<IssueCreatePayload["issue_type"]>)} /><ChoiceGroup title="Severity" value={severity} options={["UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"]} onChange={value => setSeverity(value as NonNullable<IssueCreatePayload["severity"]>)} severity /></div></div>;
}

function ChoiceGroup({ title, value, options, onChange, severity = false }: { title: string; value: string; options: string[]; onChange: (value: string) => void; severity?: boolean }) {
  return <fieldset className="issue-choice-group issue-choice-r24"><legend>{title}</legend><div>{options.map(option => <button type="button" className={`${value === option ? "selected" : ""} ${severity ? `severity-choice-${option.toLowerCase()}` : ""}`} key={option} onClick={() => onChange(option)}><span>{humanize(option)}</span>{value === option && <Check size={14} />}</button>)}</div></fieldset>;
}

function AdditionalEvidenceControl({ files, setFiles }: { files: File[]; setFiles: (files: File[]) => void }) {
  return <ProgressiveDisclosure label="Attach additional evidence" meta={files.length ? `${files.length} queued` : "Optional"}>
    <div className="issue-additional-evidence-r98-m01">
      <p>Use only when this issue includes source material that is not already in the governed Evidence Repository.</p>
      <label className="issue-dropzone issue-dropzone-r24"><input hidden multiple type="file" accept=".pdf,.docx,.txt,.md,.json" onChange={event => { const incoming = Array.from(event.target.files ?? []); const seen = new Set(files.map(file => `${file.name}:${file.size}:${file.lastModified}`)); setFiles([...files, ...incoming.filter(file => !seen.has(`${file.name}:${file.size}:${file.lastModified}`))]); }} /><span className="issue-drop-icon"><Upload size={20} /></span><strong>Attach additional evidence</strong><small>PDF · DOCX · TXT · MD · JSON</small></label>
      {files.length > 0 && <div className="issue-evidence-staging"><div className="issue-evidence-staging-head"><span>Queued</span><strong>{files.length}</strong></div>{files.map((file, index) => <div className="issue-staged-file" key={`${file.name}-${file.lastModified}-${index}`}><FileText size={15} /><div><strong>{file.name}</strong><span>{Math.max(1, Math.round(file.size / 1024))} KB</span></div><button type="button" aria-label={`Remove ${file.name}`} onClick={() => setFiles(files.filter((_, itemIndex) => itemIndex !== index))}><X size={14} /></button></div>)}</div>}
    </div>
  </ProgressiveDisclosure>;
}

function StepReview({ clientName, ticket, title, description, issueType, severity, files, setFiles }: { clientName?: string; ticket: string; title: string; description: string; issueType: string; severity: string; files: File[]; setFiles: (files: File[]) => void }) {
  return <div className="issue-step-content"><SectionIntro index="04" title="Confirm source" text="Review the human-reported facts. CREED retrieves governed evidence after Save & analyse." /><div className="issue-review-sheet issue-review-r24"><div className="issue-review-title"><span className={`severity-badge severity-${severity.toLowerCase()}`}>{severity}</span><h2>{title || "Untitled issue"}</h2><p>{clientName ?? "No client"}{ticket ? ` · ${ticket}` : ""}</p><div className="issue-review-chips-r24"><SignalChip>{humanize(issueType)}</SignalChip>{files.length > 0 && <SignalChip icon={Paperclip} tone="info">{files.length} additional evidence</SignalChip>}</div></div><ProgressiveDisclosure label="Observation" meta={`${description.length.toLocaleString()} chars`}><div className="issue-review-observation-r24">{description || "No description supplied."}</div></ProgressiveDisclosure><AdditionalEvidenceControl files={files} setFiles={setFiles} /></div></div>;
}
