"use client";

import { useMemo, useRef, useState, type FormEvent } from "react";
import {
  AlertCircle,
  CheckCircle2,
  CircleOff,
  Info,
  KeyRound,
  Pencil,
  Plus,
  RotateCcw,
  Search,
  ShieldCheck,
  UserRoundCheck,
  X,
} from "lucide-react";
import {
  createHumanAuthority,
  updateHumanAuthority,
  type HumanAuthorityRecord,
} from "@/lib/api";

type Notice = { tone: "ok" | "bad" | "neutral"; text: string } | null;

type AuthorityDraft = {
  display_name: string;
  role_title: string;
  active: boolean;
  can_submit_human_decision: boolean;
  can_approve_learning: boolean;
  can_authorize_recall: boolean;
};

function sortAuthorities(items: HumanAuthorityRecord[]) {
  return [...items].sort((a, b) =>
    Number(b.active) - Number(a.active) ||
    a.display_name.localeCompare(b.display_name) ||
    a.principal.localeCompare(b.principal),
  );
}

function authorityError(error: unknown, action: "create" | "update") {
  if (!(error instanceof Error)) return `Authority record could not be ${action === "create" ? "registered" : "updated"}.`;
  const labels: Record<string, string> = {
    AUTHORITY_PRINCIPAL_ALREADY_EXISTS: "That principal already exists with different authority settings. Edit the existing record instead.",
    AUTHORITY_NOT_FOUND: "This authority record no longer exists. Reload the registry.",
  };
  return labels[error.message] ?? `Authority record could not be ${action === "create" ? "registered" : "updated"} (${error.message}).`;
}

function permissionsCount(item: HumanAuthorityRecord | AuthorityDraft) {
  return Number(item.can_submit_human_decision) + Number(item.can_approve_learning) + Number(item.can_authorize_recall);
}

function draftFrom(item: HumanAuthorityRecord): AuthorityDraft {
  return {
    display_name: item.display_name,
    role_title: item.role_title,
    active: item.active,
    can_submit_human_decision: item.can_submit_human_decision,
    can_approve_learning: item.can_approve_learning,
    can_authorize_recall: item.can_authorize_recall,
  };
}

export function HumanAuthorityWorkspace({
  initialAuthorities,
  loadError,
}: {
  initialAuthorities: HumanAuthorityRecord[];
  loadError: boolean;
}) {
  const [authorities, setAuthorities] = useState(() => sortAuthorities(initialAuthorities));
  const [query, setQuery] = useState("");
  const [stateFilter, setStateFilter] = useState<"ALL" | "ACTIVE" | "INACTIVE">("ALL");
  const [showCreate, setShowCreate] = useState(false);
  const [principal, setPrincipal] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const [active, setActive] = useState(true);
  const [canDecide, setCanDecide] = useState(false);
  const [canApproveLearning, setCanApproveLearning] = useState(false);
  const [canRecall, setCanRecall] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState<AuthorityDraft | null>(null);
  const [savingEdit, setSavingEdit] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);
  const principalRef = useRef<HTMLInputElement>(null);
  const editRoleRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return authorities.filter(item => {
      if (stateFilter === "ACTIVE" && !item.active) return false;
      if (stateFilter === "INACTIVE" && item.active) return false;
      if (!needle) return true;
      return [item.display_name, item.principal, item.role_title, item.id].some(value => value.toLowerCase().includes(needle));
    });
  }, [authorities, query, stateFilter]);

  const activeCount = authorities.filter(item => item.active).length;
  const decisionCount = authorities.filter(item => item.active && item.can_submit_human_decision).length;
  const learningCount = authorities.filter(item => item.active && item.can_approve_learning).length;
  const recallCount = authorities.filter(item => item.active && item.can_authorize_recall).length;

  function resetCreate() {
    setPrincipal("");
    setDisplayName("");
    setRoleTitle("");
    setActive(true);
    setCanDecide(false);
    setCanApproveLearning(false);
    setCanRecall(false);
  }

  function openCreate() {
    if (loadError) return;
    setEditingId(null);
    setEditDraft(null);
    setNotice(null);
    setShowCreate(true);
    window.requestAnimationFrame(() => principalRef.current?.focus());
  }

  function closeCreate() {
    if (submitting) return;
    setShowCreate(false);
    resetCreate();
  }

  async function submitAuthority(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedPrincipal = principal.trim();
    const cleanedDisplayName = displayName.trim();
    const cleanedRole = roleTitle.trim();
    if (cleanedPrincipal.length < 3) {
      setNotice({ tone: "bad", text: "Principal must contain at least 3 characters." });
      principalRef.current?.focus();
      return;
    }
    if (cleanedDisplayName.length < 2 || cleanedRole.length < 2) {
      setNotice({ tone: "bad", text: "Display name and role title must each contain at least 2 characters." });
      return;
    }

    setSubmitting(true);
    setNotice(null);
    try {
      const created = await createHumanAuthority({
        principal: cleanedPrincipal,
        display_name: cleanedDisplayName,
        role_title: cleanedRole,
        active,
        can_submit_human_decision: canDecide,
        can_approve_learning: canApproveLearning,
        can_authorize_recall: canRecall,
      });
      const existed = authorities.some(item => item.id === created.id);
      setAuthorities(current => sortAuthorities([...current.filter(item => item.id !== created.id), created]));
      setNotice({
        tone: existed ? "neutral" : "ok",
        text: existed
          ? `${created.display_name} already exists with the same authority configuration.`
          : `${created.display_name} was registered in the human-authority directory.`,
      });
      setShowCreate(false);
      resetCreate();
    } catch (error) {
      setNotice({ tone: "bad", text: authorityError(error, "create") });
    } finally {
      setSubmitting(false);
    }
  }

  function beginEdit(item: HumanAuthorityRecord) {
    if (savingEdit) return;
    setShowCreate(false);
    resetCreate();
    setNotice(null);
    setEditingId(item.id);
    setEditDraft(draftFrom(item));
    window.requestAnimationFrame(() => editRoleRef.current?.focus());
  }

  function cancelEdit() {
    if (savingEdit) return;
    setEditingId(null);
    setEditDraft(null);
  }

  async function saveEdit(event: FormEvent<HTMLFormElement>, item: HumanAuthorityRecord) {
    event.preventDefault();
    if (!editDraft) return;
    const cleanedName = editDraft.display_name.trim();
    const cleanedRole = editDraft.role_title.trim();
    if (cleanedName.length < 2 || cleanedRole.length < 2) {
      setNotice({ tone: "bad", text: "Display name and role title must each contain at least 2 characters." });
      return;
    }

    setSavingEdit(true);
    setNotice(null);
    try {
      const updated = await updateHumanAuthority(item.id, {
        ...editDraft,
        display_name: cleanedName,
        role_title: cleanedRole,
      });
      setAuthorities(current => sortAuthorities([...current.filter(row => row.id !== updated.id), updated]));
      setEditingId(null);
      setEditDraft(null);
      setNotice({ tone: "ok", text: `${updated.display_name}'s authority configuration was updated and audited.` });
    } catch (error) {
      setNotice({ tone: "bad", text: authorityError(error, "update") });
    } finally {
      setSavingEdit(false);
    }
  }

  return (
    <div className="page authority-registry-r84">
      <div className="title-row authority-registry-title-r84">
        <div>
          <h1>Human Authority</h1>
          <p className="subtitle">
            Register named human principals and the governed CREED actions they are eligible to perform.
            Governed endpoints now enforce this directory; identity authentication remains outside this registry.
          </p>
          <div className="authority-summary-r84" aria-label="Authority registry summary">
            <span><strong>{authorities.length}</strong> registered</span>
            <span><strong>{activeCount}</strong> active</span>
            <span><strong>{decisionCount}</strong> human decision</span>
            <span><strong>{learningCount}</strong> learning approval</span>
            <span><strong>{recallCount}</strong> recall authorization</span>
          </div>
        </div>
        <button className="primary-btn" type="button" onClick={openCreate} disabled={loadError || showCreate}>
          <Plus size={15} aria-hidden="true" /> Add authority
        </button>
      </div>

      {showCreate && (
        <section className="authority-create-r84" aria-labelledby="authority-create-title">
          <div className="authority-create-head-r84">
            <div>
              <h2 id="authority-create-title">Register authority</h2>
              <p>Use a stable corporate principal or username. The principal becomes the immutable audit identity for this registry entry.</p>
            </div>
            <button className="icon-btn" type="button" onClick={closeCreate} disabled={submitting} aria-label="Close authority form">
              <X size={16} aria-hidden="true" />
            </button>
          </div>
          <form className="authority-create-form-r84" onSubmit={submitAuthority}>
            <label className="authority-field-r84">
              <span>Principal <b>Required</b></span>
              <input ref={principalRef} value={principal} onChange={event => setPrincipal(event.target.value)} placeholder="name@company.com or username" disabled={submitting} />
              <small>Stable identifier used for audit attribution. It cannot be edited after registration.</small>
            </label>
            <label className="authority-field-r84">
              <span>Display name <b>Required</b></span>
              <input value={displayName} onChange={event => setDisplayName(event.target.value)} placeholder="Aisha Rahman" disabled={submitting} />
            </label>
            <label className="authority-field-r84">
              <span>Role title <b>Required</b></span>
              <input value={roleTitle} onChange={event => setRoleTitle(event.target.value)} placeholder="Transformation Assurance Lead" disabled={submitting} />
            </label>

            <fieldset className="authority-scope-r84">
              <legend>Governed authority</legend>
              <label><input type="checkbox" checked={canDecide} onChange={event => setCanDecide(event.target.checked)} disabled={submitting} /><span><ShieldCheck size={15} /> Submit human decision</span></label>
              <label><input type="checkbox" checked={canApproveLearning} onChange={event => setCanApproveLearning(event.target.checked)} disabled={submitting} /><span><CheckCircle2 size={15} /> Approve learning</span></label>
              <label><input type="checkbox" checked={canRecall} onChange={event => setCanRecall(event.target.checked)} disabled={submitting} /><span><RotateCcw size={15} /> Authorize recall</span></label>
            </fieldset>

            <label className="authority-active-r84">
              <input type="checkbox" checked={active} onChange={event => setActive(event.target.checked)} disabled={submitting} />
              <span><strong>Active authority</strong><small>Inactive principals remain in the registry for traceability but should not be selected for governed work.</small></span>
            </label>

            <div className="authority-create-context-r84">
              <Info size={14} aria-hidden="true" />
              <span>CREED now enforces these permissions for Human Decision, learning approval and recall authorization. The selected principal is still a caller-supplied identity, not an authenticated login.</span>
            </div>
            <div className="authority-create-actions-r84">
              <button className="secondary-btn" type="button" onClick={closeCreate} disabled={submitting}>Cancel</button>
              <button className="primary-btn" type="submit" disabled={submitting}>{submitting ? "Registering…" : "Register authority"}</button>
            </div>
          </form>
        </section>
      )}

      {notice && (
        <div className={`authority-notice-r84 ${notice.tone}`} role={notice.tone === "bad" ? "alert" : "status"}>
          {notice.tone === "bad" ? <AlertCircle size={16} /> : notice.tone === "ok" ? <CheckCircle2 size={16} /> : <Info size={16} />}
          <span>{notice.text}</span>
          <button type="button" onClick={() => setNotice(null)} aria-label="Dismiss notice"><X size={14} /></button>
        </div>
      )}

      <section className="authority-ledger-r84" aria-labelledby="authority-ledger-title">
        <div className="authority-ledger-head-r84">
          <div>
            <h2 id="authority-ledger-title">Authority directory</h2>
            <p>Named principals, role context and configured governance eligibility.</p>
          </div>
          <div className="authority-ledger-controls-r84">
            <label className="authority-search-r84">
              <Search size={15} aria-hidden="true" />
              <input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search name, principal or role" aria-label="Search authority directory" />
              {query && <button type="button" onClick={() => setQuery("")} aria-label="Clear authority search"><X size={13} /></button>}
            </label>
            <label className="authority-state-filter-r84">
              <span className="sr-only">Filter authority state</span>
              <select value={stateFilter} onChange={event => setStateFilter(event.target.value as "ALL" | "ACTIVE" | "INACTIVE")}>
                <option value="ALL">All states</option>
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
              </select>
            </label>
          </div>
        </div>

        {loadError ? (
          <div className="authority-empty-r84 bad">
            <AlertCircle size={20} />
            <strong>Authority directory unavailable</strong>
            <span>CREED could not load the persisted authority registry. No placeholder principals are being shown.</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="authority-empty-r84">
            <UserRoundCheck size={20} />
            <strong>{authorities.length === 0 ? "No human authorities registered" : "No matching principals"}</strong>
            <span>{authorities.length === 0 ? "Register a named principal before wiring governed actions to an authority directory." : "Adjust the search or state filter."}</span>
            {authorities.length === 0 && <button className="secondary-btn" type="button" onClick={openCreate}>Add first authority</button>}
          </div>
        ) : (
          <div className="authority-table-r84">
            <div className="authority-table-columns-r84" aria-hidden="true">
              <span>Principal</span><span>Role</span><span>Governed authority</span><span>State</span><span>Action</span>
            </div>
            {filtered.map(item => {
              const editing = editingId === item.id && editDraft;
              return (
                <div className="authority-record-r84" key={item.id}>
                  <div className="authority-row-r84">
                    <div className="authority-person-r84">
                      <span className="authority-person-icon-r84"><UserRoundCheck size={15} /></span>
                      <span>
                        <strong>{item.display_name}</strong>
                        <code>{item.principal}</code>
                        <small>{item.id}</small>
                      </span>
                    </div>
                    <div className="authority-role-r84" data-label="Role">
                      <strong>{item.role_title}</strong>
                    </div>
                    <div className="authority-permissions-r84" data-label="Governed authority">
                      {item.can_submit_human_decision && <span><ShieldCheck size={13} /> Human decision</span>}
                      {item.can_approve_learning && <span><CheckCircle2 size={13} /> Learning approval</span>}
                      {item.can_authorize_recall && <span><RotateCcw size={13} /> Recall authorization</span>}
                      {permissionsCount(item) === 0 && <span className="none"><KeyRound size={13} /> No governed action</span>}
                    </div>
                    <div className={`authority-state-r84 ${item.active ? "active" : "inactive"}`} data-label="State">
                      {item.active ? <CheckCircle2 size={13} /> : <CircleOff size={13} />}
                      <span>{item.active ? "Active" : "Inactive"}</span>
                    </div>
                    <div className="authority-action-r84">
                      <button className="secondary-btn compact" type="button" onClick={() => beginEdit(item)} disabled={savingEdit || editingId === item.id}>
                        <Pencil size={13} /> Edit
                      </button>
                    </div>
                  </div>

                  {editing && (
                    <form className="authority-edit-r84" onSubmit={event => saveEdit(event, item)}>
                      <div className="authority-edit-context-r84">
                        <KeyRound size={15} />
                        <span><strong>{item.principal}</strong><small>Principal is immutable. Changes below are audited against this identity.</small></span>
                      </div>
                      <label>
                        <span>Display name</span>
                        <input value={editDraft.display_name} onChange={event => setEditDraft({ ...editDraft, display_name: event.target.value })} disabled={savingEdit} />
                      </label>
                      <label>
                        <span>Role title</span>
                        <input ref={editRoleRef} value={editDraft.role_title} onChange={event => setEditDraft({ ...editDraft, role_title: event.target.value })} disabled={savingEdit} />
                      </label>
                      <fieldset className="authority-edit-scope-r84">
                        <legend>Governed authority</legend>
                        <label><input type="checkbox" checked={editDraft.can_submit_human_decision} onChange={event => setEditDraft({ ...editDraft, can_submit_human_decision: event.target.checked })} disabled={savingEdit} /><span>Human decision</span></label>
                        <label><input type="checkbox" checked={editDraft.can_approve_learning} onChange={event => setEditDraft({ ...editDraft, can_approve_learning: event.target.checked })} disabled={savingEdit} /><span>Learning approval</span></label>
                        <label><input type="checkbox" checked={editDraft.can_authorize_recall} onChange={event => setEditDraft({ ...editDraft, can_authorize_recall: event.target.checked })} disabled={savingEdit} /><span>Recall authorization</span></label>
                      </fieldset>
                      <label className="authority-edit-active-r84">
                        <input type="checkbox" checked={editDraft.active} onChange={event => setEditDraft({ ...editDraft, active: event.target.checked })} disabled={savingEdit} />
                        <span>{editDraft.active ? "Active" : "Inactive"}</span>
                      </label>
                      <div className="authority-edit-actions-r84">
                        <button className="secondary-btn" type="button" onClick={cancelEdit} disabled={savingEdit}>Cancel</button>
                        <button className="primary-btn" type="submit" disabled={savingEdit}>{savingEdit ? "Saving…" : "Save authority"}</button>
                      </div>
                    </form>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
