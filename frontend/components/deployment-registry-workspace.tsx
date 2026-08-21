"use client";

import { useMemo, useRef, useState, type FormEvent } from "react";
import {
  AlertCircle,
  CalendarClock,
  CheckCircle2,
  FileCheck2,
  Info,
  Plus,
  RefreshCw,
  Rocket,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";
import {
  createDeployment,
  type ClientRecord,
  type DeploymentCreatePayload,
  type DeploymentRecord,
  type EvidenceDocument,
  type ImplementationRecord,
} from "@/lib/api";

type Notice = { tone: "ok" | "bad" | "neutral"; text: string } | null;

type Environment = DeploymentCreatePayload["environment"];

const ENVIRONMENTS: Array<{ value: Environment; label: string; detail: string }> = [
  { value: "DEVELOPMENT", label: "Development", detail: "Engineering environment" },
  { value: "SIT", label: "SIT", detail: "System integration testing" },
  { value: "UAT", label: "UAT", detail: "User acceptance testing" },
  { value: "PRODUCTION", label: "Production", detail: "Live customer environment" },
  { value: "DR", label: "DR", detail: "Disaster recovery environment" },
];

function sortDeployments(items: DeploymentRecord[]) {
  return [...items].sort((a, b) => Date.parse(b.deployed_at) - Date.parse(a.deployed_at));
}

function friendlyError(error: unknown) {
  if (!(error instanceof Error)) return "Deployment could not be recorded.";
  const labels: Record<string, string> = {
    IMPLEMENTATION_NOT_FOUND: "The selected implementation no longer exists. Reload the registry and try again.",
    EVIDENCE_DOCUMENT_NOT_FOUND: "The selected evidence document no longer exists. Reload the registry and try again.",
    DEPLOYMENT_EVENT_ALREADY_EXISTS: "A deployment is already recorded for that implementation, environment and timestamp with different provenance.",
  };
  return labels[error.message] ?? `Deployment could not be recorded (${error.message}).`;
}

const UTC_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"] as const;

function twoDigits(value: number) {
  return String(value).padStart(2, "0");
}

function formatTimestamp(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  // Deployment provenance is stored in UTC. Format it manually so SSR and the
  // browser render byte-for-byte identical text regardless of locale/timezone.
  return `${twoDigits(date.getUTCDate())} ${UTC_MONTHS[date.getUTCMonth()]} ${date.getUTCFullYear()}, ${twoDigits(date.getUTCHours())}:${twoDigits(date.getUTCMinutes())} UTC`;
}

function shortHash(value: string | null) {
  if (!value) return "No content seal";
  return `${value.slice(0, 10)}…${value.slice(-8)}`;
}

export function DeploymentRegistryWorkspace({
  initialDeployments,
  implementations,
  clients,
  documents,
  loadError,
  catalogError,
}: {
  initialDeployments: DeploymentRecord[];
  implementations: ImplementationRecord[];
  clients: ClientRecord[];
  documents: EvidenceDocument[];
  loadError: boolean;
  catalogError: boolean;
}) {
  const [deployments, setDeployments] = useState(() => sortDeployments(initialDeployments));
  const [query, setQuery] = useState("");
  const [clientFilter, setClientFilter] = useState("ALL");
  const [environmentFilter, setEnvironmentFilter] = useState("ALL");
  const [showCreate, setShowCreate] = useState(false);
  const [implementationId, setImplementationId] = useState("");
  const [environment, setEnvironment] = useState<Environment | "">("");
  const [deployedAt, setDeployedAt] = useState("");
  const [deploymentReference, setDeploymentReference] = useState("");
  const [evidenceDocumentId, setEvidenceDocumentId] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);
  const implementationRef = useRef<HTMLSelectElement>(null);

  const selectedImplementation = useMemo(
    () => implementations.find(item => item.id === implementationId) ?? null,
    [implementationId, implementations],
  );

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return deployments.filter(item => {
      if (clientFilter !== "ALL" && item.client_id !== clientFilter) return false;
      if (environmentFilter !== "ALL" && item.environment !== environmentFilter) return false;
      if (!needle) return true;
      return [
        item.implementation_name,
        item.client_name,
        item.product_name,
        item.module_name,
        item.release_version,
        item.environment,
        item.deployment_reference ?? "",
        item.evidence_title ?? "",
        item.id,
      ].some(value => value.toLowerCase().includes(needle));
    });
  }, [deployments, query, clientFilter, environmentFilter]);

  const productionCount = deployments.filter(item => item.environment === "PRODUCTION" && item.status === "DEPLOYED").length;
  const representedClients = new Set(deployments.map(item => item.client_id)).size;
  const prerequisitesReady = !loadError && !catalogError && implementations.length > 0 && documents.length > 0;

  function resetForm() {
    setImplementationId("");
    setEnvironment("");
    setDeployedAt("");
    setDeploymentReference("");
    setEvidenceDocumentId("");
    setNotes("");
  }

  function openCreate() {
    if (!prerequisitesReady) return;
    setNotice(null);
    setShowCreate(true);
    window.requestAnimationFrame(() => implementationRef.current?.focus());
  }

  function closeCreate() {
    if (submitting) return;
    setShowCreate(false);
    resetForm();
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!implementationId || !environment || !deployedAt || !evidenceDocumentId) {
      setNotice({ tone: "bad", text: "Choose an implementation, environment, deployment time and supporting evidence." });
      return;
    }

    const date = new Date(deployedAt);
    if (Number.isNaN(date.getTime())) {
      setNotice({ tone: "bad", text: "Deployment time is not valid." });
      return;
    }

    setSubmitting(true);
    setNotice(null);
    try {
      const created = await createDeployment({
        implementation_id: implementationId,
        environment,
        deployed_at: date.toISOString(),
        deployment_reference: deploymentReference.trim() || null,
        evidence_document_id: evidenceDocumentId,
        notes: notes.trim() || null,
      });
      const existed = deployments.some(item => item.id === created.id);
      setDeployments(current => sortDeployments([
        ...current.filter(item => item.id !== created.id),
        created,
      ]));
      setNotice({
        tone: existed ? "neutral" : "ok",
        text: existed
          ? `${created.client_name} ${created.release_version} already has that ${created.environment} deployment recorded.`
          : `${created.client_name} ${created.release_version} was recorded in ${created.environment}.`,
      });
      setShowCreate(false);
      resetForm();
    } catch (error) {
      setNotice({ tone: "bad", text: friendlyError(error) });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page deployment-registry-r86">
      <div className="title-row deployment-registry-title-r86">
        <div>
          <h1>Releases &amp; deployments</h1>
          <p className="subtitle">Record where an implementation release was actually deployed, with explicit environment, timestamp and supporting evidence.</p>
          <div className="deployment-summary-r86" aria-label="Deployment registry summary">
            <span><strong>{deployments.length}</strong> deployment records</span>
            <span><strong>{productionCount}</strong> production</span>
            <span><strong>{representedClients}</strong> clients represented</span>
          </div>
        </div>
        {!showCreate && (
          <button className="primary-btn" type="button" onClick={openCreate} disabled={!prerequisitesReady}>
            <Plus size={16} aria-hidden="true" />Record deployment
          </button>
        )}
      </div>

      {loadError && (
        <div className="deployment-notice-r86 bad" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <div>
            <strong>Deployment registry unavailable</strong>
            <span>CREED could not load persisted deployment records. Verify the API and database, then retry.</span>
          </div>
          <button className="secondary-btn compact" type="button" onClick={() => window.location.reload()}>
            <RefreshCw size={14} aria-hidden="true" />Retry
          </button>
        </div>
      )}

      {!loadError && catalogError && (
        <div className="deployment-notice-r86 bad" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <div>
            <strong>Deployment prerequisites unavailable</strong>
            <span>Implementation or evidence catalogs could not be loaded. Existing deployment records remain visible, but new registration is disabled.</span>
          </div>
          <button className="secondary-btn compact" type="button" onClick={() => window.location.reload()}>
            <RefreshCw size={14} aria-hidden="true" />Retry
          </button>
        </div>
      )}

      {!loadError && !catalogError && implementations.length === 0 && (
        <div className="deployment-notice-r86 neutral" role="status">
          <Info size={16} aria-hidden="true" />
          <div>
            <strong>An implementation is required first</strong>
            <span>Create the client implementation identity before recording where a release was deployed.</span>
          </div>
          <a className="secondary-btn compact" href="/implementations">Open Implementations</a>
        </div>
      )}

      {!loadError && !catalogError && implementations.length > 0 && documents.length === 0 && (
        <div className="deployment-notice-r86 neutral" role="status">
          <Info size={16} aria-hidden="true" />
          <div>
            <strong>Supporting evidence is required</strong>
            <span>Upload a release note, change record or other deployment evidence before registering a deployment fact.</span>
          </div>
          <a className="secondary-btn compact" href="/knowledge">Open Evidence Repository</a>
        </div>
      )}

      {notice && (
        <div className={`deployment-notice-r86 ${notice.tone}`} role={notice.tone === "bad" ? "alert" : "status"}>
          {notice.tone === "ok" ? <CheckCircle2 size={16} aria-hidden="true" /> : notice.tone === "bad" ? <AlertCircle size={16} aria-hidden="true" /> : <Info size={16} aria-hidden="true" />}
          <span>{notice.text}</span>
          <button type="button" onClick={() => setNotice(null)} aria-label="Dismiss notification"><X size={14} aria-hidden="true" /></button>
        </div>
      )}

      {showCreate && prerequisitesReady && (
        <section className="deployment-create-r86" aria-labelledby="deployment-create-title-r86">
          <div className="deployment-create-head-r86">
            <div>
              <h2 id="deployment-create-title-r86">Record deployment</h2>
              <p>The release value is inherited from the selected implementation. CREED does not let this form invent a second release identity.</p>
            </div>
            <button className="icon-btn" type="button" onClick={closeCreate} disabled={submitting} aria-label="Close deployment form">
              <X size={16} aria-hidden="true" />
            </button>
          </div>

          {selectedImplementation && (
            <div className="deployment-lock-r86" role="status">
              <ShieldCheck size={16} aria-hidden="true" />
              <div>
                <span>RELEASE INHERITED FROM IMPLEMENTATION</span>
                <strong>{selectedImplementation.client_name} · {selectedImplementation.name} · {selectedImplementation.release_version}</strong>
                <small>{selectedImplementation.product_name} / {selectedImplementation.module_name}. Change the release in the Implementation Registry, not here.</small>
              </div>
            </div>
          )}

          <form className="deployment-create-form-r86" onSubmit={onSubmit} noValidate>
            <label className="deployment-field-r86">
              <span>Implementation <b>Required</b></span>
              <select ref={implementationRef} value={implementationId} onChange={event => setImplementationId(event.target.value)} disabled={submitting} required>
                <option value="">Select implementation</option>
                {implementations.map(item => (
                  <option value={item.id} key={item.id}>{item.client_name} · {item.name} · {item.release_version}</option>
                ))}
              </select>
              <small>Determines client, product, module and release.</small>
            </label>

            <label className="deployment-field-r86">
              <span>Environment <b>Required</b></span>
              <select value={environment} onChange={event => setEnvironment(event.target.value as Environment | "")} disabled={submitting} required>
                <option value="">Select environment</option>
                {ENVIRONMENTS.map(item => <option value={item.value} key={item.value}>{item.label} — {item.detail}</option>)}
              </select>
              <small>Where this release was deployed.</small>
            </label>

            <label className="deployment-field-r86">
              <span>Deployment time <b>Required</b></span>
              <input type="datetime-local" value={deployedAt} onChange={event => setDeployedAt(event.target.value)} disabled={submitting} required />
              <small>Converted to an ISO timestamp when persisted.</small>
            </label>

            <label className="deployment-field-r86">
              <span>Deployment reference <b>Optional</b></span>
              <input value={deploymentReference} onChange={event => setDeploymentReference(event.target.value)} disabled={submitting} maxLength={140} placeholder="e.g. CHG-2041 or REL-2026-08" />
              <small>Change ticket, release ID or controlled rollout reference.</small>
            </label>

            <label className="deployment-field-r86 deployment-evidence-field-r86">
              <span>Supporting evidence <b>Required</b></span>
              <select value={evidenceDocumentId} onChange={event => setEvidenceDocumentId(event.target.value)} disabled={submitting} required>
                <option value="">Select evidence document</option>
                {documents.map(document => (
                  <option value={document.id} key={document.id}>{document.title} · {document.document_type}{document.version ? ` · ${document.version}` : ""}</option>
                ))}
              </select>
              <small>Provides provenance for the deployment fact; registration is blocked without it.</small>
            </label>

            <label className="deployment-field-r86 deployment-notes-field-r86">
              <span>Notes <b>Optional</b></span>
              <textarea value={notes} onChange={event => setNotes(event.target.value)} disabled={submitting} maxLength={4000} placeholder="Operational context only; do not use this field as a substitute for evidence." />
            </label>

            <div className="deployment-create-actions-r86">
              <button className="ghost-btn" type="button" onClick={closeCreate} disabled={submitting}>Cancel</button>
              <button className="primary-btn" type="submit" disabled={submitting}>
                <Rocket size={15} aria-hidden="true" />{submitting ? "Recording…" : "Record deployment"}
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="deployment-ledger-r86" aria-labelledby="deployment-ledger-title-r86">
        <div className="deployment-ledger-head-r86">
          <div>
            <h2 id="deployment-ledger-title-r86">Deployment ledger</h2>
            <span>{filtered.length} shown of {deployments.length}</span>
          </div>
          <div className="deployment-ledger-controls-r86">
            <label className="deployment-search-r86">
              <Search size={15} aria-hidden="true" />
              <span className="sr-only">Search deployments</span>
              <input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search client, release, evidence…" />
              {query && <button type="button" onClick={() => setQuery("")} aria-label="Clear search"><X size={13} aria-hidden="true" /></button>}
            </label>
            <label className="deployment-filter-r86">
              <span className="sr-only">Filter by client</span>
              <select value={clientFilter} onChange={event => setClientFilter(event.target.value)}>
                <option value="ALL">All clients</option>
                {clients.map(client => <option value={client.id} key={client.id}>{client.name}</option>)}
              </select>
            </label>
            <label className="deployment-filter-r86">
              <span className="sr-only">Filter by environment</span>
              <select value={environmentFilter} onChange={event => setEnvironmentFilter(event.target.value)}>
                <option value="ALL">All environments</option>
                {ENVIRONMENTS.map(item => <option value={item.value} key={item.value}>{item.label}</option>)}
              </select>
            </label>
          </div>
        </div>

        <div className="deployment-table-r86">
          <div className="deployment-table-columns-r86" aria-hidden="true">
            <span>Implementation</span>
            <span>Release / environment</span>
            <span>Deployment event</span>
            <span>Evidence</span>
          </div>

          {filtered.length === 0 ? (
            <div className="deployment-empty-r86">
              <Rocket size={22} aria-hidden="true" />
              <strong>{deployments.length === 0 ? "No deployments recorded" : "No deployments match the current filters"}</strong>
              <span>{deployments.length === 0 ? "Record an evidence-backed deployment when an implementation release is promoted into an environment." : "Clear or adjust the search and filters."}</span>
            </div>
          ) : filtered.map(item => (
            <article className="deployment-row-r86" key={item.id}>
              <div className="deployment-identity-r86" data-label="Implementation">
                <Rocket size={16} aria-hidden="true" />
                <span>
                  <strong>{item.implementation_name}</strong>
                  <small>{item.client_name} · {item.product_name} / {item.module_name}</small>
                  <code>{item.id}</code>
                </span>
              </div>

              <div className="deployment-release-r86" data-label="Release / environment">
                <code>{item.release_version}</code>
                <span className={`deployment-environment-r86 ${item.environment.toLowerCase()}`}>{item.environment}</span>
                <small>{item.status === "DEPLOYED" ? "Deployment recorded" : item.status}</small>
              </div>

              <div className="deployment-event-r86" data-label="Deployment event">
                <CalendarClock size={15} aria-hidden="true" />
                <span>
                  <strong>{formatTimestamp(item.deployed_at)}</strong>
                  <small>{item.deployment_reference || "No external deployment reference"}</small>
                  {item.notes && <em>{item.notes}</em>}
                </span>
              </div>

              <div className="deployment-evidence-r86" data-label="Evidence">
                <FileCheck2 size={15} aria-hidden="true" />
                <span>
                  <strong>{item.evidence_title || "Evidence record unavailable"}</strong>
                  <small>{item.evidence_document_type || "Unknown document type"}</small>
                  <code>{shortHash(item.evidence_content_hash)}</code>
                </span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
