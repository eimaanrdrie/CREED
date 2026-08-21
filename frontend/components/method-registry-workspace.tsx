"use client";

import { useMemo, useRef, useState, type FormEvent } from "react";
import {
  AlertCircle,
  Ban,
  CheckCircle2,
  CircleDashed,
  Clock3,
  GitBranch,
  Info,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";
import {
  approveBaselineMethodVersion,
  createDeliveryMethod,
  createDraftMethodVersion,
  type DeliveryMethodRecord,
  type HumanAuthorityRecord,
  type ModuleRecord,
  type ProductRecord,
  type RegisteredMethodVersionRecord,
} from "@/lib/api";

type Notice = { tone: "ok" | "bad" | "neutral"; text: string } | null;

function sortMethods(items: DeliveryMethodRecord[]) {
  return [...items].sort((a, b) =>
    a.product_name.localeCompare(b.product_name) ||
    a.module_name.localeCompare(b.module_name) ||
    a.name.localeCompare(b.name),
  );
}

function sortVersions(items: RegisteredMethodVersionRecord[]) {
  return [...items].sort((a, b) =>
    a.method_name.localeCompare(b.method_name) || b.version.localeCompare(a.version),
  );
}

function methodError(error: unknown) {
  if (!(error instanceof Error)) return "Delivery method could not be registered.";
  const labels: Record<string, string> = {
    MODULE_NOT_FOUND: "The selected module no longer exists. Reload the registry and try again.",
  };
  return labels[error.message] ?? `Delivery method could not be registered (${error.message}).`;
}

function versionError(error: unknown) {
  if (!(error instanceof Error)) return "Draft method version could not be created.";
  const labels: Record<string, string> = {
    METHOD_NOT_FOUND: "The selected delivery method no longer exists. Reload the registry and try again.",
  };
  return labels[error.message] ?? `Draft method version could not be created (${error.message}).`;
}

function baselineApprovalError(error: unknown) {
  if (!(error instanceof Error)) return "Baseline method version could not be approved.";
  const labels: Record<string, string> = {
    METHOD_VERSION_NOT_FOUND: "The selected version no longer exists. Reload the registry and try again.",
    METHOD_VERSION_NOT_DRAFT: "Only a DRAFT method version can be approved as the initial baseline.",
    METHOD_BASELINE_ALREADY_ESTABLISHED: "This method already has an approved or previously approved baseline. Use the governed learning workflow for later versions.",
    AUTHORITY_PRINCIPAL_REQUIRED: "Choose an approving authority before submitting the baseline approval.",
    AUTHORITY_PRINCIPAL_NOT_REGISTERED: "The selected approving principal is no longer registered.",
    AUTHORITY_PRINCIPAL_INACTIVE: "The selected approving principal is inactive. Choose another authority.",
    AUTHORITY_PRINCIPAL_MISMATCH: "The selected authority does not match the submitted governance principal.",
    LEARNING_APPROVAL_AUTHORITY_REQUIRED: "This principal does not have method-learning approval authority.",
  };
  return labels[error.message] ?? `Baseline method version could not be approved (${error.message}).`;
}

function statusMeta(status: string) {
  if (status === "APPROVED") return { Icon: CheckCircle2, label: "Approved", className: "approved" };
  if (status === "PROPOSED") return { Icon: Clock3, label: "Proposed", className: "proposed" };
  if (status === "REVOKED") return { Icon: Ban, label: "Revoked", className: "revoked" };
  return { Icon: CircleDashed, label: "Draft", className: "draft" };
}

export function MethodRegistryWorkspace({
  initialMethods,
  initialVersions,
  products,
  modules,
  authorities,
  loadError,
  catalogError,
  authorityError,
}: {
  initialMethods: DeliveryMethodRecord[];
  initialVersions: RegisteredMethodVersionRecord[];
  products: ProductRecord[];
  modules: ModuleRecord[];
  authorities: HumanAuthorityRecord[];
  loadError: boolean;
  catalogError: boolean;
  authorityError: boolean;
}) {
  const [methods, setMethods] = useState(() => sortMethods(initialMethods));
  const [versions, setVersions] = useState(() => sortVersions(initialVersions));
  const [query, setQuery] = useState("");
  const [productFilter, setProductFilter] = useState("ALL");
  const [showCreateMethod, setShowCreateMethod] = useState(false);
  const [productId, setProductId] = useState("");
  const [moduleId, setModuleId] = useState("");
  const [methodName, setMethodName] = useState("");
  const [methodDescription, setMethodDescription] = useState("");
  const [draftMethodId, setDraftMethodId] = useState<string | null>(null);
  const [versionLabel, setVersionLabel] = useState("");
  const [versionSummary, setVersionSummary] = useState("");
  const [baselineVersionId, setBaselineVersionId] = useState<string | null>(null);
  const [baselineAuthorityId, setBaselineAuthorityId] = useState("");
  const [baselineReason, setBaselineReason] = useState("");
  const [submittingMethod, setSubmittingMethod] = useState(false);
  const [submittingVersion, setSubmittingVersion] = useState(false);
  const [submittingBaseline, setSubmittingBaseline] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);
  const methodNameRef = useRef<HTMLInputElement>(null);
  const versionRef = useRef<HTMLInputElement>(null);
  const baselineReasonRef = useRef<HTMLTextAreaElement>(null);

  const modulesForCreate = useMemo(
    () => modules.filter(module => module.product_id === productId),
    [modules, productId],
  );

  const versionsByMethod = useMemo(() => {
    const map = new Map<string, RegisteredMethodVersionRecord[]>();
    for (const version of versions) {
      const current = map.get(version.method_id) ?? [];
      current.push(version);
      map.set(version.method_id, current);
    }
    return map;
  }, [versions]);

  const eligibleBaselineAuthorities = useMemo(
    () => authorities.filter(item => item.active && item.can_approve_learning),
    [authorities],
  );

  const baselineCandidateCount = useMemo(() => {
    let count = 0;
    for (const method of methods) {
      const methodVersions = versionsByMethod.get(method.id) ?? [];
      const baselineEstablished = methodVersions.some(item => item.status === "APPROVED" || item.status === "REVOKED");
      if (!baselineEstablished) count += methodVersions.filter(item => item.status === "DRAFT").length;
    }
    return count;
  }, [methods, versionsByMethod]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return methods.filter(method => {
      if (productFilter !== "ALL" && method.product_id !== productFilter) return false;
      if (!needle) return true;
      const methodVersions = versionsByMethod.get(method.id) ?? [];
      return [
        method.name,
        method.description ?? "",
        method.product_name,
        method.module_name,
        method.id,
        ...methodVersions.flatMap(item => [item.version, item.status, item.summary ?? "", item.id]),
      ].some(value => value.toLowerCase().includes(needle));
    });
  }, [methods, productFilter, query, versionsByMethod]);

  const approvedCount = versions.filter(item => item.status === "APPROVED").length;
  const draftCount = versions.filter(item => item.status === "DRAFT").length;
  const catalogReady = !catalogError && products.length > 0 && modules.length > 0;

  function resetMethodForm() {
    setProductId("");
    setModuleId("");
    setMethodName("");
    setMethodDescription("");
  }

  function openCreateMethod() {
    if (!catalogReady || loadError) return;
    setNotice(null);
    setDraftMethodId(null);
    setBaselineVersionId(null);
    setShowCreateMethod(true);
    window.requestAnimationFrame(() => methodNameRef.current?.focus());
  }

  function closeCreateMethod() {
    if (submittingMethod) return;
    setShowCreateMethod(false);
    resetMethodForm();
  }

  function chooseProduct(value: string) {
    setProductId(value);
    setModuleId("");
  }

  function openDraftVersion(methodId: string) {
    if (submittingVersion) return;
    setNotice(null);
    setShowCreateMethod(false);
    resetMethodForm();
    setBaselineVersionId(null);
    setDraftMethodId(methodId);
    setVersionLabel("");
    setVersionSummary("");
    window.requestAnimationFrame(() => versionRef.current?.focus());
  }

  function closeDraftVersion() {
    if (submittingVersion) return;
    setDraftMethodId(null);
    setVersionLabel("");
    setVersionSummary("");
  }

  function openBaselineApproval(versionId: string) {
    if (submittingBaseline || authorityError || eligibleBaselineAuthorities.length === 0) return;
    setNotice(null);
    setShowCreateMethod(false);
    resetMethodForm();
    closeDraftVersion();
    setBaselineVersionId(versionId);
    setBaselineAuthorityId(eligibleBaselineAuthorities.length === 1 ? eligibleBaselineAuthorities[0].id : "");
    setBaselineReason("");
    window.requestAnimationFrame(() => baselineReasonRef.current?.focus());
  }

  function closeBaselineApproval() {
    if (submittingBaseline) return;
    setBaselineVersionId(null);
    setBaselineAuthorityId("");
    setBaselineReason("");
  }

  async function submitMethod(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedName = methodName.trim();
    const cleanedDescription = methodDescription.trim();

    if (!productId || !moduleId) {
      setNotice({ tone: "bad", text: "Choose a product and module before registering the delivery method." });
      return;
    }
    const selectedModule = modules.find(item => item.id === moduleId);
    if (!selectedModule || selectedModule.product_id !== productId) {
      setNotice({ tone: "bad", text: "The selected module does not belong to the selected product." });
      return;
    }
    if (cleanedName.length < 2) {
      setNotice({ tone: "bad", text: "Method name must contain at least 2 characters." });
      methodNameRef.current?.focus();
      return;
    }

    setSubmittingMethod(true);
    setNotice(null);
    try {
      const created = await createDeliveryMethod({
        module_id: moduleId,
        name: cleanedName,
        description: cleanedDescription || null,
      });
      const existed = methods.some(item => item.id === created.id);
      setMethods(current => sortMethods([
        ...current.filter(item => item.id !== created.id),
        created,
      ]));
      setNotice({
        tone: existed ? "neutral" : "ok",
        text: existed
          ? `${created.name} already exists in ${created.module_name}.`
          : `${created.name} was added to the delivery-method registry.`,
      });
      setShowCreateMethod(false);
      resetMethodForm();
    } catch (error) {
      setNotice({ tone: "bad", text: methodError(error) });
    } finally {
      setSubmittingMethod(false);
    }
  }

  async function submitVersion(event: FormEvent<HTMLFormElement>, method: DeliveryMethodRecord) {
    event.preventDefault();
    const cleanedVersion = versionLabel.trim();
    const cleanedSummary = versionSummary.trim();
    if (!cleanedVersion) {
      setNotice({ tone: "bad", text: "Version label is required." });
      versionRef.current?.focus();
      return;
    }

    setSubmittingVersion(true);
    setNotice(null);
    try {
      const created = await createDraftMethodVersion({
        method_id: method.id,
        version: cleanedVersion,
        summary: cleanedSummary || null,
      });
      const existed = versions.some(item => item.id === created.id);
      setVersions(current => sortVersions([
        ...current.filter(item => item.id !== created.id),
        created,
      ]));
      setNotice({
        tone: existed ? "neutral" : "ok",
        text: existed
          ? `${created.version} already exists for ${created.method_name} with status ${created.status}.`
          : `${created.version} was created as a DRAFT. It is not approved or assigned to an implementation.`,
      });
      setDraftMethodId(null);
      setVersionLabel("");
      setVersionSummary("");
    } catch (error) {
      setNotice({ tone: "bad", text: versionError(error) });
    } finally {
      setSubmittingVersion(false);
    }
  }

  async function submitBaselineApproval(event: FormEvent<HTMLFormElement>, version: RegisteredMethodVersionRecord) {
    event.preventDefault();
    const authority = eligibleBaselineAuthorities.find(item => item.id === baselineAuthorityId);
    const reason = baselineReason.trim();
    if (!authority) {
      setNotice({ tone: "bad", text: "Choose an active authority with Learning approval before approving the baseline." });
      return;
    }
    if (reason.length < 3) {
      setNotice({ tone: "bad", text: "Approval rationale must contain at least 3 characters." });
      baselineReasonRef.current?.focus();
      return;
    }

    setSubmittingBaseline(true);
    setNotice(null);
    try {
      const approved = await approveBaselineMethodVersion(
        version.id,
        { reviewer: authority.principal, reason },
        authority.principal,
      );
      setVersions(current => sortVersions([
        ...current.filter(item => item.id !== approved.id),
        approved,
      ]));
      setNotice({
        tone: "ok",
        text: `${approved.version} is now the approved initial baseline for ${approved.method_name}. No implementation adoption or A-BOM dependency was created.`,
      });
      setBaselineVersionId(null);
      setBaselineAuthorityId("");
      setBaselineReason("");
    } catch (error) {
      setNotice({ tone: "bad", text: baselineApprovalError(error) });
    } finally {
      setSubmittingBaseline(false);
    }
  }

  return (
    <div className="page method-registry-r82">
      <div className="title-row method-registry-title-r82">
        <div>
          <h1>Methods</h1>
          <p className="subtitle">Register reusable delivery methods, controlled versions and the one-time governed baseline that anchors later learning and recall.</p>
          <div className="method-summary-r82" aria-label="Method registry summary">
            <span><strong>{methods.length}</strong> methods</span>
            <span><strong>{versions.length}</strong> versions</span>
            <span><strong>{approvedCount}</strong> approved</span>
            <span><strong>{draftCount}</strong> drafts</span>
          </div>
        </div>
        {!showCreateMethod && (
          <button className="primary-btn" type="button" onClick={openCreateMethod} disabled={!catalogReady || loadError}>
            <Plus size={16} aria-hidden="true" />Add method
          </button>
        )}
      </div>

      {loadError && (
        <div className="method-notice-r82 bad" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <div>
            <strong>Method registry unavailable</strong>
            <span>CREED could not load persisted methods or versions. Verify the API and database before changing the registry.</span>
          </div>
          <button className="secondary-btn compact" type="button" onClick={() => window.location.reload()}>
            <RefreshCw size={14} aria-hidden="true" />Retry
          </button>
        </div>
      )}

      {!loadError && catalogError && (
        <div className="method-notice-r82 bad" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <div>
            <strong>Product/module catalog unavailable</strong>
            <span>Existing methods remain visible, but new method registration is disabled until the catalog can be loaded. Draft versions can still be added to loaded methods.</span>
          </div>
          <button className="secondary-btn compact" type="button" onClick={() => window.location.reload()}>
            <RefreshCw size={14} aria-hidden="true" />Retry
          </button>
        </div>
      )}

      {!loadError && !catalogError && (products.length === 0 || modules.length === 0) && (
        <div className="method-notice-r82 neutral" role="status">
          <Info size={16} aria-hidden="true" />
          <div>
            <strong>Product/module catalog is empty</strong>
            <span>A delivery method must belong to an existing module. Create Products and Modules from the Registry before adding a method.</span>
          </div>
        </div>
      )}

      {!loadError && baselineCandidateCount > 0 && (authorityError || eligibleBaselineAuthorities.length === 0) && (
        <div className={`method-notice-r82 ${authorityError ? "bad" : "neutral"}`} role={authorityError ? "alert" : "status"}>
          <ShieldCheck size={16} aria-hidden="true" />
          <div>
            <strong>Baseline approval needs governance authority</strong>
            <span>{authorityError ? "CREED could not load the authority registry. Existing methods remain visible, but baseline approval is unavailable." : "Register or activate a principal with Learning approval before approving the initial baseline."}</span>
          </div>
          <a className="secondary-btn compact" href="/authority">Open Authority</a>
        </div>
      )}

      {notice && (
        <div className={`method-notice-r82 ${notice.tone}`} role={notice.tone === "bad" ? "alert" : "status"}>
          {notice.tone === "ok" ? <CheckCircle2 size={16} aria-hidden="true" /> : notice.tone === "bad" ? <AlertCircle size={16} aria-hidden="true" /> : <Info size={16} aria-hidden="true" />}
          <span>{notice.text}</span>
          <button type="button" aria-label="Dismiss message" onClick={() => setNotice(null)}><X size={14} aria-hidden="true" /></button>
        </div>
      )}

      {showCreateMethod && catalogReady && !loadError && (
        <section className="method-create-r82" aria-labelledby="method-create-title-r82">
          <div className="method-create-head-r82">
            <div>
              <h2 id="method-create-title-r82">Register delivery method</h2>
              <p>Creates the reusable method identity only. Approval and A-BOM adoption happen elsewhere in the governed lifecycle, except for the one-time initial baseline approval exposed on an eligible DRAFT version.</p>
            </div>
            <button className="icon-btn" type="button" onClick={closeCreateMethod} disabled={submittingMethod} aria-label="Close add method form">
              <X size={16} aria-hidden="true" />
            </button>
          </div>
          <form className="method-create-form-r82" onSubmit={submitMethod} noValidate>
            <label className="method-field-r82">
              <span>Product <b aria-hidden="true">Required</b></span>
              <select value={productId} onChange={event => chooseProduct(event.target.value)} disabled={submittingMethod} required>
                <option value="">Select product</option>
                {products.map(product => <option value={product.id} key={product.id}>{product.name}</option>)}
              </select>
              <small>Used to constrain the module choice.</small>
            </label>
            <label className="method-field-r82">
              <span>Module <b aria-hidden="true">Required</b></span>
              <select value={moduleId} onChange={event => setModuleId(event.target.value)} disabled={!productId || submittingMethod} required>
                <option value="">{productId ? "Select module" : "Choose product first"}</option>
                {modulesForCreate.map(module => <option value={module.id} key={module.id}>{module.name}</option>)}
              </select>
              <small>The functional area that owns the reusable method.</small>
            </label>
            <label className="method-field-r82 method-name-field-r82">
              <span>Method name <b aria-hidden="true">Required</b></span>
              <input ref={methodNameRef} value={methodName} onChange={event => setMethodName(event.target.value)} placeholder="PTP Event Handling" disabled={submittingMethod} maxLength={220} required />
              <small>Stable name for the reusable delivery method.</small>
            </label>
            <label className="method-field-r82 method-description-field-r82">
              <span>Description <b aria-hidden="true">Optional</b></span>
              <input value={methodDescription} onChange={event => setMethodDescription(event.target.value)} placeholder="Reusable event-processing method for Promise-to-Pay" disabled={submittingMethod} maxLength={3000} />
              <small>Short operational purpose; do not encode a client-specific implementation here.</small>
            </label>
            <div className="method-create-actions-r82">
              <button className="ghost-btn" type="button" onClick={closeCreateMethod} disabled={submittingMethod}>Cancel</button>
              <button className="primary-btn" type="submit" disabled={submittingMethod}>
                {submittingMethod ? <RefreshCw className="spin" size={15} aria-hidden="true" /> : <Plus size={15} aria-hidden="true" />}
                {submittingMethod ? "Registering" : "Register method"}
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="method-ledger-r82" aria-labelledby="method-ledger-title-r82">
        <div className="method-ledger-head-r82">
          <div>
            <h2 id="method-ledger-title-r82">Delivery method ledger</h2>
            <span>{filtered.length} of {methods.length} methods shown</span>
          </div>
          <div className="method-ledger-controls-r82">
            <label className="method-search-r82">
              <Search size={15} aria-hidden="true" />
              <span className="sr-only">Search methods and versions</span>
              <input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search method, module or version" />
              {query && <button type="button" onClick={() => setQuery("")} aria-label="Clear search"><X size={13} aria-hidden="true" /></button>}
            </label>
            <label className="method-product-filter-r82">
              <span className="sr-only">Filter by product</span>
              <select value={productFilter} onChange={event => setProductFilter(event.target.value)}>
                <option value="ALL">All products</option>
                {products.map(product => <option value={product.id} key={product.id}>{product.name}</option>)}
              </select>
            </label>
          </div>
        </div>

        <div className="method-table-r82" role="table" aria-label="Delivery methods">
          <div className="method-table-columns-r82" role="row">
            <span role="columnheader">Method</span>
            <span role="columnheader">Scope</span>
            <span role="columnheader">Version history</span>
            <span role="columnheader">Action</span>
          </div>

          {!loadError && filtered.map(method => {
            const methodVersions = versionsByMethod.get(method.id) ?? [];
            const showingDraft = draftMethodId === method.id;
            const baselineEstablished = methodVersions.some(item => item.status === "APPROVED" || item.status === "REVOKED");
            const approvingVersion = methodVersions.find(item => item.id === baselineVersionId) ?? null;
            return (
              <div className="method-record-r82" key={method.id}>
                <div className="method-row-r82" role="row">
                  <div className="method-identity-r82" role="cell">
                    <GitBranch size={16} aria-hidden="true" />
                    <span>
                      <strong>{method.name}</strong>
                      <code>{method.id}</code>
                      {method.description && <small>{method.description}</small>}
                    </span>
                  </div>
                  <div className="method-scope-r82" role="cell" data-label="Scope">
                    <strong>{method.module_name}</strong>
                    <small>{method.product_name}</small>
                  </div>
                  <div className="method-version-stack-r82" role="cell" data-label="Version history">
                    {methodVersions.length === 0 ? (
                      <span className="method-no-version-r82">No versions registered</span>
                    ) : (
                      methodVersions.map(version => {
                        const state = statusMeta(version.status);
                        const StateIcon = state.Icon;
                        return (
                          <div className={`method-version-line-r82 ${state.className}`} key={version.id} title={version.summary ?? undefined}>
                            <code>{version.version}</code>
                            <span><StateIcon size={12} aria-hidden="true" />{state.label}</span>
                            {version.status === "DRAFT" && !baselineEstablished && (
                              <button
                                className="method-baseline-trigger-r91"
                                type="button"
                                onClick={() => baselineVersionId === version.id ? closeBaselineApproval() : openBaselineApproval(version.id)}
                                disabled={authorityError || eligibleBaselineAuthorities.length === 0 || (submittingBaseline && baselineVersionId !== version.id)}
                                title={authorityError ? "Authority registry unavailable" : eligibleBaselineAuthorities.length === 0 ? "No eligible baseline approver" : "Approve as the initial governed baseline"}
                              >
                                <ShieldCheck size={12} aria-hidden="true" />
                                {baselineVersionId === version.id ? "Close approval" : "Approve baseline"}
                              </button>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                  <div className="method-row-action-r82" role="cell" data-label="Action">
                    <button className="secondary-btn compact" type="button" onClick={() => showingDraft ? closeDraftVersion() : openDraftVersion(method.id)} disabled={submittingVersion && !showingDraft}>
                      {showingDraft ? <X size={14} aria-hidden="true" /> : <Plus size={14} aria-hidden="true" />}
                      {showingDraft ? "Close" : "Draft version"}
                    </button>
                  </div>
                </div>

                {approvingVersion && (
                  <form className="method-baseline-approval-r91" onSubmit={event => submitBaselineApproval(event, approvingVersion)} noValidate>
                    <div className="method-version-context-r82">
                      <span>Initial governed baseline</span>
                      <strong>{approvingVersion.version}</strong>
                      <small>{method.name} / {method.product_name} / {method.module_name}</small>
                    </div>
                    <label className="method-field-r82">
                      <span>Approving authority <b aria-hidden="true">Required</b></span>
                      <select value={baselineAuthorityId} onChange={event => setBaselineAuthorityId(event.target.value)} disabled={submittingBaseline} required>
                        <option value="">Select eligible authority</option>
                        {eligibleBaselineAuthorities.map(authority => (
                          <option value={authority.id} key={authority.id}>{authority.display_name} — {authority.role_title}</option>
                        ))}
                      </select>
                      <small>Active principals with Learning approval are eligible for initial method governance.</small>
                    </label>
                    <label className="method-field-r82 method-baseline-reason-r91">
                      <span>Approval rationale <b aria-hidden="true">Required</b></span>
                      <textarea
                        ref={baselineReasonRef}
                        value={baselineReason}
                        onChange={event => setBaselineReason(event.target.value)}
                        placeholder="Initial approved baseline for existing Promise-to-Pay implementations."
                        disabled={submittingBaseline}
                        maxLength={3000}
                        required
                      />
                      <small>This establishes the first approved baseline only. It does not adopt the version into any implementation.</small>
                    </label>
                    <div className="method-baseline-actions-r91">
                      <span><ShieldCheck size={13} aria-hidden="true" />This one-time setup action is blocked after a baseline has been approved or revoked. Later versions must use the governed learning workflow.</span>
                      <div>
                        <button className="ghost-btn" type="button" onClick={closeBaselineApproval} disabled={submittingBaseline}>Cancel</button>
                        <button className="primary-btn" type="submit" disabled={submittingBaseline || !baselineAuthorityId || baselineReason.trim().length < 3}>
                          {submittingBaseline ? <RefreshCw className="spin" size={14} aria-hidden="true" /> : <ShieldCheck size={14} aria-hidden="true" />}
                          {submittingBaseline ? "Approving" : "Approve baseline"}
                        </button>
                      </div>
                    </div>
                  </form>
                )}

                {showingDraft && (
                  <form className="method-version-create-r82" onSubmit={event => submitVersion(event, method)} noValidate>
                    <div className="method-version-context-r82">
                      <span>New draft for</span>
                      <strong>{method.name}</strong>
                      <small>{method.product_name} / {method.module_name}</small>
                    </div>
                    <label className="method-field-r82 method-version-label-r82">
                      <span>Version label <b aria-hidden="true">Required</b></span>
                      <input ref={versionRef} value={versionLabel} onChange={event => setVersionLabel(event.target.value)} placeholder="PTP-EVENT-v2" disabled={submittingVersion} maxLength={80} required />
                    </label>
                    <label className="method-field-r82 method-version-summary-r82">
                      <span>Summary <b aria-hidden="true">Optional</b></span>
                      <input value={versionSummary} onChange={event => setVersionSummary(event.target.value)} placeholder="Replay-safe processing candidate" disabled={submittingVersion} maxLength={5000} />
                    </label>
                    <div className="method-version-actions-r82">
                      <span><Info size={13} aria-hidden="true" />New versions are always DRAFT. Only the first baseline can be approved here; later versions use governed learning. A-BOM adoption remains separate.</span>
                      <button className="primary-btn" type="submit" disabled={submittingVersion}>
                        {submittingVersion ? <RefreshCw className="spin" size={14} aria-hidden="true" /> : <Plus size={14} aria-hidden="true" />}
                        {submittingVersion ? "Creating" : "Create draft"}
                      </button>
                    </div>
                  </form>
                )}
              </div>
            );
          })}

          {!loadError && filtered.length === 0 && (
            <div className="method-empty-r82" role="status">
              <GitBranch size={19} aria-hidden="true" />
              <strong>{methods.length === 0 ? "No delivery methods registered" : "No methods match this view"}</strong>
              <span>{methods.length === 0 ? "Register the reusable method identity first; controlled versions can then be created beneath it." : "Adjust the search or product filter to return to the full registry."}</span>
              {methods.length === 0 && catalogReady && <button className="secondary-btn" type="button" onClick={openCreateMethod}><Plus size={14} aria-hidden="true" />Add method</button>}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
