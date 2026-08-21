"use client";

import { useMemo, useRef, useState, type FormEvent } from "react";
import {
  AlertCircle,
  CheckCircle2,
  FileCheck2,
  Info,
  Link2,
  Network,
  Plus,
  Search,
  ShieldAlert,
  Trash2,
  X,
} from "lucide-react";
import {
  createImplementationMethodDependency,
  removeImplementationMethodDependency,
  type EvidenceDocument,
  type ImplementationMethodDependencyRecord,
  type ImplementationRecord,
  type RegisteredMethodVersionRecord,
} from "@/lib/api";

type Notice = { tone: "ok" | "bad" | "neutral"; text: string } | null;

function sortDependencies(items: ImplementationMethodDependencyRecord[]) {
  return [...items].sort((a, b) =>
    a.client_name.localeCompare(b.client_name) ||
    a.implementation_name.localeCompare(b.implementation_name) ||
    a.method_version.localeCompare(b.method_version),
  );
}

function dependencyError(error: unknown) {
  if (!(error instanceof Error)) return "Dependency could not be registered.";
  const labels: Record<string, string> = {
    IMPLEMENTATION_NOT_FOUND: "The selected implementation no longer exists. Reload the registry and try again.",
    METHOD_VERSION_NOT_FOUND: "The selected method version no longer exists. Reload the registry and try again.",
    EVIDENCE_DOCUMENT_NOT_FOUND: "The selected evidence document no longer exists. Reload the registry and try again.",
    IMPLEMENTATION_METHOD_MODULE_MISMATCH: "That method version belongs to a different module and cannot be linked to this implementation.",
    DEPENDENCY_ALREADY_EXISTS_WITH_DIFFERENT_EVIDENCE: "This implementation already uses that method version with different evidence. Remove the existing dependency before registering a replacement.",
    LEARNED_METHOD_VERSION_NOT_APPROVED_FOR_ADOPTION: "This learned Method Version has not completed governed Learning approval and cannot be reused yet.",
    ADOPTION_RECEIPT_REQUIRED_FOR_LEARNED_VERSION: "This learned Method Version has no Signed Adoption Receipt. CREED will not reuse it.",
    ADOPTION_RECEIPT_DETAIL_REQUIRED: "The Signed Adoption Receipt is incomplete. CREED will not reuse this learned Method Version.",
    ADOPTION_RECEIPT_INTEGRITY_INVALID: "The Signed Adoption Receipt failed integrity verification. CREED blocked this reuse.",
    ADOPTION_SCOPE_REQUIRED_FOR_LEARNED_VERSION: "This learned Method Version has no enforceable R94 adoption scope. CREED blocked this reuse.",
    ADOPTION_SCOPE_METHOD_VERSION_MISMATCH: "The Signed Adoption Receipt does not match this Method Version. CREED blocked this reuse.",
    ADOPTION_SCOPE_EXCLUDES_IMPLEMENTATION: "The Learning Authority did not approve this implementation inside the Signed Adoption Receipt scope.",
  };
  return labels[error.message] ?? `Dependency could not be registered (${error.message}).`;
}

function removeError(error: unknown) {
  if (!(error instanceof Error)) return "Dependency could not be removed.";
  const labels: Record<string, string> = {
    DEPENDENCY_NOT_FOUND: "This dependency no longer exists. Reload the registry.",
    NOT_IMPLEMENTATION_METHOD_DEPENDENCY: "This record is not an implementation-to-method dependency and cannot be removed here.",
  };
  return labels[error.message] ?? `Dependency could not be removed (${error.message}).`;
}

function versionState(status: string) {
  if (status === "APPROVED") return { label: "Approved", tone: "approved" };
  if (status === "REVOKED") return { label: "Revoked", tone: "revoked" };
  if (status === "PROPOSED") return { label: "Proposed", tone: "proposed" };
  return { label: "Draft", tone: "draft" };
}

function shortHash(value: string | null) {
  if (!value) return "No content seal";
  return `${value.slice(0, 12)}…${value.slice(-8)}`;
}

function adoptionEligibility(version: RegisteredMethodVersionRecord, implementationId: string) {
  const policy = version.adoption_policy;
  if (!policy?.enforced) return { allowed: true, label: null as string | null };
  if (policy.reason !== "READY" || policy.receipt_integrity !== "VALID") {
    return { allowed: false, label: "Governed learning unavailable" };
  }
  if (policy.scope_mode === "METHOD_CATALOG") {
    return { allowed: true, label: "Catalog scope" };
  }
  const allowed = policy.implementation_ids.includes(implementationId);
  return {
    allowed,
    label: allowed ? "Within signed scope" : "Outside signed scope",
  };
}

export function DependencyRegistryWorkspace({
  initialDependencies,
  implementations,
  methodVersions,
  documents,
  loadError,
  catalogError,
}: {
  initialDependencies: ImplementationMethodDependencyRecord[];
  implementations: ImplementationRecord[];
  methodVersions: RegisteredMethodVersionRecord[];
  documents: EvidenceDocument[];
  loadError: boolean;
  catalogError: boolean;
}) {
  const [dependencies, setDependencies] = useState(() => sortDependencies(initialDependencies));
  const [query, setQuery] = useState("");
  const [clientFilter, setClientFilter] = useState("ALL");
  const [showCreate, setShowCreate] = useState(false);
  const [implementationId, setImplementationId] = useState("");
  const [methodVersionId, setMethodVersionId] = useState("");
  const [evidenceDocumentId, setEvidenceDocumentId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [removeReason, setRemoveReason] = useState("");
  const [removing, setRemoving] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);
  const implementationRef = useRef<HTMLSelectElement>(null);
  const removeReasonRef = useRef<HTMLTextAreaElement>(null);

  const clients = useMemo(() => {
    const map = new Map<string, string>();
    for (const implementation of implementations) map.set(implementation.client_id, implementation.client_name);
    for (const dependency of dependencies) map.set(dependency.client_id, dependency.client_name);
    return [...map.entries()].sort((a, b) => a[1].localeCompare(b[1]));
  }, [dependencies, implementations]);

  const selectedImplementation = useMemo(
    () => implementations.find(item => item.id === implementationId) ?? null,
    [implementationId, implementations],
  );

  const compatibleVersions = useMemo(() => {
    if (!selectedImplementation) return [];
    return methodVersions
      .filter(item => item.module_id === selectedImplementation.module_id)
      .sort((a, b) => a.method_name.localeCompare(b.method_name) || b.version.localeCompare(a.version));
  }, [methodVersions, selectedImplementation]);

  const selectedMethodVersion = useMemo(
    () => methodVersions.find(item => item.id === methodVersionId) ?? null,
    [methodVersionId, methodVersions],
  );

  const selectedAdoptionEligibility = useMemo(
    () => selectedMethodVersion && implementationId ? adoptionEligibility(selectedMethodVersion, implementationId) : null,
    [implementationId, selectedMethodVersion],
  );

  const sortedDocuments = useMemo(
    () => [...documents].sort((a, b) => a.title.localeCompare(b.title)),
    [documents],
  );

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return dependencies.filter(item => {
      if (clientFilter !== "ALL" && item.client_id !== clientFilter) return false;
      if (!needle) return true;
      return [
        item.client_name,
        item.implementation_name,
        item.implementation_release_version,
        item.product_name,
        item.module_name,
        item.method_name,
        item.method_version,
        item.method_version_status,
        item.evidence_title ?? "",
        item.evidence_document_type ?? "",
        item.id,
      ].some(value => value.toLowerCase().includes(needle));
    });
  }, [clientFilter, dependencies, query]);

  const linkedImplementations = new Set(dependencies.map(item => item.implementation_id)).size;
  const linkedVersions = new Set(dependencies.map(item => item.method_version_id)).size;
  const evidenceBacked = dependencies.filter(item => item.evidence_document_id).length;
  const prerequisitesReady = !catalogError && implementations.length > 0 && methodVersions.length > 0 && documents.length > 0;

  function resetCreate() {
    setImplementationId("");
    setMethodVersionId("");
    setEvidenceDocumentId("");
  }

  function openCreate() {
    if (loadError || !prerequisitesReady) return;
    setNotice(null);
    setRemovingId(null);
    setRemoveReason("");
    setShowCreate(true);
    window.requestAnimationFrame(() => implementationRef.current?.focus());
  }

  function closeCreate() {
    if (submitting) return;
    setShowCreate(false);
    resetCreate();
  }

  function chooseImplementation(value: string) {
    setImplementationId(value);
    setMethodVersionId("");
  }

  async function submitDependency(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!implementationId || !methodVersionId || !evidenceDocumentId) {
      setNotice({ tone: "bad", text: "Choose an implementation, compatible method version and supporting evidence document." });
      return;
    }
    const implementation = implementations.find(item => item.id === implementationId);
    const version = methodVersions.find(item => item.id === methodVersionId);
    if (!implementation || !version || implementation.module_id !== version.module_id) {
      setNotice({ tone: "bad", text: "The selected method version is not compatible with the implementation module." });
      return;
    }
    const eligibility = adoptionEligibility(version, implementation.id);
    if (!eligibility.allowed) {
      setNotice({ tone: "bad", text: "This implementation is outside the learned Method Version's signed adoption scope." });
      return;
    }

    setSubmitting(true);
    setNotice(null);
    try {
      const created = await createImplementationMethodDependency({
        implementation_id: implementationId,
        method_version_id: methodVersionId,
        evidence_document_id: evidenceDocumentId,
      });
      const existed = dependencies.some(item => item.id === created.id);
      setDependencies(current => sortDependencies([
        ...current.filter(item => item.id !== created.id),
        created,
      ]));
      setNotice({
        tone: existed ? "neutral" : "ok",
        text: existed
          ? `${created.implementation_name} already records ${created.method_version} as a current dependency.`
          : `${created.implementation_name} now records ${created.method_version} as an evidence-backed A-BOM dependency.`,
      });
      setShowCreate(false);
      resetCreate();
    } catch (error) {
      setNotice({ tone: "bad", text: dependencyError(error) });
    } finally {
      setSubmitting(false);
    }
  }

  function beginRemove(id: string) {
    if (removing) return;
    setNotice(null);
    setShowCreate(false);
    resetCreate();
    setRemovingId(id);
    setRemoveReason("");
    window.requestAnimationFrame(() => removeReasonRef.current?.focus());
  }

  function cancelRemove() {
    if (removing) return;
    setRemovingId(null);
    setRemoveReason("");
  }

  async function confirmRemove(event: FormEvent<HTMLFormElement>, dependency: ImplementationMethodDependencyRecord) {
    event.preventDefault();
    const reason = removeReason.trim();
    if (reason.length < 3) {
      setNotice({ tone: "bad", text: "Give a short reason for removing the dependency from current A-BOM routing." });
      removeReasonRef.current?.focus();
      return;
    }
    setRemoving(true);
    setNotice(null);
    try {
      await removeImplementationMethodDependency(dependency.id, reason);
      setDependencies(current => current.filter(item => item.id !== dependency.id));
      setRemovingId(null);
      setRemoveReason("");
      setNotice({
        tone: "ok",
        text: `${dependency.implementation_name} → ${dependency.method_version} was removed from current dependency routing. The removal remains auditable.`,
      });
    } catch (error) {
      setNotice({ tone: "bad", text: removeError(error) });
    } finally {
      setRemoving(false);
    }
  }

  return (
    <div className="page dependency-registry-r83">
      <div className="title-row dependency-registry-title-r83">
        <div>
          <h1>Dependencies</h1>
          <p className="subtitle">Maintain the Local A-BOM relationships that connect a client implementation to the method version it actually uses, with evidence attached to every new registration.</p>
          <div className="dependency-summary-r83" aria-label="Dependency registry summary">
            <span><strong>{dependencies.length}</strong> relationships</span>
            <span><strong>{linkedImplementations}</strong> implementations linked</span>
            <span><strong>{linkedVersions}</strong> method versions in use</span>
            <span><strong>{evidenceBacked}</strong> evidence-backed</span>
          </div>
        </div>
        {!showCreate && (
          <button className="primary-btn" type="button" onClick={openCreate} disabled={loadError || !prerequisitesReady}>
            <Plus size={15} aria-hidden="true" /> Register dependency
          </button>
        )}
      </div>

      {showCreate && (
        <section className="dependency-create-r83" aria-labelledby="dependency-create-title-r83">
          <div className="dependency-create-head-r83">
            <div>
              <h2 id="dependency-create-title-r83">Register implementation dependency</h2>
              <p>This writes one explicit <code>USES_METHOD_VERSION</code> edge. It does not approve the method, declare an implementation affected, or create a governance adoption receipt.</p>
            </div>
            <button className="icon-btn" type="button" onClick={closeCreate} aria-label="Close dependency form" disabled={submitting}>
              <X size={16} aria-hidden="true" />
            </button>
          </div>
          <form className="dependency-create-form-r83" onSubmit={submitDependency}>
            <label className="dependency-field-r83">
              <span>Implementation <b>Required</b></span>
              <select ref={implementationRef} value={implementationId} onChange={event => chooseImplementation(event.target.value)} disabled={submitting}>
                <option value="">Choose implementation</option>
                {implementations.map(item => (
                  <option value={item.id} key={item.id}>{item.client_name} — {item.name} · {item.release_version}</option>
                ))}
              </select>
              <small>The deployed client-specific solution that owns this dependency.</small>
            </label>
            <label className="dependency-field-r83">
              <span>Method version <b>Required</b></span>
              <select value={methodVersionId} onChange={event => setMethodVersionId(event.target.value)} disabled={!selectedImplementation || submitting}>
                <option value="">{selectedImplementation ? "Choose compatible version" : "Choose implementation first"}</option>
                {compatibleVersions.map(item => {
                  const scope = adoptionEligibility(item, implementationId);
                  return (
                    <option value={item.id} key={item.id} disabled={!scope.allowed}>
                      {item.method_name} — {item.version} · {item.status}{scope.label ? ` · ${scope.label}` : ""}
                    </option>
                  );
                })}
              </select>
              <small>Only same-module versions are shown. Governed learned versions are additionally constrained by their Signed Adoption Receipt.</small>
              {selectedMethodVersion?.adoption_policy?.enforced && selectedAdoptionEligibility && (
                <small>Signed scope: {selectedMethodVersion.adoption_policy.scope_mode ?? "Unavailable"} · {selectedAdoptionEligibility.allowed ? "this implementation is eligible" : "this implementation is blocked"}.</small>
              )}
            </label>
            <label className="dependency-field-r83 dependency-evidence-field-r83">
              <span>Supporting evidence <b>Required</b></span>
              <select value={evidenceDocumentId} onChange={event => setEvidenceDocumentId(event.target.value)} disabled={submitting}>
                <option value="">Choose repository evidence</option>
                {sortedDocuments.map(item => (
                  <option value={item.id} key={item.id}>{item.title} · {item.document_type}{item.version ? ` · ${item.version}` : ""}</option>
                ))}
              </select>
              <small>Use a configuration, release or design record that supports the dependency claim.</small>
            </label>
            <div className="dependency-create-context-r83">
              <Info size={15} aria-hidden="true" />
              <span>
                {selectedMethodVersion && selectedMethodVersion.status !== "APPROVED"
                  ? `${selectedMethodVersion.version} is ${selectedMethodVersion.status}. Recording usage does not approve it; the non-approved state remains visible to governance workflows.`
                  : "A-BOM registration records current implementation usage only. Impact, Human Decision, adoption and recall remain separate governed workflows."}
              </span>
            </div>
            <div className="dependency-create-actions-r83">
              <button className="ghost-btn" type="button" onClick={closeCreate} disabled={submitting}>Cancel</button>
              <button className="primary-btn" type="submit" disabled={submitting}>
                <Link2 size={15} aria-hidden="true" /> {submitting ? "Registering…" : "Register dependency"}
              </button>
            </div>
          </form>
        </section>
      )}

      {notice && (
        <div className={`dependency-notice-r83 ${notice.tone}`} role={notice.tone === "bad" ? "alert" : "status"}>
          {notice.tone === "bad" ? <AlertCircle size={16} aria-hidden="true" /> : notice.tone === "ok" ? <CheckCircle2 size={16} aria-hidden="true" /> : <Info size={16} aria-hidden="true" />}
          <span>{notice.text}</span>
          <button type="button" aria-label="Dismiss message" onClick={() => setNotice(null)}><X size={14} aria-hidden="true" /></button>
        </div>
      )}

      {loadError && (
        <div className="dependency-notice-r83 bad" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <div><strong>Dependency registry unavailable</strong><span>CREED could not load persisted A-BOM relationships. No fallback relationships are being shown.</span></div>
        </div>
      )}

      {!loadError && catalogError && (
        <div className="dependency-notice-r83 bad" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <div><strong>Registry prerequisites unavailable</strong><span>Existing dependencies are visible, but implementation, method-version or evidence catalogs could not be loaded for new registration.</span></div>
        </div>
      )}

      {!loadError && !catalogError && !prerequisitesReady && (
        <div className="dependency-notice-r83 neutral" role="status">
          <Info size={16} aria-hidden="true" />
          <div>
            <strong>Registration prerequisites are incomplete</strong>
            <span>Create at least one implementation and method version, then upload supporting Knowledge evidence before registering an A-BOM relationship.</span>
          </div>
        </div>
      )}

      <section className="dependency-ledger-r83" aria-labelledby="dependency-ledger-title-r83">
        <header className="dependency-ledger-head-r83">
          <div>
            <h2 id="dependency-ledger-title-r83">Local A-BOM ledger</h2>
            <span>{filtered.length} of {dependencies.length} relationships shown</span>
          </div>
          <div className="dependency-ledger-controls-r83">
            <label className="dependency-search-r83">
              <Search size={14} aria-hidden="true" />
              <span className="sr-only">Search dependencies</span>
              <input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search client, implementation or method" />
              {query && <button type="button" onClick={() => setQuery("")} aria-label="Clear search"><X size={13} aria-hidden="true" /></button>}
            </label>
            <label className="dependency-client-filter-r83">
              <span className="sr-only">Filter by client</span>
              <select value={clientFilter} onChange={event => setClientFilter(event.target.value)}>
                <option value="ALL">All clients</option>
                {clients.map(([id, name]) => <option value={id} key={id}>{name}</option>)}
              </select>
            </label>
          </div>
        </header>

        <div className="dependency-table-r83">
          <div className="dependency-table-columns-r83" aria-hidden="true">
            <span>Implementation</span><span>Uses method version</span><span>Supporting evidence</span><span>Action</span>
          </div>
          {filtered.length === 0 ? (
            <div className="dependency-empty-r83">
              <Network size={22} aria-hidden="true" />
              <strong>{dependencies.length === 0 ? "No implementation dependencies registered" : "No dependencies match this view"}</strong>
              <span>{dependencies.length === 0 ? "Register an evidence-backed implementation → method-version relationship to make Local A-BOM routing explicit." : "Change the search or client filter to inspect another relationship."}</span>
              {dependencies.length === 0 && prerequisitesReady && !loadError && <button className="secondary-btn" type="button" onClick={openCreate}><Plus size={14} aria-hidden="true" /> Register dependency</button>}
            </div>
          ) : filtered.map(item => {
            const state = versionState(item.method_version_status);
            const isRemoving = removingId === item.id;
            return (
              <div className="dependency-record-r83" key={item.id}>
                <div className="dependency-row-r83">
                  <div className="dependency-implementation-r83">
                    <span className="dependency-node-icon-r83" aria-hidden="true"><Network size={15} /></span>
                    <span>
                      <strong>{item.implementation_name}</strong>
                      <small>{item.client_name} · {item.product_name} / {item.module_name}</small>
                      <code>{item.implementation_release_version} · {item.implementation_id}</code>
                    </span>
                  </div>
                  <div className="dependency-method-r83" data-label="Uses method version">
                    <strong>{item.method_name}</strong>
                    <code>{item.method_version}</code>
                    <span className={state.tone}>{state.label}</span>
                  </div>
                  <div className="dependency-evidence-r83" data-label="Supporting evidence">
                    <FileCheck2 size={15} aria-hidden="true" />
                    <span>
                      <strong>{item.evidence_title ?? "Evidence reference unavailable"}</strong>
                      <small>{item.evidence_document_type ?? "Unresolved evidence"}{item.evidence_version ? ` · ${item.evidence_version}` : ""}</small>
                      <code title={item.evidence_content_hash ?? undefined}>{shortHash(item.evidence_content_hash)}</code>
                    </span>
                  </div>
                  <div className="dependency-action-r83" data-label="Action">
                    <button className="dependency-remove-trigger-r83" type="button" onClick={() => beginRemove(item.id)} disabled={removing}>
                      <Trash2 size={14} aria-hidden="true" /> Remove
                    </button>
                  </div>
                </div>
                {isRemoving && (
                  <form className="dependency-remove-r83" onSubmit={event => confirmRemove(event, item)}>
                    <div className="dependency-remove-context-r83">
                      <ShieldAlert size={16} aria-hidden="true" />
                      <span><strong>Remove current A-BOM relationship?</strong><small>This changes impact and recall routing for {item.implementation_name}. The removal action is retained in Audit.</small></span>
                    </div>
                    <label>
                      <span>Reason <b>Required</b></span>
                      <textarea ref={removeReasonRef} value={removeReason} onChange={event => setRemoveReason(event.target.value)} placeholder="Why is this dependency no longer current?" disabled={removing} />
                    </label>
                    <div className="dependency-remove-actions-r83">
                      <button className="ghost-btn" type="button" onClick={cancelRemove} disabled={removing}>Cancel</button>
                      <button className="dependency-remove-confirm-r83" type="submit" disabled={removing}>
                        <Trash2 size={14} aria-hidden="true" /> {removing ? "Removing…" : "Remove dependency"}
                      </button>
                    </div>
                  </form>
                )}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
