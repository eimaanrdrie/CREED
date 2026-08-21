"use client";

import { FormEvent, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  Info,
  Plus,
  RefreshCw,
  Search,
  X,
} from "lucide-react";
import { createClient, type ClientCreatePayload, type ClientRecord } from "@/lib/api";

type ClientType = ClientCreatePayload["client_type"];
type Notice = { tone: "ok" | "neutral" | "bad"; text: string } | null;

const CLIENT_TYPES: Array<{ value: ClientType; label: string }> = [
  { value: "BANK", label: "Bank" },
  { value: "FINANCIAL_INSTITUTION", label: "Financial institution" },
];

function typeLabel(value: string) {
  return CLIENT_TYPES.find(option => option.value === value)?.label
    ?? value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, letter => letter.toUpperCase());
}

function sortClients(clients: ClientRecord[]) {
  return [...clients].sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" }));
}

export function ClientRegistryWorkspace({
  initialClients,
  loadError,
}: {
  initialClients: ClientRecord[];
  loadError: boolean;
}) {
  const [clients, setClients] = useState(() => sortClients(initialClients));
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [clientType, setClientType] = useState<ClientType>("BANK");
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);
  const nameRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return clients.filter(client => {
      if (typeFilter !== "ALL" && client.client_type !== typeFilter) return false;
      if (!needle) return true;
      return [client.name, client.client_type, client.id]
        .some(value => value.toLowerCase().includes(needle));
    });
  }, [clients, query, typeFilter]);

  const bankCount = clients.filter(client => client.client_type === "BANK").length;
  const institutionCount = clients.filter(client => client.client_type === "FINANCIAL_INSTITUTION").length;
  const bankLabel = bankCount === 1 ? "bank" : "banks";
  const institutionLabel = institutionCount === 1 ? "financial institution" : "financial institutions";

  function openCreate() {
    if (loadError) return;
    setNotice(null);
    setShowCreate(true);
    window.requestAnimationFrame(() => nameRef.current?.focus());
  }

  function closeCreate() {
    if (submitting) return;
    setShowCreate(false);
    setName("");
    setClientType("BANK");
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedName = name.trim();
    if (cleanedName.length < 2) {
      setNotice({ tone: "bad", text: "Client name must contain at least 2 characters." });
      nameRef.current?.focus();
      return;
    }

    setSubmitting(true);
    setNotice(null);
    try {
      const created = await createClient({ name: cleanedName, client_type: clientType });
      const existed = clients.some(client => client.id === created.id);
      setClients(current => sortClients([
        ...current.filter(client => client.id !== created.id),
        created,
      ]));
      setNotice({
        tone: existed ? "neutral" : "ok",
        text: existed
          ? `${created.name} already exists in the client registry.`
          : `${created.name} was added to the client registry.`,
      });
      setName("");
      setClientType("BANK");
      setShowCreate(false);
    } catch (error) {
      setNotice({
        tone: "bad",
        text: error instanceof Error
          ? `Client could not be added (${error.message}).`
          : "Client could not be added.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page client-registry-r80">
      <div className="title-row client-registry-title-r80">
        <div>
          <h1>Clients</h1>
          <p className="subtitle">Register the organisations that own delivery issues and governed implementations.</p>
          <div className="client-registry-summary-r80" aria-label="Client registry summary">
            <span><strong>{clients.length}</strong> registered</span>
            <span><strong>{bankCount}</strong> {bankLabel}</span>
            <span><strong>{institutionCount}</strong> {institutionLabel}</span>
          </div>
        </div>
        {!showCreate && (
          <button className="primary-btn" type="button" onClick={openCreate} disabled={loadError}>
            <Plus size={16} aria-hidden="true" />Add client
          </button>
        )}
      </div>

      {loadError && (
        <div className="client-registry-notice-r80 bad" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <div>
            <strong>Client registry unavailable</strong>
            <span>CREED could not load persisted clients. Verify the API and database, then retry.</span>
          </div>
          <button className="secondary-btn compact" type="button" onClick={() => window.location.reload()}>
            <RefreshCw size={14} aria-hidden="true" />Retry
          </button>
        </div>
      )}

      {showCreate && !loadError && (
        <section className="client-create-r80" aria-labelledby="client-create-title-r80">
          <div className="client-create-head-r80">
            <div>
              <h2 id="client-create-title-r80">Register client</h2>
              <p>Creates a persistent client record used by issue intake. Implementation ownership is managed separately.</p>
            </div>
            <button className="icon-btn" type="button" onClick={closeCreate} disabled={submitting} aria-label="Close add client form">
              <X size={16} aria-hidden="true" />
            </button>
          </div>
          <form className="client-create-form-r80" onSubmit={onSubmit} noValidate>
            <label className="client-field-r80">
              <span>Client name <b aria-hidden="true">Required</b></span>
              <input
                ref={nameRef}
                value={name}
                onChange={event => setName(event.target.value)}
                placeholder="e.g. Crescent Bank"
                minLength={2}
                maxLength={180}
                required
                autoComplete="organization"
                disabled={submitting}
              />
              <small>Use the organisation name that should appear in issue intake and assurance records.</small>
            </label>
            <label className="client-field-r80">
              <span>Client type</span>
              <select value={clientType} onChange={event => setClientType(event.target.value as ClientType)} disabled={submitting}>
                {CLIENT_TYPES.map(option => <option value={option.value} key={option.value}>{option.label}</option>)}
              </select>
              <small>Classification only. It does not assign products or implementations.</small>
            </label>
            <div className="client-create-actions-r80">
              <button className="ghost-btn" type="button" onClick={closeCreate} disabled={submitting}>Cancel</button>
              <button className="primary-btn" type="submit" disabled={submitting}>
                {submitting ? <RefreshCw className="spin" size={15} aria-hidden="true" /> : <Plus size={15} aria-hidden="true" />}
                {submitting ? "Adding client" : "Add client"}
              </button>
            </div>
          </form>
        </section>
      )}

      {notice && (
        <div className={`client-registry-notice-r80 ${notice.tone}`} role={notice.tone === "bad" ? "alert" : "status"}>
          {notice.tone === "ok" ? <CheckCircle2 size={16} aria-hidden="true" /> : notice.tone === "bad" ? <AlertCircle size={16} aria-hidden="true" /> : <Info size={16} aria-hidden="true" />}
          <span>{notice.text}</span>
          <button type="button" aria-label="Dismiss message" onClick={() => setNotice(null)}><X size={14} /></button>
        </div>
      )}

      <section className="client-ledger-r80" aria-labelledby="client-ledger-title-r80">
        <header className="client-ledger-head-r80">
          <div>
            <h2 id="client-ledger-title-r80">Client registry</h2>
            <span>{filtered.length} of {clients.length} visible</span>
          </div>
          <div className="client-ledger-controls-r80">
            <label className="client-search-r80">
              <Search size={15} aria-hidden="true" />
              <input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search clients" aria-label="Search clients" />
              {query && <button type="button" onClick={() => setQuery("")} aria-label="Clear client search"><X size={14} /></button>}
            </label>
            <label className="client-type-filter-r80">
              <span className="sr-only">Filter by client type</span>
              <select value={typeFilter} onChange={event => setTypeFilter(event.target.value)} aria-label="Filter clients by type">
                <option value="ALL">All types</option>
                {CLIENT_TYPES.map(option => <option value={option.value} key={option.value}>{option.label}</option>)}
              </select>
            </label>
          </div>
        </header>

        {loadError ? (
          <div className="client-empty-r80">
            <AlertCircle size={23} aria-hidden="true" />
            <strong>Registry data was not loaded</strong>
            <span>Retry after the API and database are available.</span>
          </div>
        ) : clients.length === 0 ? (
          <div className="client-empty-r80">
            <Building2 size={24} aria-hidden="true" />
            <strong>No clients registered</strong>
            <span>Add the first organisation before assigning issues or implementations.</span>
            <button className="secondary-btn compact" type="button" onClick={openCreate}><Plus size={14} />Add client</button>
          </div>
        ) : filtered.length === 0 ? (
          <div className="client-empty-r80">
            <Search size={23} aria-hidden="true" />
            <strong>No matching clients</strong>
            <button className="secondary-btn compact" type="button" onClick={() => { setQuery(""); setTypeFilter("ALL"); }}><X size={14} />Clear filters</button>
          </div>
        ) : (
          <div className="client-table-r80" role="table" aria-label="Registered clients">
            <div className="client-table-columns-r80" role="row">
              <span>Client</span><span>Type</span><span>Client ID</span>
            </div>
            {filtered.map(client => (
              <div className="client-row-r80" role="row" key={client.id}>
                <div className="client-identity-r80" role="cell" data-label="Client">
                  <Building2 size={16} aria-hidden="true" />
                  <strong>{client.name}</strong>
                </div>
                <span className="client-type-r80" role="cell" data-label="Type">{typeLabel(client.client_type)}</span>
                <code role="cell" data-label="Client ID">{client.id}</code>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
