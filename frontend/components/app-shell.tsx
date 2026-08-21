"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { ChevronRight, Menu, ShieldCheck, UserRound } from "lucide-react";
import type { HealthResponse } from "@/lib/api";
import { Sidebar } from "./sidebar";

export type Breadcrumb = { label: string; href?: string };

export function AppShell({
  health,
  active,
  breadcrumbs,
  children,
}: {
  health: HealthResponse | null;
  active: string;
  breadcrumbs?: Breadcrumb[];
  children: ReactNode;
}) {
  const [navOpen, setNavOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const navDialogRef = useRef<HTMLDivElement>(null);
  const crumbs = breadcrumbs?.length ? breadcrumbs : [{ label: active }];

  useEffect(() => {
    if (!navOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setNavOpen(false);
        return;
      }

      if (event.key !== "Tab") return;
      const dialog = navDialogRef.current;
      if (!dialog) return;
      const focusable = Array.from(
        dialog.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      ).filter((element) => !element.hasAttribute("hidden"));
      if (!focusable.length) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
      window.requestAnimationFrame(() => menuButtonRef.current?.focus());
    };
  }, [navOpen]);

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <div className="shell">
        <Sidebar health={health} active={active} />
        <main className="main" id="main-content" tabIndex={-1}>
          <header className="topbar">
            <div className="topbar-left">
              <button
                ref={menuButtonRef}
                className="icon-btn mobile-menu"
                type="button"
                aria-label="Open navigation"
                aria-expanded={navOpen}
                aria-controls="mobile-primary-navigation"
                onClick={() => setNavOpen(true)}
              >
                <Menu size={17} aria-hidden="true" />
              </button>
              <nav className="crumb" aria-label="Breadcrumb">
                <a href="/" className="crumb-home crumb-home-icon" aria-label="CREED overview"><ShieldCheck size={14} aria-hidden="true" /></a>
                {crumbs.map((crumb, index) => (
                  <span className="crumb-segment" key={`${crumb.label}-${index}`}>
                    <ChevronRight size={12} aria-hidden="true" />
                    {crumb.href ? <a href={crumb.href}>{crumb.label}</a> : <strong aria-current="page">{crumb.label}</strong>}
                  </span>
                ))}
              </nav>
            </div>
            <div className="user-chip" aria-label="Current role: Assurance Lead, Project Delivery">
              <div className="user-copy" aria-hidden="true">
                <strong>Assurance Lead</strong>
                <span className="user-role-detail">Project Delivery</span>
              </div>
              <span className="avatar" aria-hidden="true"><UserRound size={15} strokeWidth={1.8} /></span>
            </div>
          </header>
          {children}
        </main>

        {navOpen && (
          <div ref={navDialogRef} className="mobile-nav-layer" role="dialog" aria-modal="true" aria-label="Primary navigation menu">
            <button className="mobile-nav-backdrop" type="button" aria-label="Close navigation" onClick={() => setNavOpen(false)} />
            <Sidebar id="mobile-primary-navigation" health={health} active={active} mobile onClose={() => setNavOpen(false)} />
          </div>
        )}
      </div>
    </>
  );
}
