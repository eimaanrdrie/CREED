"use client";

import { useMemo, useRef, useState, type FormEvent } from "react";
import {
  AlertCircle,
  CheckCircle2,
  CirclePause,
  Info,
  Package,
  Plus,
  RefreshCw,
  Search,
  ToggleLeft,
  ToggleRight,
  X,
} from "lucide-react";
import {
  createProduct,
  updateProduct,
  type ProductCreatePayload,
  type ProductRecord,
} from "@/lib/api";

type Notice = { tone: "ok" | "neutral" | "bad"; text: string } | null;

function sortProducts(products: ProductRecord[]) {
  return [...products].sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" }));
}

export function ProductRegistryWorkspace({
  initialProducts,
  loadError,
}: {
  initialProducts: ProductRecord[];
  loadError: boolean;
}) {
  const [products, setProducts] = useState(() => sortProducts(initialProducts));
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "ACTIVE" | "INACTIVE">("ALL");
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [active, setActive] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const nameRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return products.filter(product => {
      if (statusFilter === "ACTIVE" && !product.active) return false;
      if (statusFilter === "INACTIVE" && product.active) return false;
      if (!needle) return true;
      return [product.name, product.description ?? "", product.id]
        .some(value => value.toLowerCase().includes(needle));
    });
  }, [products, query, statusFilter]);

  const activeCount = products.filter(product => product.active).length;
  const inactiveCount = products.length - activeCount;

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
    setDescription("");
    setActive(true);
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedName = name.trim();
    const cleanedDescription = description.trim();
    if (cleanedName.length < 2) {
      setNotice({ tone: "bad", text: "Product name must contain at least 2 characters." });
      nameRef.current?.focus();
      return;
    }

    const payload: ProductCreatePayload = {
      name: cleanedName,
      description: cleanedDescription || null,
      active,
    };

    setSubmitting(true);
    setNotice(null);
    try {
      const created = await createProduct(payload);
      const existed = products.some(product => product.id === created.id);
      setProducts(current => sortProducts([
        ...current.filter(product => product.id !== created.id),
        created,
      ]));
      setNotice({
        tone: existed ? "neutral" : "ok",
        text: existed
          ? `${created.name} already exists with the same catalog definition.`
          : `${created.name} was added to the product catalog.`,
      });
      setShowCreate(false);
      setName("");
      setDescription("");
      setActive(true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "PRODUCT_CREATE_FAILED";
      setNotice({
        tone: "bad",
        text: message === "PRODUCT_NAME_ALREADY_EXISTS"
          ? "A product with this name already exists with different catalog details."
          : `Product could not be added (${message}).`,
      });
    } finally {
      setSubmitting(false);
    }
  }

  async function toggleProduct(product: ProductRecord) {
    setUpdatingId(product.id);
    setNotice(null);
    try {
      const updated = await updateProduct(product.id, { active: !product.active });
      setProducts(current => sortProducts(current.map(item => item.id === updated.id ? updated : item)));
      setNotice({
        tone: "ok",
        text: `${updated.name} is now ${updated.active ? "active" : "inactive"}.`,
      });
    } catch (error) {
      setNotice({
        tone: "bad",
        text: error instanceof Error
          ? `Product status could not be changed (${error.message}).`
          : "Product status could not be changed.",
      });
    } finally {
      setUpdatingId(null);
    }
  }

  return (
    <div className="page product-registry-r89">
      <div className="title-row product-registry-title-r89">
        <div>
          <h1>Products</h1>
          <p className="subtitle">Maintain the delivery product catalog used by modules, implementations, methods and ownership.</p>
          <div className="product-registry-summary-r89" aria-label="Product registry summary">
            <span><strong>{products.length}</strong> registered</span>
            <span><strong>{activeCount}</strong> active</span>
            <span><strong>{inactiveCount}</strong> inactive</span>
          </div>
        </div>
        {!showCreate && (
          <button className="primary-btn" type="button" onClick={openCreate} disabled={loadError}>
            <Plus size={16} aria-hidden="true" />Add product
          </button>
        )}
      </div>

      {loadError && (
        <div className="product-registry-notice-r89 bad" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <div>
            <strong>Product catalog unavailable</strong>
            <span>CREED could not load persisted products. Verify the API and database, then retry.</span>
          </div>
          <button className="secondary-btn compact" type="button" onClick={() => window.location.reload()}>
            <RefreshCw size={14} aria-hidden="true" />Retry
          </button>
        </div>
      )}

      {showCreate && !loadError && (
        <section className="product-create-r89" aria-labelledby="product-create-title-r89">
          <div className="product-create-head-r89">
            <div>
              <h2 id="product-create-title-r89">Register product</h2>
              <p>Creates a persistent catalog record. Modules are registered separately and are never created implicitly.</p>
            </div>
            <button className="icon-btn" type="button" onClick={closeCreate} disabled={submitting} aria-label="Close add product form">
              <X size={16} aria-hidden="true" />
            </button>
          </div>
          <form className="product-create-form-r89" onSubmit={onSubmit} noValidate>
            <label className="product-field-r89">
              <span>Product name <b aria-hidden="true">Required</b></span>
              <input
                ref={nameRef}
                value={name}
                onChange={event => setName(event.target.value)}
                placeholder="e.g. Collections"
                minLength={2}
                maxLength={180}
                required
                autoComplete="off"
                disabled={submitting}
              />
              <small>Use the stable product name that should appear across delivery and assurance records.</small>
            </label>

            <label className="product-field-r89 product-description-r89">
              <span>Description</span>
              <textarea
                value={description}
                onChange={event => setDescription(event.target.value)}
                placeholder="Describe the product boundary and delivery scope."
                maxLength={3000}
                rows={3}
                disabled={submitting}
              />
              <small>Keep this factual. Modules and methods provide the more specific implementation detail.</small>
            </label>

            <label className="product-field-r89">
              <span>Catalog status</span>
              <select value={active ? "ACTIVE" : "INACTIVE"} onChange={event => setActive(event.target.value === "ACTIVE")} disabled={submitting}>
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
              </select>
              <small>Status is catalog metadata. Existing records are not deleted when a product becomes inactive.</small>
            </label>

            <div className="product-create-actions-r89">
              <button className="ghost-btn" type="button" onClick={closeCreate} disabled={submitting}>Cancel</button>
              <button className="primary-btn" type="submit" disabled={submitting}>
                {submitting ? <RefreshCw className="spin" size={15} aria-hidden="true" /> : <Plus size={15} aria-hidden="true" />}
                {submitting ? "Adding product" : "Add product"}
              </button>
            </div>
          </form>
        </section>
      )}

      {notice && (
        <div className={`product-registry-notice-r89 ${notice.tone}`} role={notice.tone === "bad" ? "alert" : "status"}>
          {notice.tone === "ok" ? <CheckCircle2 size={16} aria-hidden="true" /> : notice.tone === "bad" ? <AlertCircle size={16} aria-hidden="true" /> : <Info size={16} aria-hidden="true" />}
          <span>{notice.text}</span>
          <button type="button" aria-label="Dismiss message" onClick={() => setNotice(null)}><X size={14} /></button>
        </div>
      )}

      <section className="product-ledger-r89" aria-labelledby="product-ledger-title-r89">
        <header className="product-ledger-head-r89">
          <div>
            <h2 id="product-ledger-title-r89">Product catalog</h2>
            <span>{filtered.length} of {products.length} visible</span>
          </div>
          <div className="product-ledger-controls-r89">
            <label className="product-search-r89">
              <Search size={15} aria-hidden="true" />
              <input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search products" aria-label="Search products" />
              {query && <button type="button" onClick={() => setQuery("")} aria-label="Clear product search"><X size={14} /></button>}
            </label>
            <label className="product-status-filter-r89">
              <span className="sr-only">Filter by product status</span>
              <select value={statusFilter} onChange={event => setStatusFilter(event.target.value as typeof statusFilter)} aria-label="Filter products by status">
                <option value="ALL">All statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
              </select>
            </label>
          </div>
        </header>

        {loadError ? (
          <div className="product-empty-r89">
            <AlertCircle size={23} aria-hidden="true" />
            <strong>Catalog data was not loaded</strong>
            <span>Retry after the API and database are available.</span>
          </div>
        ) : products.length === 0 ? (
          <div className="product-empty-r89">
            <Package size={24} aria-hidden="true" />
            <strong>No products registered</strong>
            <span>Add the first delivery product before registering modules, implementations or methods.</span>
            <button className="secondary-btn compact" type="button" onClick={openCreate}><Plus size={14} />Add product</button>
          </div>
        ) : filtered.length === 0 ? (
          <div className="product-empty-r89">
            <Search size={23} aria-hidden="true" />
            <strong>No matching products</strong>
            <button className="secondary-btn compact" type="button" onClick={() => { setQuery(""); setStatusFilter("ALL"); }}><X size={14} />Clear filters</button>
          </div>
        ) : (
          <div className="product-table-r89" role="table" aria-label="Registered products">
            <div className="product-table-columns-r89" role="row">
              <span>Product</span><span>Description</span><span>Status</span><span>Product ID</span><span><span className="sr-only">Actions</span></span>
            </div>
            {filtered.map(product => (
              <div className="product-row-r89" role="row" key={product.id}>
                <div className="product-identity-r89" role="cell" data-label="Product">
                  <Package size={16} aria-hidden="true" />
                  <strong>{product.name}</strong>
                </div>
                <span className="product-description-cell-r89" role="cell" data-label="Description">
                  {product.description || "No description"}
                </span>
                <span className={`product-status-r89 ${product.active ? "active" : "inactive"}`} role="cell" data-label="Status">
                  {product.active ? <CheckCircle2 size={14} aria-hidden="true" /> : <CirclePause size={14} aria-hidden="true" />}
                  {product.active ? "Active" : "Inactive"}
                </span>
                <code role="cell" data-label="Product ID">{product.id}</code>
                <button
                  className="product-status-action-r89"
                  type="button"
                  onClick={() => toggleProduct(product)}
                  disabled={updatingId === product.id}
                  aria-label={`${product.active ? "Deactivate" : "Activate"} ${product.name}`}
                >
                  {updatingId === product.id
                    ? <RefreshCw className="spin" size={15} aria-hidden="true" />
                    : product.active
                      ? <ToggleRight size={17} aria-hidden="true" />
                      : <ToggleLeft size={17} aria-hidden="true" />}
                  <span>{product.active ? "Deactivate" : "Activate"}</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
