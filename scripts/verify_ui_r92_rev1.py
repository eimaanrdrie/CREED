from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sidebar = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
design = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
notes = (ROOT / "UI_R92_REV1_NOTES.md").read_text(encoding="utf-8")

checks = {
    "pointer bridge element": 'nav-flyout-bridge-r92' in sidebar and 'open && !mobile' in sidebar,
    "pointer bridge css": all(token in css for token in ['.nav-flyout-bridge-r92', 'left:100%', 'width:14px', 'pointer-events:auto']),
    "mobile bridge disabled": '.sidebar-mobile .nav-flyout-bridge-r92 { display:none; }' in css,
    "grace timer": '}, 280);' in sidebar and 'scheduleFlyoutClose' in sidebar and 'clearCloseTimer' in sidebar,
    "hover still opens": 'onMouseEnter={() => { if (!mobile) onOpen(); }}' in sidebar,
    "flyout reentry cancels close": '<div className="nav-flyout" id={controlId} hidden={!open} onMouseEnter={() => { if (!mobile) onOpen(); }}>' in sidebar,
    "click lock state": all(token in sidebar for token in ['lockedPanelRef', 'setLockedFlyout', 'toggleFlyoutPanel']),
    "pinned panel resists hover steal": 'if (locked && locked !== panel) return;' in sidebar,
    "outside and escape close lock": sidebar.count('closeAllPanels();') >= 4 and 'event.key === "Escape"' in sidebar and 'pointerdown' in sidebar,
    "keyboard focus opens": 'onFocusCapture={() => { if (!mobile) onOpen(); }}' in sidebar,
    "keyboard blur bounded close": 'onBlurCapture={(event)' in sidebar and 'onClose();' in sidebar,
    "mobile stays tap driven": 'if (mobile) {' in sidebar and 'setOpenPanel((value) => value === panel ? null : panel);' in sidebar,
    "registry wiring": 'onOpen={() => openFlyoutPanel("registry")}' in sidebar and 'onClose={() => scheduleFlyoutClose("registry")}' in sidebar,
    "governance wiring": 'onOpen={() => openFlyoutPanel("governance")}' in sidebar and 'onClose={() => scheduleFlyoutClose("governance")}' in sidebar,
    "design contract": 'UI-R92 REV1 — Registry/Governance Flyout Interaction Fix' in design and '280ms grace period' in design,
    "notes candidate": 'Status: candidate, awaiting user approval.' in notes and 'Frontend sidebar interaction only.' in notes,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
if failed:
    raise SystemExit("UI-R92 REV1 verifier failed: " + ", ".join(failed))
print("UI-R92 REV1 verifier PASS")
