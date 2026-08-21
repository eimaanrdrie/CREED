"use client";

import { useMemo, useRef, useState, type FormEvent } from "react";
import {
  AlertCircle,
  Boxes,
  Building2,
  CheckCircle2,
  GitBranch,
  Info,
  Layers3,
  Pencil,
  Plus,
  Search,
  ShieldCheck,
  Trash2,
  UserRoundCheck,
  UsersRound,
  X,
} from "lucide-react";
import {
  createOwnershipAssignment,
  removeOwnershipAssignment,
  updateOwnershipAssignment,
  type DeliveryMethodRecord,
  type HumanAuthorityRecord,
  type ImplementationRecord,
  type ModuleRecord,
  type ProductRecord,
  type ResponsibilityAssignmentRecord,
  type ResponsibilityScope,
  type ResponsibilityType,
} from "@/lib/api";

type Notice = { tone: "ok" | "bad" | "neutral"; text: string } | null;

type Target = {
  id: string;
  name: string;
  context: string;
};

const SCOPE_LABELS: Record<ResponsibilityScope, string> = {
  PRODUCT: "Product",
  MODULE: "Module",
  IMPLEMENTATION: "Implementation",
  METHOD: "Method",
};

const ROLE_LABELS: Record<ResponsibilityType, string> = {
  PRODUCT_OWNER: "Product owner",
  MODULE_OWNER: "Module owner",
  TECHNICAL_OWNER: "Technical owner",
  QA_OWNER: "QA owner",
  IMPLEMENTATION_LEAD: "Implementation lead",
};

const ROLE_BY_SCOPE: Record<ResponsibilityScope, ResponsibilityType[]> = {
  PRODUCT: ["PRODUCT_OWNER", "QA_OWNER"],
  MODULE: ["MODULE_OWNER", "TECHNICAL_OWNER", "QA_OWNER"],
  IMPLEMENTATION: ["IMPLEMENTATION_LEAD", "TECHNICAL_OWNER", "QA_OWNER"],
  METHOD: ["TECHNICAL_OWNER", "QA_OWNER"],
};

const ScopeIcon = ({ scope, size = 15 }: { scope: ResponsibilityScope; size?: number }) => {
  if (scope === "PRODUCT") return <Layers3 size={size} aria-hidden="true" />;
  if (scope === "MODULE") return <Boxes size={size} aria-hidden="true" />;
  if (scope === "IMPLEMENTATION") return <Building2 size={size} aria-hidden="true" />;
  return <GitBranch size={size} aria-hidden="true" />;
};

function sortAssignments(items: ResponsibilityAssignmentRecord[]) {
  return [...items].sort((a, b) =>
    a.scope_type.localeCompare(b.scope_type) ||
    a.scope_name.localeCompare(b.scope_name) ||
    a.responsibility_type.localeCompare(b.responsibility_type),
  );
}

function ownershipError(error: unknown) {
  if (!(error instanceof Error)) return "Ownership change could not be saved.";
  const labels: Record<string, string> = {
    RESPONSIBILITY_ALREADY_ASSIGNED: "That responsibility already has a different owner. Use Reassign so CREED records the transfer explicitly.",
    RESPONSIBILITY_ROLE_NOT_ALLOWED_FOR_SCOPE: "That responsibility role is not valid for the selected scope.",
    RESPONSIBILITY_SCOPE_NOT_FOUND: "The selected product, module, implementation or method no longer exists.",
    AUTHORITY_NOT_FOUND: "The selected authority record no longer exists.",
    AUTHORITY_INACTIVE: "Inactive principals cannot receive a new responsibility assignment.",
    RESPONSIBILITY_NOT_FOUND: "This responsibility assignment no longer exists. Reload the registry.",
  };
  return labels[error.message] ?? `Ownership change could not be saved (${error.message}).`;
}

export function OwnershipRegistryWorkspace({
  initialAssignments,
  products,
  modules,
  implementations,
  methods,
  authorities,
  loadError,
  catalogError,
}: {
  initialAssignments: ResponsibilityAssignmentRecord[];
  products: ProductRecord[];
  modules: ModuleRecord[];
  implementations: ImplementationRecord[];
  methods: DeliveryMethodRecord[];
  authorities: HumanAuthorityRecord[];
  loadError: boolean;
  catalogError: boolean;
}) {
  const [assignments, setAssignments] = useState(() => sortAssignments(initialAssignments));
  const [query, setQuery] = useState("");
  const [scopeFilter, setScopeFilter] = useState<"ALL" | ResponsibilityScope>("ALL");
  const [roleFilter, setRoleFilter] = useState<"ALL" | ResponsibilityType>("ALL");
  const [showCreate, setShowCreate] = useState(false);
  const [scopeType, setScopeType] = useState<ResponsibilityScope>("PRODUCT");
  const [scopeId, setScopeId] = useState("");
  const [responsibilityType, setResponsibilityType] = useState<ResponsibilityType>("PRODUCT_OWNER");
  const [authorityId, setAuthorityId] = useState("");
  const [teamName, setTeamName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editAuthorityId, setEditAuthorityId] = useState("");
  const [editTeamName, setEditTeamName] = useState("");
  const [editReason, setEditReason] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);
  const scopeRef = useRef<HTMLSelectElement>(null);
  const editAuthorityRef = useRef<HTMLSelectElement>(null);

  const activeAuthorities = useMemo(
    () => authorities.filter(item => item.active).sort((a, b) => a.display_name.localeCompare(b.display_name)),
    [authorities],
  );

  const targets = useMemo<Record<ResponsibilityScope, Target[]>>(() => {
    const productNames = new Map(products.map(item => [item.id, item.name]));
    return {
      PRODUCT: products.map(item => ({ id: item.id, name: item.name, context: "Product" })),
      MODULE: modules.map(item => ({
        id: item.id,
        name: item.name,
        context: `${productNames.get(item.product_id) ?? "Unknown product"} / ${item.name}`,
      })),
      IMPLEMENTATION: implementations.map(item => ({
        id: item.id,
        name: item.name,
        context: `${item.client_name} · ${item.product_name} / ${item.module_name} · ${item.release_version}`,
      })),
      METHOD: methods.map(item => ({
        id: item.id,
        name: item.name,
        context: `${item.product_name} / ${item.module_name}`,
      })),
    };
  }, [products, modules, implementations, methods]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return assignments.filter(item => {
      if (scopeFilter !== "ALL" && item.scope_type !== scopeFilter) return false;
      if (roleFilter !== "ALL" && item.responsibility_type !== roleFilter) return false;
      if (!needle) return true;
      return [
        item.scope_name,
        item.scope_context,
        item.display_name,
        item.principal,
        item.team_name ?? "",
        ROLE_LABELS[item.responsibility_type],
        item.id,
      ].some(value => value.toLowerCase().includes(needle));
    });
  }, [assignments, query, scopeFilter, roleFilter]);

  const coveredScopes = new Set(assignments.map(item => `${item.scope_type}:${item.scope_id}`)).size;
  const representedPrincipals = new Set(assignments.map(item => item.authority_id)).size;
  const attentionCount = assignments.filter(item => !item.authority_active).length;
  const prerequisitesReady = !loadError && !catalogError && activeAuthorities.length > 0 && Object.values(targets).some(items => items.length > 0);

  function resetCreate(nextScope: ResponsibilityScope = "PRODUCT") {
    setScopeType(nextScope);
    setScopeId("");
    setResponsibilityType(ROLE_BY_SCOPE[nextScope][0]);
    setAuthorityId("");
    setTeamName("");
  }

  function openCreate() {
    if (!prerequisitesReady) return;
    setEditingId(null);
    setNotice(null);
    setShowCreate(true);
    window.requestAnimationFrame(() => scopeRef.current?.focus());
  }

  function closeCreate() {
    if (submitting) return;
    setShowCreate(false);
    resetCreate();
  }

  function onScopeChange(next: ResponsibilityScope) {
    setScopeType(next);
    setScopeId("");
    setResponsibilityType(ROLE_BY_SCOPE[next][0]);
  }

  async function submitAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!scopeId || !authorityId || !responsibilityType) {
      setNotice({ tone: "bad", text: "Choose a scope target, responsibility and accountable principal." });
      return;
    }
    setSubmitting(true);
    setNotice(null);
    try {
      const created = await createOwnershipAssignment({
        scope_type: scopeType,
        scope_id: scopeId,
        responsibility_type: responsibilityType,
        authority_id: authorityId,
        team_name: teamName.trim() || null,
      });
      const existed = assignments.some(item => item.id === created.id);
      setAssignments(current => sortAssignments([...current.filter(item => item.id !== created.id), created]));
      setShowCreate(false);
      resetCreate();
      setNotice({
        tone: existed ? "neutral" : "ok",
        text: existed
          ? `${ROLE_LABELS[created.responsibility_type]} for ${created.scope_name} is already assigned to ${created.display_name}.`
          : `${created.display_name} is now the ${ROLE_LABELS[created.responsibility_type].toLowerCase()} for ${created.scope_name}.`,
      });
    } catch (error) {
      setNotice({ tone: "bad", text: ownershipError(error) });
    } finally {
      setSubmitting(false);
    }
  }

  function beginEdit(item: ResponsibilityAssignmentRecord) {
    if (savingEdit) return;
    setShowCreate(false);
    setNotice(null);
    setEditingId(item.id);
    setEditAuthorityId(item.authority_id);
    setEditTeamName(item.team_name ?? "");
    setEditReason("");
    window.requestAnimationFrame(() => editAuthorityRef.current?.focus());
  }

  function cancelEdit() {
    if (savingEdit) return;
    setEditingId(null);
    setEditAuthorityId("");
    setEditTeamName("");
    setEditReason("");
  }

  async function saveReassignment(event: FormEvent<HTMLFormElement>, item: ResponsibilityAssignmentRecord) {
    event.preventDefault();
    if (!editAuthorityId) {
      setNotice({ tone: "bad", text: "Choose the accountable principal." });
      return;
    }
    if (editReason.trim().length < 3) {
      setNotice({ tone: "bad", text: "Give a short reason so the ownership transfer is auditable." });
      return;
    }
    setSavingEdit(true);
    setNotice(null);
    try {
      const updated = await updateOwnershipAssignment(item.id, {
        authority_id: editAuthorityId,
        team_name: editTeamName.trim() || null,
        reason: editReason.trim(),
      });
      setAssignments(current => sortAssignments([...current.filter(row => row.id !== updated.id), updated]));
      cancelEdit();
      setNotice({ tone: "ok", text: `${ROLE_LABELS[updated.responsibility_type]} for ${updated.scope_name} is now assigned to ${updated.display_name}.` });
    } catch (error) {
      setNotice({ tone: "bad", text: ownershipError(error) });
    } finally {
      setSavingEdit(false);
    }
  }

  async function removeAssignment(item: ResponsibilityAssignmentRecord) {
    if (editReason.trim().length < 3) {
      setNotice({ tone: "bad", text: "Give a short reason before removing an ownership assignment." });
      return;
    }
    setSavingEdit(true);
    setNotice(null);
    try {
      await removeOwnershipAssignment(item.id, editReason.trim());
      setAssignments(current => current.filter(row => row.id !== item.id));
      cancelEdit();
      setNotice({ tone: "neutral", text: `${ROLE_LABELS[item.responsibility_type]} was removed from ${item.scope_name}; the change remains in Audit.` });
    } catch (error) {
      setNotice({ tone: "bad", text: ownershipError(error) });
    } finally {
      setSavingEdit(false);
    }
  }

  return (
    <div className="page ownership-registry-r87">
      <div className="title-row ownership-registry-title-r87">
        <div>
          <h1>Ownership &amp; responsibility</h1>
          <p className="subtitle">Map accountable people to products, modules, implementations and reusable methods. Ownership clarifies who is responsible; governance authority remains controlled separately.</p>
          <div className="ownership-summary-r87" aria-label="Ownership registry summary">
            <span><strong>{assignments.length}</strong> assignments</span>
            <span><strong>{coveredScopes}</strong> assets covered</span>
            <span><strong>{representedPrincipals}</strong> accountable principals</span>
            <span className={attentionCount ? "attention" : ""}><strong>{attentionCount}</strong> attention</span>
          </div>
        </div>
        {!showCreate && (
          <button className="primary-btn" type="button" onClick={openCreate} disabled={!prerequisitesReady}>
            <Plus size={16} aria-hidden="true" />Assign responsibility
          </button>
        )}
      </div>

      {loadError && (
        <div className="ownership-notice-r87 bad" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <div><strong>Ownership registry unavailable</strong><span>CREED could not load persisted responsibility assignments. No placeholder owners are being shown.</span></div>
        </div>
      )}

      {!loadError && catalogError && (
        <div className="ownership-notice-r87 bad" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <div><strong>Ownership catalogs unavailable</strong><span>Existing assignments remain visible, but CREED could not load scope or authority catalogs required for new assignments.</span></div>
        </div>
      )}

      {!loadError && !catalogError && activeAuthorities.length === 0 && (
        <div className="ownership-notice-r87 neutral" role="status">
          <UserRoundCheck size={16} aria-hidden="true" />
          <div><strong>An active principal is required first</strong><span>Ownership must point to a named Human Authority record so accountability is traceable to one stable principal.</span></div>
          <a className="secondary-btn compact" href="/authority">Open Authority</a>
        </div>
      )}

      {notice && (
        <div className={`ownership-notice-r87 ${notice.tone}`} role={notice.tone === "bad" ? "alert" : "status"}>
          {notice.tone === "ok" ? <CheckCircle2 size={16} aria-hidden="true" /> : notice.tone === "bad" ? <AlertCircle size={16} aria-hidden="true" /> : <Info size={16} aria-hidden="true" />}
          <span>{notice.text}</span>
          <button type="button" onClick={() => setNotice(null)} aria-label="Dismiss notice"><X size={14} aria-hidden="true" /></button>
        </div>
      )}

      {showCreate && prerequisitesReady && (
        <section className="ownership-create-r87" aria-labelledby="ownership-create-title-r87">
          <div className="ownership-create-head-r87">
            <div>
              <h2 id="ownership-create-title-r87">Assign responsibility</h2>
              <p>Assign one current accountable principal per asset and responsibility role. Existing ownership cannot be silently replaced.</p>
            </div>
            <button className="icon-btn" type="button" onClick={closeCreate} disabled={submitting} aria-label="Close ownership form"><X size={16} aria-hidden="true" /></button>
          </div>
          <form className="ownership-create-form-r87" onSubmit={submitAssignment}>
            <label className="ownership-field-r87">
              <span>Scope <b>Required</b></span>
              <select ref={scopeRef} value={scopeType} onChange={event => onScopeChange(event.target.value as ResponsibilityScope)} disabled={submitting}>
                {(Object.keys(SCOPE_LABELS) as ResponsibilityScope[]).map(scope => <option value={scope} key={scope}>{SCOPE_LABELS[scope]}</option>)}
              </select>
              <small>What kind of delivery asset owns the responsibility.</small>
            </label>
            <label className="ownership-field-r87 ownership-target-field-r87">
              <span>Asset <b>Required</b></span>
              <select value={scopeId} onChange={event => setScopeId(event.target.value)} disabled={submitting} required>
                <option value="">Select {SCOPE_LABELS[scopeType].toLowerCase()}</option>
                {targets[scopeType].map(item => <option value={item.id} key={item.id}>{item.name} — {item.context}</option>)}
              </select>
              <small>{targets[scopeType].length ? "Select the persisted CREED asset." : `No ${SCOPE_LABELS[scopeType].toLowerCase()} records are available.`}</small>
            </label>
            <label className="ownership-field-r87">
              <span>Responsibility <b>Required</b></span>
              <select value={responsibilityType} onChange={event => setResponsibilityType(event.target.value as ResponsibilityType)} disabled={submitting}>
                {ROLE_BY_SCOPE[scopeType].map(role => <option value={role} key={role}>{ROLE_LABELS[role]}</option>)}
              </select>
              <small>Roles are constrained by the selected scope.</small>
            </label>
            <label className="ownership-field-r87">
              <span>Accountable principal <b>Required</b></span>
              <select value={authorityId} onChange={event => setAuthorityId(event.target.value)} disabled={submitting} required>
                <option value="">Select active principal</option>
                {activeAuthorities.map(item => <option value={item.id} key={item.id}>{item.display_name} — {item.role_title}</option>)}
              </select>
              <small>Uses the stable principal from Human Authority.</small>
            </label>
            <label className="ownership-field-r87">
              <span>Team <b>Optional</b></span>
              <input value={teamName} onChange={event => setTeamName(event.target.value)} maxLength={180} disabled={submitting} placeholder="e.g. Collections Delivery" />
              <small>Team context only; accountability remains attached to the named principal.</small>
            </label>
            <div className="ownership-create-context-r87">
              <ShieldCheck size={15} aria-hidden="true" />
              <span>Responsibility is not permission. This assignment does not grant Human Decision, learning approval or recall authorization rights.</span>
            </div>
            <div className="ownership-create-actions-r87">
              <button className="secondary-btn" type="button" onClick={closeCreate} disabled={submitting}>Cancel</button>
              <button className="primary-btn" type="submit" disabled={submitting || targets[scopeType].length === 0}>{submitting ? "Assigning…" : "Assign responsibility"}</button>
            </div>
          </form>
        </section>
      )}

      <section className="ownership-ledger-r87" aria-labelledby="ownership-ledger-title-r87">
        <div className="ownership-ledger-head-r87">
          <div><h2 id="ownership-ledger-title-r87">Responsibility ledger</h2><span>{filtered.length} shown of {assignments.length}</span></div>
          <div className="ownership-ledger-controls-r87">
            <label className="ownership-search-r87">
              <Search size={15} aria-hidden="true" />
              <input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search asset, owner or team" aria-label="Search ownership registry" />
              {query && <button type="button" onClick={() => setQuery("")} aria-label="Clear ownership search"><X size={13} /></button>}
            </label>
            <label className="ownership-filter-r87"><span className="sr-only">Filter scope</span><select value={scopeFilter} onChange={event => setScopeFilter(event.target.value as "ALL" | ResponsibilityScope)}><option value="ALL">All scopes</option>{(Object.keys(SCOPE_LABELS) as ResponsibilityScope[]).map(scope => <option value={scope} key={scope}>{SCOPE_LABELS[scope]}</option>)}</select></label>
            <label className="ownership-filter-r87"><span className="sr-only">Filter responsibility</span><select value={roleFilter} onChange={event => setRoleFilter(event.target.value as "ALL" | ResponsibilityType)}><option value="ALL">All responsibilities</option>{(Object.keys(ROLE_LABELS) as ResponsibilityType[]).map(role => <option value={role} key={role}>{ROLE_LABELS[role]}</option>)}</select></label>
          </div>
        </div>

        {loadError ? (
          <div className="ownership-empty-r87 bad"><AlertCircle size={20} /><strong>Responsibility ledger unavailable</strong><span>Restore database/API access and reload this workspace.</span></div>
        ) : filtered.length === 0 ? (
          <div className="ownership-empty-r87"><UsersRound size={20} /><strong>{assignments.length ? "No matching assignments" : "No responsibilities assigned"}</strong><span>{assignments.length ? "Adjust the search or filters." : "Map accountable principals to delivery assets so ownership is explicit during investigation and remediation."}</span>{assignments.length === 0 && prerequisitesReady && <button className="secondary-btn" type="button" onClick={openCreate}>Assign first responsibility</button>}</div>
        ) : (
          <div className="ownership-table-r87">
            <div className="ownership-table-columns-r87" aria-hidden="true"><span>Asset</span><span>Responsibility</span><span>Accountable principal</span><span>State</span><span>Action</span></div>
            {filtered.map(item => {
              const editing = editingId === item.id;
              return (
                <article className={`ownership-record-r87 ${!item.authority_active ? "needs-attention" : ""}`} key={item.id}>
                  <div className="ownership-row-r87">
                    <div className="ownership-asset-r87" data-label="Asset"><span className="ownership-scope-icon-r87"><ScopeIcon scope={item.scope_type} /></span><span><strong>{item.scope_name}</strong><small>{item.scope_context}</small><code>{item.scope_type} · {item.scope_id}</code></span></div>
                    <div className="ownership-role-r87" data-label="Responsibility"><strong>{ROLE_LABELS[item.responsibility_type]}</strong><code>{item.responsibility_type}</code></div>
                    <div className="ownership-principal-r87" data-label="Accountable principal"><UserRoundCheck size={15} aria-hidden="true" /><span><strong>{item.display_name}</strong><small>{item.authority_role_title}{item.team_name ? ` · ${item.team_name}` : ""}</small><code>{item.principal}</code></span></div>
                    <div className="ownership-state-r87" data-label="State">{item.authority_active ? <span className="ownership-state-label-r87 ok"><CheckCircle2 size={13} /> Active principal</span> : <span className="ownership-state-label-r87 warn"><AlertCircle size={13} /> Principal inactive</span>}<small>Updated {new Date(item.updated_at).toLocaleDateString()}</small></div>
                    <div className="ownership-action-r87" data-label="Action"><button className="secondary-btn compact" type="button" onClick={() => editing ? cancelEdit() : beginEdit(item)} disabled={savingEdit}><Pencil size={13} aria-hidden="true" />{editing ? "Close" : "Maintain"}</button></div>
                  </div>
                  {editing && (
                    <form className="ownership-maintain-r87" onSubmit={event => saveReassignment(event, item)}>
                      <div className="ownership-maintain-head-r87"><div><strong>Maintain ownership</strong><span>Reassignment and removal require a reason and are recorded in Audit.</span></div></div>
                      <label className="ownership-field-r87"><span>Accountable principal <b>Required</b></span><select ref={editAuthorityRef} value={editAuthorityId} onChange={event => setEditAuthorityId(event.target.value)} disabled={savingEdit}>{activeAuthorities.map(authority => <option value={authority.id} key={authority.id}>{authority.display_name} — {authority.role_title}</option>)}</select></label>
                      <label className="ownership-field-r87"><span>Team <b>Optional</b></span><input value={editTeamName} onChange={event => setEditTeamName(event.target.value)} maxLength={180} disabled={savingEdit} /></label>
                      <label className="ownership-field-r87 ownership-reason-field-r87"><span>Change reason <b>Required</b></span><textarea value={editReason} onChange={event => setEditReason(event.target.value)} disabled={savingEdit} placeholder="Why is accountability changing?" /></label>
                      <div className="ownership-maintain-actions-r87"><button className="secondary-btn danger" type="button" onClick={() => void removeAssignment(item)} disabled={savingEdit}><Trash2 size={13} />Remove assignment</button><span className="ownership-maintain-spacer-r87" /><button className="secondary-btn" type="button" onClick={cancelEdit} disabled={savingEdit}>Cancel</button><button className="primary-btn" type="submit" disabled={savingEdit}>{savingEdit ? "Saving…" : "Save reassignment"}</button></div>
                    </form>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
