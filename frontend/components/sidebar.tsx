"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import {
  Activity,
  BrainCircuit,
  Building2,
  Boxes,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Database,
  FileWarning,
  GitBranch,
  History,
  Layers3,
  FolderTree,
  LayoutDashboard,
  LibraryBig,
  Network,
  Package,
  Rocket,
  Scale,
  Server,
  TriangleAlert,
  UserRoundCheck,
  UsersRound,
  X,
} from "lucide-react";
import type { HealthResponse } from "@/lib/api";

export const CORE_NAV_ITEMS = [
  { label: "Overview", icon: LayoutDashboard, href: "/" },
  { label: "Issues", icon: FileWarning, href: "/issues" },
  { label: "Evidence Repository", icon: LibraryBig, href: "/knowledge" },
  { label: "Approved Knowledge", icon: CheckCircle2, href: "/approved-knowledge" },
  { label: "Knowledge Recall", icon: History, href: "/recalls" },
] as const;

export const REGISTRY_NAV_ITEMS = [
  { label: "Products", icon: Package, href: "/products" },
  { label: "Modules", icon: FolderTree, href: "/modules" },
  { label: "Clients", icon: Building2, href: "/clients" },
  { label: "Implementations", icon: Boxes, href: "/implementations" },
  { label: "Methods", icon: GitBranch, href: "/methods" },
  { label: "Deployments", icon: Rocket, href: "/deployments" },
  { label: "Dependencies", icon: Network, href: "/dependencies" },
] as const;

export const GOVERNANCE_NAV_ITEMS = [
  { label: "Authority", icon: UserRoundCheck, href: "/authority" },
  { label: "Ownership", icon: UsersRound, href: "/ownership" },
  { label: "Audit", icon: Activity, href: "/audit" },
] as const;

const NAV_DESCRIPTIONS: Record<string, string> = {
  Products: "Delivery product catalog",
  Modules: "Product capability catalog",
  Clients: "Organisations and counterparties",
  Implementations: "Client delivery instances",
  Methods: "Reusable delivery methods",
  Deployments: "Release promotion history",
  Dependencies: "Local A-BOM relationships",
  Authority: "Governed action eligibility",
  Ownership: "Accountability assignments",
  Audit: "Traceable activity history",
};

export const UTILITY_NAV_ITEMS = [
  { label: "AI Runtime", icon: BrainCircuit, href: "/ai-runtime" },
] as const;

// Flat export remains available for route/test compatibility. Visual hierarchy is
// owned by the grouped collections above.
export const NAV_ITEMS = [
  ...CORE_NAV_ITEMS,
  ...REGISTRY_NAV_ITEMS,
  ...GOVERNANCE_NAV_ITEMS,
  ...UTILITY_NAV_ITEMS,
] as const;

type OpenPanel = "registry" | "governance" | "system" | null;

function stateClass(state?: string) {
  if (state === "CONNECTED") return "ok";
  if (state === "UNAVAILABLE") return "bad";
  return "warn";
}

function stateLabel(state?: string) {
  if (state === "CONNECTED") return "Connected";
  if (state === "UNAVAILABLE") return "Unavailable";
  if (state === "NOT_CONFIGURED") return "Not configured";
  return state?.replaceAll("_", " ") || "Checking";
}

function systemSummary(health: HealthResponse | null) {
  if (!health) return { tone: "warn", label: "Checking", detail: "System status is being checked" } as const;
  const states = [
    health.dependencies.api,
    health.dependencies.database,
    health.dependencies.qwen,
    health.dependencies.knowledge_source,
  ];
  if (health.status === "ok" && states.every((state) => state === "CONNECTED")) {
    return { tone: "ok", label: "Healthy", detail: "All monitored services are connected" } as const;
  }
  if (states.some((state) => state === "UNAVAILABLE")) {
    return { tone: "bad", label: "Degraded", detail: "One or more monitored services are unavailable" } as const;
  }
  return { tone: "warn", label: "Attention", detail: "One or more monitored services need attention" } as const;
}

function NavigationLink({
  label,
  href,
  Icon,
  active,
  onNavigate,
}: {
  label: string;
  href: string;
  Icon: typeof LayoutDashboard;
  active: boolean;
  onNavigate?: () => void;
}) {
  return (
    <a
      className={`nav-item ${active ? "active" : ""}`}
      href={href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
    >
      <Icon size={16} strokeWidth={1.8} aria-hidden="true" />
      <span>{label}</span>
    </a>
  );
}

function FlyoutLink({
  label,
  description,
  href,
  Icon,
  active,
  onNavigate,
}: {
  label: string;
  description: string;
  href: string;
  Icon: typeof LayoutDashboard;
  active: boolean;
  onNavigate?: () => void;
}) {
  return (
    <a
      className={`nav-flyout-link ${active ? "active" : ""}`}
      href={href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
    >
      <span className="nav-flyout-icon" aria-hidden="true"><Icon size={17} strokeWidth={1.8} /></span>
      <span className="nav-flyout-copy">
        <strong>{label}</strong>
        <span>{description}</span>
      </span>
      <ChevronRight className="nav-flyout-link-arrow" size={15} strokeWidth={1.9} aria-hidden="true" />
    </a>
  );
}

function NavigationFlyoutGroup({
  label,
  Icon,
  items,
  active,
  open,
  onOpen,
  onClose,
  onToggle,
  onNavigate,
  controlId,
  mobile,
}: {
  label: string;
  Icon: typeof LayoutDashboard;
  items: readonly { label: string; icon: typeof LayoutDashboard; href: string }[];
  active: string;
  open: boolean;
  onOpen: () => void;
  onClose: () => void;
  onToggle: () => void;
  onNavigate?: () => void;
  controlId: string;
  mobile: boolean;
}) {
  const containsActive = items.some((item) => item.label === active);

  return (
    <div
      className={`nav-group nav-flyout-group ${open ? "open" : ""} ${containsActive ? "contains-active" : ""}`}
      onMouseEnter={() => { if (!mobile) onOpen(); }}
      onMouseLeave={() => { if (!mobile) onClose(); }}
      onFocusCapture={() => { if (!mobile) onOpen(); }}
      onBlurCapture={(event) => {
        if (mobile) return;
        const nextTarget = event.relatedTarget as Node | null;
        if (!nextTarget || !event.currentTarget.contains(nextTarget)) onClose();
      }}
    >
      <button
        className={`nav-item nav-group-toggle ${containsActive ? "active-parent" : ""}`}
        type="button"
        aria-expanded={open}
        aria-controls={controlId}
        onClick={onToggle}
      >
        <Icon size={16} strokeWidth={1.8} aria-hidden="true" />
        <span>{label}</span>
        {containsActive && <span className="nav-group-current">{active}</span>}
        <ChevronRight className="nav-group-chevron" size={15} strokeWidth={1.9} aria-hidden="true" />
      </button>

      {open && !mobile && <span className="nav-flyout-bridge-r92" aria-hidden="true" />}

      <div className="nav-flyout" id={controlId} hidden={!open} onMouseEnter={() => { if (!mobile) onOpen(); }}>
        <div className="nav-flyout-head">
          <div>
            <strong>{label}</strong>
            <span>{items.length} workspaces</span>
          </div>
          <button className="nav-flyout-close" type="button" onClick={onClose} aria-label={`Close ${label} navigation`}>
            <X size={17} aria-hidden="true" />
          </button>
        </div>
        <div className="nav-flyout-list" aria-label={`${label} workspaces`}>
          {items.map(({ label: itemLabel, icon: ItemIcon, href }) => (
            <FlyoutLink
              key={itemLabel}
              label={itemLabel}
              description={NAV_DESCRIPTIONS[itemLabel] ?? "Open workspace"}
              href={href}
              Icon={ItemIcon}
              active={active === itemLabel}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export function Sidebar({
  health,
  active = "Overview",
  mobile = false,
  onClose,
  id,
}: {
  health: HealthResponse | null;
  active?: string;
  mobile?: boolean;
  onClose?: () => void;
  id?: string;
}) {
  const [openPanel, setOpenPanel] = useState<OpenPanel>(null);
  const [checkedAtLabel, setCheckedAtLabel] = useState(health?.timestamp ? "Latest health check" : "Checking live services");
  const sidebarRef = useRef<HTMLElement>(null);
  const closeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lockedPanelRef = useRef<"registry" | "governance" | null>(null);
  const summary = systemSummary(health);

  const clearCloseTimer = () => {
    if (closeTimerRef.current !== null) {
      clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  };

  const setLockedFlyout = (panel: "registry" | "governance" | null) => {
    lockedPanelRef.current = panel;
  };

  const closeAllPanels = () => {
    clearCloseTimer();
    setLockedFlyout(null);
    setOpenPanel(null);
  };

  const openFlyoutPanel = (panel: "registry" | "governance") => {
    clearCloseTimer();
    const locked = lockedPanelRef.current;
    if (locked && locked !== panel) return;
    setOpenPanel(panel);
  };

  const scheduleFlyoutClose = (panel: "registry" | "governance") => {
    if (mobile) {
      setOpenPanel((value) => value === panel ? null : value);
      return;
    }
    if (lockedPanelRef.current === panel) return;
    clearCloseTimer();
    closeTimerRef.current = setTimeout(() => {
      closeTimerRef.current = null;
      if (lockedPanelRef.current !== panel) {
        setOpenPanel((value) => value === panel ? null : value);
      }
    }, 280);
  };

  const toggleFlyoutPanel = (panel: "registry" | "governance") => {
    clearCloseTimer();
    if (mobile) {
      setLockedFlyout(null);
      setOpenPanel((value) => value === panel ? null : panel);
      return;
    }
    if (lockedPanelRef.current === panel) {
      setLockedFlyout(null);
      setOpenPanel(null);
      return;
    }
    setLockedFlyout(panel);
    setOpenPanel(panel);
  };

  useEffect(() => {
    closeAllPanels();
  }, [active]);

  useEffect(() => () => clearCloseTimer(), []);

  // Locale-aware time formatting must run after hydration. Node and the browser can
  // format AM/PM casing differently, which would otherwise create an SSR mismatch.
  useEffect(() => {
    if (!health?.timestamp) {
      setCheckedAtLabel("Checking live services");
      return;
    }

    const checkedAt = new Date(health.timestamp);
    if (Number.isNaN(checkedAt.valueOf())) {
      setCheckedAtLabel("Latest health check");
      return;
    }

    setCheckedAtLabel(`Checked ${checkedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`);
  }, [health?.timestamp]);

  useEffect(() => {
    if (!openPanel) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeAllPanels();
      }
    };
    const onPointerDown = (event: PointerEvent) => {
      const sidebar = sidebarRef.current;
      if (sidebar && !sidebar.contains(event.target as Node)) closeAllPanels();
    };

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("pointerdown", onPointerDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("pointerdown", onPointerDown);
    };
  }, [openPanel]);

  const statuses = [
    ["API", health?.dependencies.api, Server],
    ["Database", health?.dependencies.database, Database],
    ["Qwen", health?.dependencies.qwen, BrainCircuit],
    ["Evidence Source", health?.dependencies.knowledge_source, LibraryBig],
  ] as const;

  const stateIcon = (state?: string) => {
    if (state === "CONNECTED") return CheckCircle2;
    if (state === "UNAVAILABLE") return TriangleAlert;
    return CircleHelp;
  };

  const navigate = () => {
    closeAllPanels();
    onClose?.();
  };

  return (
    <aside ref={sidebarRef} id={id} className={`sidebar ${mobile ? "sidebar-mobile" : ""}`} aria-label="Primary navigation">
      <div className="brand-row">
        <a className="brand" href="/" aria-label="CREED overview">
          <span className="brand-mark" aria-hidden="true">
            <Image src="/creed-logo.png" alt="" width={38} height={38} priority className="brand-mark-image" />
          </span>
          <span className="brand-copy">
            <strong>CREED</strong>
          </span>
        </a>
        {mobile && (
          <button className="icon-btn sidebar-close" type="button" onClick={onClose} aria-label="Close navigation" autoFocus>
            <X size={17} aria-hidden="true" />
          </button>
        )}
      </div>

      <nav className="nav nav-primary" aria-label="Assurance workspaces">
        {CORE_NAV_ITEMS.map(({ label, icon: Icon, href }) => (
          <NavigationLink
            key={label}
            label={label}
            href={href}
            Icon={Icon}
            active={active === label}
            onNavigate={navigate}
          />
        ))}

        <NavigationFlyoutGroup
          label="Registry"
          Icon={Layers3}
          items={REGISTRY_NAV_ITEMS}
          active={active}
          open={openPanel === "registry"}
          onOpen={() => openFlyoutPanel("registry")}
          onClose={() => scheduleFlyoutClose("registry")}
          onToggle={() => toggleFlyoutPanel("registry")}
          onNavigate={navigate}
          controlId={`${id || "desktop"}-registry-navigation`}
          mobile={mobile}
        />
        <NavigationFlyoutGroup
          label="Governance"
          Icon={Scale}
          items={GOVERNANCE_NAV_ITEMS}
          active={active}
          open={openPanel === "governance"}
          onOpen={() => openFlyoutPanel("governance")}
          onClose={() => scheduleFlyoutClose("governance")}
          onToggle={() => toggleFlyoutPanel("governance")}
          onNavigate={navigate}
          controlId={`${id || "desktop"}-governance-navigation`}
          mobile={mobile}
        />
      </nav>

      <nav className="nav nav-utility" aria-label="Runtime workspace">
        {UTILITY_NAV_ITEMS.map(({ label, icon: Icon, href }) => (
          <NavigationLink
            key={label}
            label={label}
            href={href}
            Icon={Icon}
            active={active === label}
            onNavigate={navigate}
          />
        ))}
      </nav>

      <div className="sidebar-bottom">
        <button
          className={`system-summary-btn ${summary.tone}`}
          type="button"
          aria-expanded={openPanel === "system"}
          aria-controls={`${id || "desktop"}-system-health`}
          aria-label={`System ${summary.label}. ${summary.detail}`}
          onClick={() => {
            clearCloseTimer();
            setLockedFlyout(null);
            setOpenPanel((value) => value === "system" ? null : "system");
          }}
        >
          <span className="system-summary-icon" aria-hidden="true">
            {summary.tone === "ok" ? <CheckCircle2 size={16} /> : summary.tone === "bad" ? <TriangleAlert size={16} /> : <CircleHelp size={16} />}
          </span>
          <span className="system-summary-copy"><strong>System</strong><span>{summary.label}</span></span>
          <ChevronRight className="system-summary-chevron" size={15} strokeWidth={1.9} aria-hidden="true" />
        </button>

        <div className="system-health-popover" id={`${id || "desktop"}-system-health`} hidden={openPanel !== "system"}>
          <div className="system-health-head">
            <div>
              <strong>System health</strong>
              <span>{checkedAtLabel}</span>
            </div>
            <button className="nav-flyout-close" type="button" onClick={closeAllPanels} aria-label="Close system health">
              <X size={17} aria-hidden="true" />
            </button>
          </div>
          <div className="system-health-list" role="status" aria-live="polite" aria-atomic="true">
            {statuses.map(([label, state, ServiceIcon]) => {
              const StateIcon = stateIcon(state);
              const readable = stateLabel(state);
              return (
                <div className={`system-health-row ${stateClass(state)}`} key={label} aria-label={`${label}: ${readable}`}>
                  <span className="system-health-service" aria-hidden="true"><ServiceIcon size={15} /></span>
                  <span>{label}</span>
                  <span className="system-health-state"><StateIcon size={13} aria-hidden="true" />{readable}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </aside>
  );
}
