"use client";

import { useMemo, useRef, useState, type FormEvent } from "react";
import {
  AlertCircle,
  Boxes,
  CheckCircle2,
  CircleDot,
  Info,
  Plus,
  RefreshCw,
  Search,
  X,
} from "lucide-react";
import {
  createImplementation,
  type ClientRecord,
  type ImplementationRecord,
  type ModuleRecord,
  type ProductRecord,
} from "@/lib/api";

type Notice = { tone: "ok" | "bad" | "neutral"; text: string } | null;

function sortImplementations(items: ImplementationRecord[]) {
  return [...items].sort((a, b) =>
    a.client_name.localeCompare(b.client_name) ||
    a.product_name.localeCompare(b.product_name) ||
    a.module_name.localeCompare(b.module_name) ||
    a.name.localeCompare(b.name) ||
    a.release_version.localeCompare(b.release_version),
  );
}

function friendlyError(error: unknown) {
  if (!(error instanceof Error)) return "Implementation could not be registered.";
  const labels: Record<string, string> = {
    CLIENT_NOT_FOUND: "The selected client no longer exists. Reload the registry and try again.",
    PRODUCT_NOT_FOUND: "The selected product no longer exists. Reload the registry and try again.",
    MODULE_NOT_FOUND: "The selected module no longer exists. Reload the registry and try again.",
    MODULE_PRODUCT_MISMATCH: "The selected module does not belong to the selected product.",
  };
  return labels[error.message] ?? `Implementation could not be registered (${error.message}).`;
}

export function ImplementationRegistryWorkspace({
  initialImplementations,
  clients,
  products,
  modules,
  loadError,
  catalogError,
}: {
  initialImplementations: ImplementationRecord[];
  clients: ClientRecord[];
  products: ProductRecord[];
  modules: ModuleRecord[];
  loadError: boolean;
  catalogError: boolean;
}) {
  const [implementations, setImplementations] = useState(() => sortImplementations(initialImplementations));
  const [query, setQuery] = useState("");
  const [clientFilter, setClientFilter] = useState("ALL");
  const [showCreate, setShowCreate] = useState(false);
  const [clientId, setClientId] = useState("");
  const [productId, setProductId] = useState("");
  const [moduleId, setModuleId] = useState("");
  const [name, setName] = useState("");
  const [releaseVersion, setReleaseVersion] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);
  const nameRef = useRef<HTMLInputElement>(null);

  const availableModules = useMemo(
    () => modules.filter(module => module.product_id === productId),
    [modules, productId],
  );

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return implementations.filter(item => {
      if (clientFilter !== "ALL" && item.client_id !== clientFilter) return false;
      if (!needle) return true;
      return [
        item.name,
        item.client_name,
        item.product_name,
        item.module_name,
        item.release_version,
        item.status,
        item.id,
      ].some(value => value.toLowerCase().includes(needle));
    });
  }, [implementations, query, clientFilter]);

  const activeCount = implementations.filter(item => item.status === "ACTIVE").length;
  const representedClients = new Set(implementations.map(item => item.client_id)).size;
  const prerequisitesReady = !loadError && !catalogError && clients.length > 0 && products.length > 0 && modules.length > 0;

  function resetForm() {
    setClientId("");
    setProductId("");
    setModuleId("");
    setName("");
    setReleaseVersion("");
  }

  function openCreate() {
    if (!prerequisitesReady) return;
    setNotice(null);
    setShowCreate(true);
    window.requestAnimationFrame(() => nameRef.current?.focus());
  }

  function closeCreate() {
    if (submitting) return;
    setShowCreate(false);
    resetForm();
  }

  function chooseProduct(value: string) {
    setProductId(value);
    setModuleId("");
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedName = name.trim();
    const cleanedRelease = releaseVersion.trim();

    if (!clientId || !productId || !moduleId) {
      setNotice({ tone: "bad", text: "Choose a client, product and module before registering the implementation." });
      return;
    }
    if (cleanedName.length < 2) {
      setNotice({ tone: "bad", text: "Implementation name must contain at least 2 characters." });
      nameRef.current?.focus();
      return;
    }
    if (!cleanedRelease) {
      setNotice({ tone: "bad", text: "Release version is required." });
      return;
    }

    setSubmitting(true);
    setNotice(null);
    try {
      const created = await createImplementation({
        client_id: clientId,
        product_id: productId,
        module_id: moduleId,
        name: cleanedName,
        release_version: cleanedRelease,
      });
      const existed = implementations.some(item => item.id === created.id);
      setImplementations(current => sortImplementations([
        ...current.filter(item => item.id !== created.id),
        created,
      ]));
      setNotice({
        tone: existed ? "neutral" : "ok",
        text: existed
          ? `${created.client_name} already has ${created.module_name} release ${created.release_version} registered as ${created.name}.`
          : `${created.name} was added to the implementation registry.`,
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
    <div className="page implementation-registry-r81">
      <div className="title-row implementation-registry-title-r81">
        <div>
          <h1>Implementations</h1>
          <p className="subtitle">Register deployed client implementations so issues, evidence and dependency mappings have an explicit implementation identity.</p>
          <div className="implementation-summary-r81" aria-label="Implementation registry summary">
            <span><strong>{implementations.length}</strong> registered</span>
            <span><strong>{activeCount}</strong> active</span>
            <span><strong>{representedClients}</strong> clients represented</span>
          </div>
        </div>
        {!showCreate && (
          <button className="primary-btn" type="button" onClick={openCreate} disabled={!prerequisitesReady}>
            <Plus size={16} aria-hidden="true" />Add implementation
          </button>
        )}
      </div>

      {loadError && (
        <div className="implementation-notice-r81 bad" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <div>
            <strong>Implementation registry unavailable</strong>
            <span>CREED could not load persisted implementations. Verify the API and database, then retry.</span>
          </div>
          <button className="secondary-btn compact" type="button" onClick={() => window.location.reload()}>
            <RefreshCw size={14} aria-hidden="true" />Retry
          </button>
        </div>
      )}

      {!loadError && catalogError && (
        <div className="implementation-notice-r81 bad" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <div>
            <strong>Implementation catalog unavailable</strong>
            <span>Client, product or module options could not be loaded. Existing implementations remain visible, but registration is disabled.</span>
          </div>
          <button className="secondary-btn compact" type="button" onClick={() => window.location.reload()}>
            <RefreshCw size={14} aria-hidden="true" />Retry
          </button>
        </div>
      )}

      {!loadError && !catalogError && clients.length === 0 && (
        <div className="implementation-notice-r81 neutral" role="status">
          <Info size={16} aria-hidden="true" />
          <div>
            <strong>A client is required first</strong>
            <span>Register the organisation before creating an implementation identity.</span>
          </div>
          <a className="secondary-btn compact" href="/clients">Open Clients</a>
        </div>
      )}

      {!loadError && !catalogError && clients.length > 0 && (products.length === 0 || modules.length === 0) && (
        <div className="implementation-notice-r81 neutral" role="status">
          <Info size={16} aria-hidden="true" />
          <div>
            <strong>Product/module catalog is empty</strong>
            <span>Implementation registration requires an existing product and module. This module does not create catalog records.</span>
          </div>
        </div>
      )}

      {showCreate && prerequisitesReady && (
        <section className="implementation-create-r81" aria-labelledby="implementation-create-title-r81">
          <div className="implementation-create-head-r81">
            <div>
              <h2 id="implementation-create-title-r81">Register implementation</h2>
              <p>Creates the persistent deployment identity only. Method-version and Local A-BOM dependency edges are governed separately.</p>
            </div>
            <button className="icon-btn" type="button" onClick={closeCreate} disabled={submitting} aria-label="Close add implementation form">
              <X size={16} aria-hidden="true" />
            </button>
          </div>

          <form className="implementation-create-form-r81" onSubmit={onSubmit} noValidate>
            <label className="implementation-field-r81">
              <span>Client <b aria-hidden="true">Required</b></span>
              <select value={clientId} onChange={event => setClientId(event.target.value)} disabled={submitting} required>
                <option value="">Select client</option>
                {clients.map(client => <option value={client.id} key={client.id}>{client.name}</option>)}
              </select>
              <small>The organisation that owns this deployed implementation.</small>
            </label>

            <label className="implementation-field-r81">
              <span>Product <b aria-hidden="true">Required</b></span>
              <select value={productId} onChange={event => chooseProduct(event.target.value)} disabled={submitting} required>
                <option value="">Select product</option>
                {products.map(product => <option value={product.id} key={product.id}>{product.name}</option>)}
              </select>
              <small>Choose from the existing governed product catalog.</small>
            </label>

            <label className="implementation-field-r81">
              <span>Module <b aria-hidden="true">Required</b></span>
              <select value={moduleId} onChange={event => setModuleId(event.target.value)} disabled={submitting || !productId} required>
                <option value="">{productId ? "Select module" : "Select product first"}</option>
                {availableModules.map(module => <option value={module.id} key={module.id}>{module.name}</option>)}
              </select>
              <small>Only modules belonging to the selected product are shown.</small>
            </label>

            <label className="implementation-field-r81 implementation-name-field-r81">
              <span>Implementation name <b aria-hidden="true">Required</b></span>
              <input
                ref={nameRef}
                value={name}
                onChange={event => setName(event.target.value)}
                placeholder="e.g. Crescent PTP Implementation"
                minLength={2}
                maxLength={220}
                required
                disabled={submitting}
              />
              <small>Use the deployment identity operators will recognise in investigations.</small>
            </label>

            <label className="implementation-field-r81 implementation-release-field-r81">
              <span>Release version <b aria-hidden="true">Required</b></span>
              <input
                value={releaseVersion}
                onChange={event => setReleaseVersion(event.target.value)}
                placeholder="e.g. R1"
                maxLength={80}
                required
                disabled={submitting}
              />
              <small>Release/build label for this client/module deployment.</small>
            </label>

            <div className="implementation-create-actions-r81">
              <button className="ghost-btn" type="button" onClick={closeCreate} disabled={submitting}>Cancel</button>
              <button className="primary-btn" type="submit" disabled={submitting}>
                {submitting ? <RefreshCw className="spin" size={15} aria-hidden="true" /> : <Plus size={15} aria-hidden="true" />}
                {submitting ? "Adding implementation" : "Add implementation"}
              </button>
            </div>
          </form>
        </section>
      )}

      {notice && (
        <div className={`implementation-notice-r81 ${notice.tone}`} role={notice.tone === "bad" ? "alert" : "status"}>
          {notice.tone === "ok" ? <CheckCircle2 size={16} aria-hidden="true" /> : notice.tone === "bad" ? <AlertCircle size={16} aria-hidden="true" /> : <Info size={16} aria-hidden="true" />}
          <span>{notice.text}</span>
          <button type="button" aria-label="Dismiss message" onClick={() => setNotice(null)}><X size={14} /></button>
        </div>
      )}

      <section className="implementation-ledger-r81" aria-labelledby="implementation-ledger-title-r81">
        <header className="implementation-ledger-head-r81">
          <div>
            <h2 id="implementation-ledger-title-r81">Implementation registry</h2>
            <span>{filtered.length} of {implementations.length} visible</span>
          </div>
          <div className="implementation-ledger-controls-r81">
            <label className="implementation-search-r81">
              <Search size={15} aria-hidden="true" />
              <input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search implementations" aria-label="Search implementations" />
              {query && <button type="button" onClick={() => setQuery("")} aria-label="Clear implementation search"><X size={14} /></button>}
            </label>
            <label className="implementation-client-filter-r81">
              <span className="sr-only">Filter implementations by client</span>
              <select value={clientFilter} onChange={event => setClientFilter(event.target.value)} aria-label="Filter implementations by client">
                <option value="ALL">All clients</option>
                {clients.map(client => <option value={client.id} key={client.id}>{client.name}</option>)}
              </select>
            </label>
          </div>
        </header>

        {loadError ? (
          <div className="implementation-empty-r81">
            <AlertCircle size={23} aria-hidden="true" />
            <strong>Registry data was not loaded</strong>
            <span>Retry after the API and database are available.</span>
          </div>
        ) : implementations.length === 0 ? (
          <div className="implementation-empty-r81">
            <Boxes size={24} aria-hidden="true" />
            <strong>No implementations registered</strong>
            <span>Create a client deployment identity before attaching implementation-specific dependency evidence.</span>
            {prerequisitesReady && <button className="secondary-btn compact" type="button" onClick={openCreate}><Plus size={14} />Add implementation</button>}
          </div>
        ) : filtered.length === 0 ? (
          <div className="implementation-empty-r81">
            <Search size={23} aria-hidden="true" />
            <strong>No matching implementations</strong>
            <button className="secondary-btn compact" type="button" onClick={() => { setQuery(""); setClientFilter("ALL"); }}><X size={14} />Clear filters</button>
          </div>
        ) : (
          <div className="implementation-table-r81" role="table" aria-label="Registered implementations">
            <div className="implementation-table-columns-r81" role="row">
              <span>Implementation</span><span>Client</span><span>Product / module</span><span>Release</span><span>Status</span>
            </div>
            {filtered.map(item => (
              <div className="implementation-row-r81" role="row" key={item.id}>
                <div className="implementation-identity-r81" role="cell" data-label="Implementation">
                  <Boxes size={16} aria-hidden="true" />
                  <span><strong>{item.name}</strong><code>{item.id}</code></span>
                </div>
                <span className="implementation-client-r81" role="cell" data-label="Client">{item.client_name}</span>
                <span className="implementation-scope-r81" role="cell" data-label="Product / module"><strong>{item.product_name}</strong><small>{item.module_name}</small></span>
                <code className="implementation-release-r81" role="cell" data-label="Release">{item.release_version}</code>
                <span className={`implementation-status-r81 ${item.status === "ACTIVE" ? "active" : "neutral"}`} role="cell" data-label="Status">
                  {item.status === "ACTIVE" ? <CheckCircle2 size={14} aria-hidden="true" /> : <CircleDot size={14} aria-hidden="true" />}
                  {item.status.replaceAll("_", " ")}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
