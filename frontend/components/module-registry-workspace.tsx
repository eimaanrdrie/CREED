"use client";

import { useMemo, useRef, useState, type FormEvent } from "react";
import {
  AlertCircle,
  CheckCircle2,
  CirclePause,
  FolderTree,
  Info,
  Plus,
  RefreshCw,
  Search,
  ToggleLeft,
  ToggleRight,
  X,
} from "lucide-react";
import {
  createModule,
  updateModule,
  type ModuleCreatePayload,
  type ModuleRecord,
  type ProductRecord,
} from "@/lib/api";

type Notice = { tone: "ok" | "neutral" | "bad"; text: string } | null;

function sortModules(modules: ModuleRecord[], productName: (id: string) => string) {
  return [...modules].sort((a, b) => {
    const productOrder = productName(a.product_id).localeCompare(productName(b.product_id), undefined, { sensitivity: "base" });
    return productOrder || a.name.localeCompare(b.name, undefined, { sensitivity: "base" });
  });
}

export function ModuleRegistryWorkspace({
  initialProducts,
  initialModules,
  loadError,
}: {
  initialProducts: ProductRecord[];
  initialModules: ModuleRecord[];
  loadError: boolean;
}) {
  const productById = useMemo(() => new Map(initialProducts.map(product => [product.id, product])), [initialProducts]);
  const productName = (id: string) => productById.get(id)?.name ?? "Unknown product";
  const activeProducts = useMemo(() => initialProducts.filter(product => product.active), [initialProducts]);

  const [modules, setModules] = useState(() => sortModules(initialModules, productName));
  const [query, setQuery] = useState("");
  const [productFilter, setProductFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "ACTIVE" | "INACTIVE">("ALL");
  const [showCreate, setShowCreate] = useState(false);
  const [productId, setProductId] = useState(activeProducts[0]?.id ?? "");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [active, setActive] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const nameRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return modules.filter(module => {
      if (productFilter !== "ALL" && module.product_id !== productFilter) return false;
      if (statusFilter === "ACTIVE" && !module.active) return false;
      if (statusFilter === "INACTIVE" && module.active) return false;
      if (!needle) return true;
      const product = productById.get(module.product_id)?.name ?? "";
      return [module.name, module.description ?? "", module.id, product]
        .some(value => value.toLowerCase().includes(needle));
    });
  }, [modules, productFilter, statusFilter, query, productById]);

  const activeCount = modules.filter(module => module.active).length;
  const inactiveCount = modules.length - activeCount;

  function openCreate() {
    if (loadError || activeProducts.length === 0) return;
    setNotice(null);
    if (!productId || !activeProducts.some(product => product.id === productId)) setProductId(activeProducts[0].id);
    setShowCreate(true);
    window.requestAnimationFrame(() => nameRef.current?.focus());
  }

  function closeCreate() {
    if (submitting) return;
    setShowCreate(false);
    setName("");
    setDescription("");
    setActive(true);
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedName = name.trim();
    const cleanedDescription = description.trim();
    if (!productId) {
      setNotice({ tone: "bad", text: "Choose an active product before registering the module." });
      return;
    }
    if (cleanedName.length < 2) {
      setNotice({ tone: "bad", text: "Module name must contain at least 2 characters." });
      nameRef.current?.focus();
      return;
    }

    const payload: ModuleCreatePayload = {
      product_id: productId,
      name: cleanedName,
      description: cleanedDescription || null,
      active,
    };

    setSubmitting(true);
    setNotice(null);
    try {
      const created = await createModule(payload);
      const existed = modules.some(module => module.id === created.id);
      setModules(current => sortModules([
        ...current.filter(module => module.id !== created.id),
        created,
      ], productName));
      setNotice({
        tone: existed ? "neutral" : "ok",
        text: existed
          ? `${created.name} already exists under ${productName(created.product_id)} with the same catalog definition.`
          : `${created.name} was added under ${productName(created.product_id)}.`,
      });
      setShowCreate(false);
      setName("");
      setDescription("");
      setActive(true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "MODULE_CREATE_FAILED";
      setNotice({
        tone: "bad",
        text: message === "MODULE_NAME_ALREADY_EXISTS"
          ? "A module with this name already exists under the selected product with different catalog details."
          : message === "PRODUCT_INACTIVE"
            ? "The selected product is inactive. Reactivate it before registering another module."
            : `Module could not be added (${message}).`,
      });
    } finally {
      setSubmitting(false);
    }
  }

  async function toggleModule(module: ModuleRecord) {
    setUpdatingId(module.id);
    setNotice(null);
    try {
      const updated = await updateModule(module.id, { active: !module.active });
      setModules(current => sortModules(current.map(item => item.id === updated.id ? updated : item), productName));
      setNotice({ tone: "ok", text: `${updated.name} is now ${updated.active ? "active" : "inactive"}.` });
    } catch (error) {
      setNotice({
        tone: "bad",
        text: error instanceof Error
          ? `Module status could not be changed (${error.message}).`
          : "Module status could not be changed.",
      });
    } finally {
      setUpdatingId(null);
    }
  }

  return (
    <div className="page module-registry-r90">
      <div className="title-row module-registry-title-r90">
        <div>
          <h1>Modules</h1>
          <p className="subtitle">Maintain product-scoped delivery capabilities used by implementations, methods and ownership.</p>
          <div className="module-registry-summary-r90" aria-label="Module registry summary">
            <span><strong>{modules.length}</strong> registered</span>
            <span><strong>{activeCount}</strong> active</span>
            <span><strong>{inactiveCount}</strong> inactive</span>
            <span><strong>{initialProducts.length}</strong> products</span>
          </div>
        </div>
        {!showCreate && (
          <button className="primary-btn" type="button" onClick={openCreate} disabled={loadError || activeProducts.length === 0}>
            <Plus size={16} aria-hidden="true" />Add module
          </button>
        )}
      </div>

      {!loadError && activeProducts.length === 0 && (
        <div className="module-registry-notice-r90 neutral" role="status">
          <Info size={16} aria-hidden="true" />
          <div>
            <strong>Active product required</strong>
            <span>Register or reactivate a product before adding modules.</span>
          </div>
          <a className="secondary-btn compact" href="/products">Open products</a>
        </div>
      )}

      {loadError && (
        <div className="module-registry-notice-r90 bad" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <div>
            <strong>Module catalog unavailable</strong>
            <span>CREED could not load persisted products or modules. Verify the API and database, then retry.</span>
          </div>
          <button className="secondary-btn compact" type="button" onClick={() => window.location.reload()}>
            <RefreshCw size={14} aria-hidden="true" />Retry
          </button>
        </div>
      )}

      {showCreate && !loadError && activeProducts.length > 0 && (
        <section className="module-create-r90" aria-labelledby="module-create-title-r90">
          <div className="module-create-head-r90">
            <div>
              <h2 id="module-create-title-r90">Register module</h2>
              <p>Creates a product-scoped catalog record. Methods and implementations remain separate governed records.</p>
            </div>
            <button className="icon-btn" type="button" onClick={closeCreate} disabled={submitting} aria-label="Close add module form">
              <X size={16} aria-hidden="true" />
            </button>
          </div>
          <form className="module-create-form-r90" onSubmit={onSubmit} noValidate>
            <label className="module-field-r90">
              <span>Product <b aria-hidden="true">Required</b></span>
              <select value={productId} onChange={event => setProductId(event.target.value)} required disabled={submitting}>
                {activeProducts.map(product => <option value={product.id} key={product.id}>{product.name}</option>)}
              </select>
              <small>Only active products can receive new modules.</small>
            </label>

            <label className="module-field-r90">
              <span>Module name <b aria-hidden="true">Required</b></span>
              <input ref={nameRef} value={name} onChange={event => setName(event.target.value)} placeholder="e.g. Promise-to-Pay" minLength={2} maxLength={180} required autoComplete="off" disabled={submitting} />
              <small>Use the stable capability name used in delivery and assurance records.</small>
            </label>

            <label className="module-field-r90 module-description-r90">
              <span>Description</span>
              <textarea value={description} onChange={event => setDescription(event.target.value)} placeholder="Describe the module boundary and operational responsibility." maxLength={3000} rows={3} disabled={submitting} />
              <small>Keep the description factual; method-level behavior belongs in the Method Registry.</small>
            </label>

            <label className="module-field-r90">
              <span>Catalog status</span>
              <select value={active ? "ACTIVE" : "INACTIVE"} onChange={event => setActive(event.target.value === "ACTIVE")} disabled={submitting}>
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
              </select>
              <small>Deactivation does not delete historical implementations, methods or ownership.</small>
            </label>

            <div className="module-create-actions-r90">
              <button className="ghost-btn" type="button" onClick={closeCreate} disabled={submitting}>Cancel</button>
              <button className="primary-btn" type="submit" disabled={submitting}>
                {submitting ? <RefreshCw className="spin" size={15} aria-hidden="true" /> : <Plus size={15} aria-hidden="true" />}
                {submitting ? "Adding module" : "Add module"}
              </button>
            </div>
          </form>
        </section>
      )}

      {notice && (
        <div className={`module-registry-notice-r90 ${notice.tone}`} role={notice.tone === "bad" ? "alert" : "status"}>
          {notice.tone === "ok" ? <CheckCircle2 size={16} aria-hidden="true" /> : notice.tone === "bad" ? <AlertCircle size={16} aria-hidden="true" /> : <Info size={16} aria-hidden="true" />}
          <span>{notice.text}</span>
          <button type="button" aria-label="Dismiss message" onClick={() => setNotice(null)}><X size={14} /></button>
        </div>
      )}

      <section className="module-ledger-r90" aria-labelledby="module-ledger-title-r90">
        <header className="module-ledger-head-r90">
          <div>
            <h2 id="module-ledger-title-r90">Module catalog</h2>
            <span>{filtered.length} of {modules.length} visible</span>
          </div>
          <div className="module-ledger-controls-r90">
            <label className="module-search-r90">
              <Search size={15} aria-hidden="true" />
              <input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search modules" aria-label="Search modules" />
              {query && <button type="button" onClick={() => setQuery("")} aria-label="Clear module search"><X size={14} /></button>}
            </label>
            <label className="module-filter-r90">
              <span className="sr-only">Filter modules by product</span>
              <select value={productFilter} onChange={event => setProductFilter(event.target.value)} aria-label="Filter modules by product">
                <option value="ALL">All products</option>
                {initialProducts.map(product => <option value={product.id} key={product.id}>{product.name}</option>)}
              </select>
            </label>
            <label className="module-filter-r90">
              <span className="sr-only">Filter modules by status</span>
              <select value={statusFilter} onChange={event => setStatusFilter(event.target.value as typeof statusFilter)} aria-label="Filter modules by status">
                <option value="ALL">All statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
              </select>
            </label>
          </div>
        </header>

        {loadError ? (
          <div className="module-empty-r90"><AlertCircle size={23} aria-hidden="true" /><strong>Catalog data was not loaded</strong><span>Retry after the API and database are available.</span></div>
        ) : initialProducts.length === 0 ? (
          <div className="module-empty-r90"><FolderTree size={24} aria-hidden="true" /><strong>No products registered</strong><span>A module must belong to a product. Register the first product before continuing.</span><a className="secondary-btn compact" href="/products"><Plus size={14} />Add product</a></div>
        ) : modules.length === 0 ? (
          <div className="module-empty-r90"><FolderTree size={24} aria-hidden="true" /><strong>No modules registered</strong><span>Add the first product capability before registering methods or implementations.</span>{activeProducts.length > 0 && <button className="secondary-btn compact" type="button" onClick={openCreate}><Plus size={14} />Add module</button>}</div>
        ) : filtered.length === 0 ? (
          <div className="module-empty-r90"><Search size={23} aria-hidden="true" /><strong>No matching modules</strong><button className="secondary-btn compact" type="button" onClick={() => { setQuery(""); setProductFilter("ALL"); setStatusFilter("ALL"); }}><X size={14} />Clear filters</button></div>
        ) : (
          <div className="module-table-r90" role="table" aria-label="Registered modules">
            <div className="module-table-columns-r90" role="row">
              <span>Module</span><span>Product</span><span>Description</span><span>Status</span><span>Module ID</span><span><span className="sr-only">Actions</span></span>
            </div>
            {filtered.map(module => {
              const parent = productById.get(module.product_id);
              return (
                <div className="module-row-r90" role="row" key={module.id}>
                  <div className="module-identity-r90" role="cell" data-label="Module"><FolderTree size={16} aria-hidden="true" /><strong>{module.name}</strong></div>
                  <div className="module-product-r90" role="cell" data-label="Product"><strong>{parent?.name ?? "Unknown product"}</strong>{parent && !parent.active && <span>Parent inactive</span>}</div>
                  <span className="module-description-cell-r90" role="cell" data-label="Description">{module.description || "No description"}</span>
                  <span className={`module-status-r90 ${module.active ? "active" : "inactive"}`} role="cell" data-label="Status">{module.active ? <CheckCircle2 size={14} aria-hidden="true" /> : <CirclePause size={14} aria-hidden="true" />}{module.active ? "Active" : "Inactive"}</span>
                  <code role="cell" data-label="Module ID">{module.id}</code>
                  <button className="module-status-action-r90" type="button" onClick={() => toggleModule(module)} disabled={updatingId === module.id} aria-label={`${module.active ? "Deactivate" : "Activate"} ${module.name}`}>
                    {updatingId === module.id ? <RefreshCw className="spin" size={15} aria-hidden="true" /> : module.active ? <ToggleRight size={17} aria-hidden="true" /> : <ToggleLeft size={17} aria-hidden="true" />}
                    <span>{module.active ? "Deactivate" : "Activate"}</span>
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
