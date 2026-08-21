# CREED UI Design System — Assurance Ledger

## Visual direction

CREED is an operational assurance product. The redesign uses an Impeccable-inspired dark mineral/lacquer system adapted to core-banking delivery governance: precise, quiet, technical, and evidence-led.

### Principles

- Operate first: scanability, task completion, provenance and state clarity outrank decorative expression.
- Deep navy surfaces, not pure black.
- Azure blue is the primary interaction/brand accent; use it sparingly.
- Cyan/teal represents validated/healthy/trusted states.
- Small radii, hairline structure, almost no decorative shadow.
- Avoid cards nested inside cards when a divider, row, or grid can carry the hierarchy.
- Use geometric/system sans typography with monospace metadata labels.
- Motion must preserve hierarchy and respect `prefers-reduced-motion`.
- All interface icons come from `lucide-react`. Do not add emoji, inline SVG icon sets, or text arrows as icon substitutes.

## Tokens

Primary tokens live in `app/globals.css` using OKLCH values.

- `--bg`, `--bg-deep`: deep navy application surfaces
- `--panel`, `--panel-soft`, `--panel-raised`: layered navy working surfaces
- `--azure`, `--azure-strong`, `--azure-pale`: brand/action hierarchy
- `--cyan`, `--trusted`: secondary/trusted state language
- `--gold`, `--gold-pale`, `--verdigris`: compatibility aliases retained for approved component contracts
- `--amber`: warning/pending
- `--red`: failed/revoked/destructive
- `--line`, `--line-strong`: calibration hairlines
- radii: 3px / 5px / 7px
- spacing: 8 / 16 / 24 / 32 / 48

## Shared primitives

- `.primary-btn`, `.secondary-btn`, `.ghost-btn`
- `.card`
- `.panel-head`
- `.status-pill`
- `.step-icon`
- `.title-row`
- `.page`

New screens should reuse these before inventing page-specific primitives.

## Navigation

The persistent desktop sidebar separates daily assurance work from setup/governance administration.

First-level operational navigation:

1. Overview
2. Issues
3. Change Radar
4. Knowledge
5. Recalls
6. Registry (collapsible)
7. Governance (collapsible)

Registry contains Products, Modules, Clients, Implementations, Methods, Deployments and Dependencies. Governance contains Authority, Ownership and Audit. Both groups are collapsed by default and automatically open when the current route is inside that group. AI Runtime remains a separate utility workspace above live System status.

There is no Demo tab or Demo route in the product interface.

## Change Radar

Change Radar is an operational reasoning surface, not a decorative network graph.

- Use a left-to-right causal hierarchy: source/recall → method version → implementations.
- Custom React Flow nodes must encode role and state without relying on colour alone.
- Impact mode shows investigation priority, never a final affected/safe declaration.
- Recall mode shows explicit dependency routing, never an automatic defect declaration.
- The inspector must expose signal value, configured weight, contribution and supporting evidence IDs.
- Evidence references open the stored evidence record rather than acting as inert labels.
- Filtering may hide implementation nodes but must preserve the source and method context.
- React Flow controls and MiniMap remain functional; node dragging/connection editing are disabled because this is an assurance inspection surface, not a graph authoring tool.


## UI-R06 — Evidence Intelligence Workspace

The Knowledge area is an operational evidence surface, not a document-gallery page.

Primary jobs:
1. **Find** — hybrid retrieval + governed evidence registry.
2. **Inspect** — source text, parse/index state, provenance and full SHA-256 content seal.
3. **Ingest** — add human-supplied project evidence and make the post-ingestion lifecycle explicit.

Rules:
- Never expose the internal `LOCAL_DEMO` identifier in operator-facing copy; display **Local Repository**.
- Retrieval scores are prioritisation signals, not approval/compliance scores.
- Evidence detail must expose the actual parsed source text used for retrieval.
- Parse/index/embedding degradation states remain visible.
- Evidence ingestion is human-supplied source material; it does not validate business meaning.
- All interface icons remain from `lucide-react`.


## UI-R07 — Recalls & Governance Artefacts

Recall is a governed withdrawal workflow, not a warning feed.

Primary jobs:
1. **Authorize** — a human selects currently approved knowledge, an evidence-bearing source issue, identity and rationale.
2. **Seal** — CREED creates a Signed Recall Notice with human attestation and SHA-256 integrity.
3. **Route** — only explicit Local A-BOM `USES_METHOD_VERSION` adopters become recall obligations.
4. **Inspect** — the notice exposes source evidence, exact hash, authority, routed implementations and investigation IDs.

Rules:
- Revocation is visually destructive and always requires explicit human authority.
- Qwen cannot revoke organisational knowledge.
- Recall routing never means an implementation is proven defective.
- Historical adoption is preserved; recall records the later withdrawal rather than erasing prior approval.
- Integrity must be visible on both registry and notice-detail surfaces.
- The full SHA-256 content seal must be copyable and independently verified through the backend verifier endpoint.
- Signed Recall Notices are printable governance artefacts.
- All interface icons remain from `lucide-react`.


## UI-R08 — Glass-Box Trace Workspace

Audit is an operational reconstruction surface, not a raw log dump.

Primary jobs:
1. **Reconstruct** — show one chronological trace across issue, agents, Qwen, evidence, impact, humans and governance.
2. **Inspect** — reveal persisted execution metadata, failure state, model identity, duration, token counts and evidence references.
3. **Prove provenance** — expose evidence SHA-256 seals and integrity-sealed adoption/recall artefacts.
4. **Separate authority** — AI findings/proposals and human authority events must be visually distinct.

Rules:
- Never display hidden chain-of-thought or imply that internal reasoning is an audit artefact.
- Global mode is a governance/runtime activity view; run mode reconstructs one graph run.
- Qwen failures remain visible and are never normalized into success.
- Impact values remain investigation-priority signals, not final affected/safe decisions.
- Evidence access must drill into the stored source record and full SHA-256 seal.
- Adoption and recall records link to their governed artefact views and show integrity state.
- All interface icons remain from `lucide-react`.


## UI-R09 — Local AI Control Plane

AI Runtime is an execution-proof surface, not a decorative model-status page.

Primary jobs:
1. **Handshake** — prove Ollama reachability, configured-model availability and schema-validated inference.
2. **Execute** — let an operator trigger a real structured Qwen call and inspect returned JSON, latency and tokens.
3. **Prove** — show persisted successful and failed Qwen execution records with actual/configured model identity and runtime errors.
4. **Recover** — expose truthful unavailable/not-installed states and a concrete recovery path without manufacturing a healthy state.

Rules:
- READY is shown only when the backend runtime probe reports READY.
- A loopback Ollama URL may be labelled LOOPBACK; any other endpoint is only CONFIGURED, not automatically certified as local.
- Never replace failed Qwen execution with canned content.
- Runtime history exposes execution provenance, not hidden chain-of-thought.
- All interface icons remain from `lucide-react`.

## UI-R10 — Responsive & Accessibility Baseline

The redesigned product must remain operable without a mouse and across small/coarse-pointer devices.

Rules:
- Provide a skip-to-main-content link on every application surface.
- Primary navigation exposes `aria-current=page`; mobile navigation closes with Escape and restores focus to its trigger.
- Dynamic failures use alert semantics; long-running backend work uses polite status semantics.
- Coarse-pointer controls use a 44px minimum target; mobile form controls use a 16px text floor to avoid browser zoom.
- Technical IDs, SHA-256 values, model errors and source text must wrap/scroll without causing horizontal page overflow.
- Respect `prefers-reduced-motion` and `prefers-contrast`.
- Do not use colour as the only state indicator; status text and semantic labels remain present.
- The final product contains no Demo route/tab and no icon source other than `lucide-react`.


## UI-R12 — Deep Navy + Azure Blue

The approved R11 structure now uses a cool fintech palette: deep navy shell/surfaces, Azure for action and focus, cyan/teal for trusted states, amber for pending/degraded and red for failed/revoked/destructive. The palette change is visual only; governance and runtime semantics are unchanged.

## UI-R22 visual minimalism layer

CREED now follows a three-layer information model:

1. **Glance** — number, state, relationship, or current action is visible first.
2. **Inspect** — operational explanation appears only when the user selects the relevant object/stage.
3. **Prove** — evidence, hashes, model/runtime provenance, deterministic signals, and governance records remain available on demand.

The rule is reduction by hierarchy, not reduction by font size. Dynamic evidence and authority-bearing records must never be hidden merely to make the interface look cleaner.

## UI-R30 — Minimal AI Runtime + Visual-Minimalism Closure

AI Runtime now follows **Glance → Execute → Prove**:
- Show Ollama → Qwen → schema → CREED runtime state first.
- Make a real structured Qwen call the dominant action.
- Show classification, validation, latency, tokens and actual model at a glance.
- Keep JSON, run IDs and detailed runtime provenance behind progressive disclosure.
- Keep failure and recovery visible; never compress unavailable states into a healthy-looking summary.
- Keep LOOPBACK distinct from merely CONFIGURED endpoints.

R23–R30 complete the R22 visual-minimalism pass across Overview, Issues/Intake, Analysis, Change Radar, Knowledge, Recalls, Audit and AI Runtime. Reduction is achieved through hierarchy and progressive disclosure, not smaller typography or removal of evidence/governance proof.

## UI-R31 — Width-Safe System Status

The persistent sidebar must never compress service health into horizontally competing mini-cards. System health is a vertical compact list: service identity on the left, actual backend-derived state on the right. Long degraded/unavailable states wrap inside the row rather than widening or clipping the sidebar. This is a layout correction only; health semantics remain unchanged.

## UI-R33 — Width-Safe Issue Metadata

Issue severity, type and attachment count are compact signals inside the case identity, not independent fixed columns. The metadata lane may wrap, but individual enum/count chips stay horizontal. Nested chip text must not inherit generic issue-ledger span clamping/margins. Real issue values remain visible at the approved type scale; reflow is preferred over shrinking or clipping.

## UI-R34 — Overflow Regression Contract

The R30 visual-minimalism system plus R31-R33 targeted fixes now share one width-safety contract: dynamic text must stay inside its owning surface; controls reflow before they overflow; hashes/run IDs break safely; technical preformatted source may scroll locally; and the application viewport remains free of horizontal scrolling. Readable typography is preserved rather than reduced to make layouts fit.

## UI-R35 — AI Runtime Hydration / Execution Proof Contract
- Runtime timestamps rendered during SSR must use an explicit locale and timezone; never use environment-default locale/timezone formatting in hydration-sensitive output.
- Execution proof must reflow around long model names, run IDs, durations and timestamps rather than widening the page.
- Runtime proof data remains complete; progressive disclosure may reduce visual density but must not fabricate or discard provenance.

## UI-R49 — Analysis Workbench Foundation

Analysis is an **Operate-mode investigation workbench**, not a dashboard of equal-weight cards.

Primary reading/task path:
1. Identify the case and real execution state.
2. Move through Case Context → Evidence → Investigation → Human Decision.
3. Keep live agent execution and the human-authority boundary visible as a secondary rail.
4. Open deeper source/model/evidence proof only when inspection requires it.

Structural rules:
- One major boundary per work zone; functional submodules inside the zone use separators rather than nested card chrome.
- The case header is compact and operational: title, essential case facts, real run ID/state, and the real run action.
- The agent rail is secondary to investigation content and remains truthful to persisted/SSE backend lifecycle events.
- Human source and Qwen interpretation are grouped but remain semantically and visually distinct.
- Evidence and impact remain proof/prioritisation inputs; neither becomes a human verdict through layout or colour.
- At constrained content widths, the workbench reflows from two columns to one without shrinking readable type or hiding governance proof.
- Deep Navy + Azure Blue, Lucide-only icons, GLANCE → INSPECT → PROVE, and existing Human Authority semantics remain unchanged.

## UI-R50 — Analysis Visual Signal Strip + Case Summary

The Analysis workbench now uses a **state-first visual summary** before detailed investigation content.

Reading hierarchy:
1. **Current state** — the backend run state or currently executing AgentStep leads the surface.
2. **Case signals** — case severity/type, persisted Qwen interpretation, evidence count, impact candidates, AI finding labels, and Human Authority status are shown as one shared hairline-separated band rather than independent metric cards.
3. **Analysis path** — the lifecycle tracker follows the real graph topology exactly: Intake → Retrieval → Knowledge Link → Impact → Investigation → Evidence Validator → Human Review.
4. **Work zones** — Case Context → Evidence → Investigation → Human Decision remain the detailed task path from R49.

Truth rules:
- Run state and active agent come only from persisted/SSE `AnalysisRun` / `AgentStep` lifecycle data.
- Evidence and candidate counts come from backend step metadata emitted by the executing retrieval and impact nodes.
- AI finding labels are read from persisted investigation records; they remain AI findings, not human verdicts.
- Human decision summaries are read from persisted human-review records. `WAITING_HUMAN` remains visibly distinct from a completed decision.
- Qwen confidence is extraction confidence only; it is not impact probability, safety, or human authority.
- No timer-derived progress, fabricated counts, fake finding labels, or inferred governance decisions are introduced.
- One outer signal surface with hairline separation is preferred to a row of card widgets; colour is used only to reinforce labelled state.
- At constrained container widths, the signals and lifecycle tracker reflow structurally while preserving readable type and DOM/task order.

## UI-R51 — Investigation Master/Detail Workbench

The Investigation zone now uses an **Operate-mode master/detail workbench** rather than separate Impact and Findings cards.

Reading hierarchy:
1. **Candidate rail** — ranked implementations show deterministic priority, client context and persisted AI-finding state in one compact list.
2. **Selected implementation** — one implementation owns the detail surface at a time; selection changes presentation only and does not recalculate backend data.
3. **Deterministic priority** — score signals and contributions remain visibly separate from AI interpretation.
4. **AI investigation** — Qwen's persisted finding, confidence and validation state are shown as investigation output, never as a human verdict.
5. **Proof + Human Authority** — evidence references and recorded/pending human decision remain inspectable without competing with the primary task flow.

Rules:
- Impact score remains an investigation-priority signal, not proof of defect or affected status.
- Candidate ordering uses persisted impact/risk values already returned by the backend; the UI does not invent a probability.
- AI finding labels remain `POTENTIALLY_AFFECTED`, `NO_SUPPORTING_EVIDENCE_OF_IMPACT`, or `INSUFFICIENT_EVIDENCE`.
- Human decisions remain `AFFECTED`, `NOT_AFFECTED`, or `NEEDS_MORE_INVESTIGATION` and visually remain a separate authority source.
- Evidence references displayed in proof come only from persisted impact/finding records.
- The master/detail layout reflows by Analysis container width, not only browser viewport width.
- GLANCE → INSPECT → PROVE, Deep Navy + Azure Blue, Lucide-only iconography, and approved backend/LangGraph/Qwen semantics remain unchanged.

## UI-R52 — Analysis Evidence Ledger + Proof Inspector

The Evidence zone now uses an **Operate-mode master/detail evidence workbench** rather than a ranked teaser row plus expanded card ledger.

Reading hierarchy:
1. **Ranked evidence ledger** — persisted retrieval hits are the navigation surface, ordered exactly as returned by backend retrieval.
2. **Selected evidence** — one retrieved chunk owns the inspector at a time; selecting it changes frontend focus only.
3. **Retrieved excerpt** — the text actually returned by retrieval is shown before deeper provenance.
4. **Ranking signals** — semantic, keyword, metadata, query-coverage and issue-link contributions explain why the chunk surfaced.
5. **Traceability + provenance** — document ID, chunk ID, matched queries, stored source, parse/index state, embedding model and SHA-256 remain inspectable.

Rules:
- Retrieval score is ranking/prioritisation, not proof that a document is correct, current, or approved.
- The excerpt comes only from the persisted retrieval hit; the UI does not rewrite or summarise source evidence.
- Stored provenance is loaded from the existing document-detail API for the selected document. Failure to load it remains visible; the UI does not fabricate source metadata.
- Internal `LOCAL_DEMO` source keys remain operator-facing as `LOCAL REPOSITORY`.
- SHA-256 is a content-integrity seal, not a human approval or PKI signature.
- Full source inspection continues through the existing Knowledge surface; Analysis does not duplicate the entire document repository.
- Evidence master/detail reflows by the real Analysis container width and retains readable type rather than shrinking proof.
- GLANCE → INSPECT → PROVE, Deep Navy + Azure Blue, Lucide-only iconography, and approved retrieval/Qwen/LangGraph/Human Authority semantics remain unchanged.

## UI-R53 — Human Authority + Decision Workbench

The Human Decision zone now uses an **Operate-mode authority workbench** rather than repeated decision cards.

Reading hierarchy:
1. **Authority command** — persisted Human Review state leads; `WAITING_HUMAN` is shown as a paused governed boundary rather than generic workflow status.
2. **Review-case rail** — implementation cases are navigation. AI finding type and draft/recorded human state remain visible without competing for primary authority.
3. **Selected case** — one implementation owns the decision surface at a time.
4. **AI investigation context** — the persisted AI finding, confidence and evidence-reference count are advisory inputs only.
5. **Human decision** — `AFFECTED`, `NOT_AFFECTED`, or `NEEDS_MORE_INVESTIGATION` plus rationale is the action-bearing surface and visually outranks the AI finding.
6. **Governed handoff** — after review completion, any Qwen learning proposal appears downstream and remains explicitly unapproved until separate human learning approval.

Rules:
- AI findings never become final labels through colour, typography or placement.
- Human decisions are persisted separately from model output and are the governed outcome.
- Submission remains complete-review/atomic: every implementation needs a decision and rationale before the existing resume call is available.
- Reviewer identity remains the approved `Transformation Assurance Lead` value already used by the frontend contract.
- The UI does not manufacture review cases, findings, evidence counts, decisions, reviewer identity from model text, or workflow state.
- A learning proposal is not presented as adopted knowledge; separate human learning approval remains required.
- Master/detail selection changes frontend focus only and does not alter investigation records.
- The workbench reflows by Analysis container width, preserving readable type and 44px action targets.
- Deep Navy + Azure Blue, Lucide-only iconography, GLANCE → INSPECT → PROVE, and approved Qwen/LangGraph/retrieval/governance semantics remain unchanged.

## UI-R54 — Analysis Execution Rail + Responsive Closure

The redesigned Analysis workspace closes with one **execution-proof rail** rather than another dashboard panel.

Reading hierarchy:
1. **Current execution** — the persisted `AnalysisRun` / currently `RUNNING` or `WAITING_HUMAN` step leads the rail.
2. **Lifecycle counts** — completed, active, queued and failed counts are derived from the actual AgentStep states.
3. **Agent chronology** — every backend graph step remains visible with status, task, duration and inspectable persisted output/error.
4. **Decision authority** — the rail ends with the governance boundary: AI execution is observable, but final authority remains human.

Rules:
- No timer-derived progress, fabricated completion percentage, inferred agent state or fake success is introduced.
- The rail is sticky only while it has a dedicated desktop column; once the workbench reflows to one column it becomes a normal bounded proof surface.
- The lifecycle list may scroll locally only in the dedicated desktop rail. Compact/single-column layouts remove the nested scroll region.
- Existing backend/SSE lifecycle semantics, Human Review interrupt/resume, Qwen, retrieval, impact, evidence, learning and recall behavior remain unchanged.
- Dynamic IDs, hashes, model names and proof strings wrap inside their owning surfaces rather than widening the page.
- Deep Navy + Azure Blue, Lucide-only iconography, readable typography, 44px actions, and GLANCE → INSPECT → PROVE remain the Analysis visual contract.

## UI-R55 — Analysis Header + State Compression

The Analysis first viewport now applies an Impeccable **DISTILL → CLARIFY → LAYOUT** pass. It is an Operate surface: the case, current governed state, real signals and graph progress lead; secondary proof begins only after the operator reaches the workbench.

Reading hierarchy:
1. **Issue identity** — issue title, client/ticket/attachment metadata, and quiet run identity.
2. **Current state** — one compact backend-driven state bar. `WAITING_HUMAN` is an amber action/governance state, never a failure state.
3. **Essential signals** — case severity/type, Qwen confidence/verification state, evidence count, candidate count and human-decision count share one low-height inline strip.
4. **Analysis path** — seven real graph stages remain visible without boxed stage cards or repeated `DONE` labels. Completed stages recede; only current, waiting or failed stages receive strong emphasis.
5. **Case Context** — detailed work begins immediately after the compressed orientation layer.

Rules:
- State and counts remain derived from `AnalysisRun`, `AgentStep`, persisted Issue Understanding, retrieval/impact metadata and Human Review records; no frontend timer or fabricated percentage is introduced.
- Human Review uses the run-level `WAITING_HUMAN` state as the governing visual state even if a stale step payload would otherwise render ambiguously.
- `FAILED` alone receives failure-red treatment; `WAITING_HUMAN` is amber, `COMPLETED` trusted/teal, and `CANCELLED` remains visually muted rather than being presented as a defect verdict.
- Ticket/run identity does not compete with the issue title and long identifiers wrap inside the container.
- Previous R49–R54 workbench modules remain functionally intact below this first-viewport distillation.

## UI-R56 — Case Context Distillation

`01 Case context` now applies an Impeccable **DISTILL → CLARIFY** pass. The default view is a direct source-vs-model comparison rather than two verbose cards.

Reading hierarchy:
1. **Human Source** — origin and a short clamped excerpt of the exact persisted issue description.
2. **AI Interpretation** — persisted extraction confidence plus Product, Module, Issue type and suspected Function.
3. **Material mismatch** — source/Qwen client mismatch remains visible because it changes review context.
4. **Inspect** — original ticket metadata/full text and complete Qwen extraction/runtime proof are progressively disclosed.

Rules:
- R56 never rewrites or invents a human-source summary; the glance excerpt is the original description constrained by CSS.
- Full Qwen summary, keywords, warnings, model identity, tokens and execution proof remain available, but no longer dominate the default Case Context view.
- Human Source and AI Interpretation remain separate information classes and neither is visually presented as a governed final decision.
- Verify/Re-run and persisted human verification behavior remain unchanged.
- The comparison reflows by Analysis container width without compressing important text.
- Deep Navy + Azure Blue, Lucide-only iconography, GLANCE → INSPECT → PROVE, truthful runtime semantics and human authority remain unchanged.

## UI-R57 — Evidence Distillation

`02 Evidence` now applies an Impeccable **DISTILL → LAYOUT** pass. The default view answers only what evidence surfaced, how strongly it ranked, and which excerpt is relevant; retrieval mechanics and provenance remain available behind Inspect.

Reading hierarchy:
1. **Retrieval summary** — source count and searched-chunk count are the only always-visible retrieval metrics.
2. **Ranked sources** — persisted retrieval order, document identity, one persisted-query reason and retrieval match provide the navigation surface.
3. **Selected evidence** — one source owns the inspector at a time, with source/type context and a four-line excerpt.
4. **Read full excerpt** — the complete retrieved source text is available without dominating the default viewport.
5. **Inspect proof** — semantic/keyword/metadata signals, score adjustments, document/chunk IDs, matched queries and stored provenance are progressively disclosed.
6. **Retrieval details** — search concepts and the ranking-not-validation boundary are available on demand rather than permanently occupying the Evidence zone.

Rules:
- The UI never rewrites the source excerpt or invents a retrieval reason. The one-line reason uses the first persisted matched query when available, otherwise the persisted citation location.
- Retrieval score is ranking priority, not source validation, human authority, or proof that an implementation is affected.
- Source provenance is still loaded through the existing document-detail API and failures remain explicit.
- Internal `LOCAL_DEMO` remains operator-facing as `LOCAL REPOSITORY`.
- The master/detail surface reflows by Analysis container width and clamps default-visible text before reducing readable typography.
- Deep Navy + Azure Blue, Lucide-only iconography, GLANCE → INSPECT → PROVE, and approved Qwen/LangGraph/Human Authority semantics remain unchanged.

## UI-R58 — Investigation Visual Matrix

`03 Investigation` now applies an Impeccable **LAYOUT → TYPESET → DISTILL** pass. It is a comparison surface first and a proof surface second.

Reading hierarchy:
1. **Candidate matrix** — implementations are compared in one flat operating table using persisted priority, AI finding and Human Authority state.
2. **Selected implementation** — one low-height identity rail shows only Priority, AI finding and Evidence count.
3. **Priority drivers** — only the top three deterministic contributors are default-visible; complete signal/value/weight detail is Inspect content.
4. **AI finding** — persisted finding label, confidence and a three-line clamp of the exact finding statement are default-visible; the complete statement and validation state are Inspect content.
5. **Evidence** — persisted evidence-reference count and a short exact-ID preview are default-visible; complete references remain in proof.
6. **Proof** — impact basis, complete evidence refs and Human Authority stay available behind progressive disclosure.

Rules:
- Candidate order and priority values come from persisted impact/risk records; the frontend does not calculate a defect probability.
- Priority is investigation priority only and never becomes a defect verdict through typography, colour, ordering or copy.
- AI findings remain advisory persisted model output and remain visually distinct from Human Authority.
- The frontend clamps long AI prose rather than rewriting or summarising it.
- Evidence preview uses exact persisted IDs; no synthetic evidence explanation is introduced.
- Use flat rows, separators and aligned data roles rather than nested cards. Default-visible words must justify their place.
- Typography favors Operate-mode scanability: stable roles, tabular numeric signals and short readable measures.
- The matrix and selected-inspection lanes reflow by the real Analysis container width.
- Deep Navy + Azure Blue, Lucide-only iconography, GLANCE → INSPECT → PROVE, and approved Qwen/LangGraph/retrieval/governance semantics remain unchanged.

## UI-R59 — Human Decision Focus Mode

`04 Human decision` now applies an Impeccable **CLARIFY → DISTILL** pass. When the real LangGraph run is waiting on `WAITING_HUMAN`, the governed human task becomes the dominant surface and AI context recedes to Inspect.

Reading hierarchy:
1. **Human Authority** — one compact action header states whether governed review is required or already recorded.
2. **Implementation list** — review cases remain selectable, but default-visible metadata is limited to persisted priority, AI finding label and human-review state.
3. **Selected implementation** — one low-height rail shows Priority, AI advisory label and persisted evidence-reference count.
4. **Human decision** — `AFFECTED`, `NOT_AFFECTED`, or `NEEDS_MORE_INVESTIGATION` is the primary action. Decision descriptions remain accessible but no longer occupy the visual surface.
5. **Rationale** — appears only after a governed decision has been selected, reducing inactive-form noise.
6. **Why did AI suggest this?** — full persisted AI statement, confidence and exact evidence references move behind progressive disclosure.
7. **Submit** — review completeness and the existing atomic resume action remain visible without repeating governance prose.

Rules:
- Human Authority must visually outrank AI findings whenever `WAITING_HUMAN` is active.
- AI finding text is advisory context only and is never promoted into a final decision by placement, colour or wording.
- Priority remains investigation priority, not a defect verdict.
- Human decisions and rationales remain persisted separately from model output through the existing Human Review resume API.
- No review case, priority value, AI finding, confidence or evidence-reference count is invented by the frontend.
- The complete AI statement is not rewritten or summarized; it is simply moved behind Inspect.
- The three approved human decision enum values and the 3–3000 character rationale contract remain unchanged.
- The decision workbench reflows by the real Analysis container width and retains readable type plus 44px primary action targets.
- Deep Navy + Azure Blue, Lucide-only iconography, GLANCE → INSPECT → PROVE, and approved Qwen/LangGraph/retrieval/governance semantics remain unchanged.

## UI-R60 — Execution Proof Distillation + Hardening

The Analysis right rail now applies an Impeccable **DISTILL → HARDEN** pass. It is execution telemetry only: current backend state, run identity, lifecycle counts and a compact agent timeline. Investigation prose, model conclusions and raw runtime object dumps do not belong in this rail.

Reading hierarchy:
1. **Current execution** — the persisted `AnalysisRun` / current `RUNNING` or `WAITING_HUMAN` stage leads with one concise operational state.
2. **Run identity** — graph run ID remains inspectable but visually quiet.
3. **Lifecycle summary** — completed, running/waiting and failed counts come only from persisted `AgentStep` state.
4. **Agent timeline** — seven stages show name, real lifecycle status and measured duration without repeating task prose.
5. **Execution details** — one progressive disclosure exposes only bounded operational facts such as module, actual model, confidence, evidence/chunk counts, candidate/investigation counts and evidence-gap counts.
6. **Errors** — operator-facing error copy is bounded and sanitized; persisted technical details remain available in Audit rather than rendering raw Python/LangGraph object dumps in Analysis.

Rules:
- The rail must never display `GraphInterrupt(...)`, traceback text, serialized interrupt payloads, investigation statements or other long runtime object representations as default operator copy.
- Sanitizing display text does not change, delete or overwrite persisted execution data; Audit remains the deeper proof surface.
- `WAITING_HUMAN` is a governed waiting state, not a failure. It uses amber, while only real failed execution uses red.
- No frontend timer, fake completion count, synthetic duration, invented model, inferred evidence count or fabricated agent state is introduced.
- The rail contains no repeated Human Authority explanation because Human Decision owns that task surface.
- Seven lifecycle rows fit without an internal scrollbar; single-column layouts therefore avoid nested scrolling completely.
- Long run IDs and model names wrap or truncate inside their owning surface instead of widening the page.
- Deep Navy + Azure Blue, Lucide-only iconography, GLANCE → INSPECT → PROVE, and approved Qwen/LangGraph/retrieval/governance semantics remain unchanged.

## UI-R61 — Full Analysis Adapt + Polish Closure

The complete Analysis surface now applies the final Impeccable **ADAPT → POLISH** pass. R55–R60 established the task hierarchy; R61 removes leftover page-level card chrome and duplicate helper copy so the surface reads as one operating flow rather than a dashboard assembled from modules.

Reading hierarchy:
1. **Orientation** — issue identity, current real state, essential signals and graph path.
2. **Case Context** — human source vs Qwen interpretation.
3. **Evidence** — ranked sources and selected proof.
4. **Investigation** — candidate comparison and one selected analysis.
5. **Human Decision** — governed action when review is required.
6. **Run Telemetry** — secondary execution proof, visually quieter than the main task.

Rules:
- Major zones use whitespace and hairlines; nested task workbenches own the minimum boundary needed for orientation.
- Default-visible helper prose is removed when the heading and data already explain the task.
- Adaptation happens before typography becomes cramped: the execution rail leaves sticky/two-column mode at the Analysis container threshold rather than waiting for browser viewport collapse.
- Long IDs, hashes, model names, evidence references and proof facts must wrap or truncate inside their owners and must never widen the Analysis page.
- Progressive disclosure uses one consistent rhythm across source proof, evidence proof, AI analysis, Human Authority proof, learning proof and execution details.
- R61 does not rewrite persisted human input, model output, evidence or governance records; it changes presentation only.
- Deep Navy + Azure Blue, Lucide-only iconography, GLANCE → INSPECT → PROVE, truthful backend lifecycle state and Human Authority semantics remain unchanged.

## UI-R62 — Analysis Workspace Navigation + Execution Consolidation

R62 changes Analysis information architecture without changing backend semantics.

- The long top Analysis Path is removed from the rendered page because the right rail already carries the real persisted LangGraph lifecycle.
- `Case Context`, `Evidence`, `Investigation`, and `Human Decision` are now local workspace choices. Only one workspace is rendered at a time.
- Workspace counts are derived from real persisted step metadata (`evidence_count`, `candidate_count`, `result_count`).
- `Human Decision` receives an amber action indicator only when the real run state is `WAITING_HUMAN`; waiting remains distinct from failure.
- The selected workspace is written to the URL as `?view=context|evidence|investigation|human` and restored after mount, so refresh/navigation can preserve the operator's working context without introducing a hydration mismatch.
- The right rail is renamed **Agent Execution Task** and becomes the single visual lifecycle surface. It continues to display only persisted execution telemetry and bounded proof; no fake progress, raw GraphInterrupt payload, hidden chain-of-thought, or repeated investigation prose is added.
- Approved R56–R60 workspace content remains intact inside each selectable view.


## UI-R63 — Case Context readability and action contrast
- Case Context is now an isolated workspace under the R62 navigator, so the human-supplied issue description is shown in full by default rather than clamped.
- Verify is a high-contrast Azure action; Re-run is a dark secondary action with a legible disabled state.
- Disabled actions remain visually readable without implying availability; backend/runtime gating is unchanged.
- No data, Qwen, LangGraph, retrieval, governance, or Human Authority semantics changed.


## UI-R63 REV1 — Analysis action visibility + thin scrollbar
- The Investigation `Radar` handoff uses an Analysis-scoped dark Azure action instead of inheriting the legacy light `secondary-btn compact` rule.
- `Radar` remains a navigation handoff to the existing Change Radar route and does not alter impact, investigation, or graph state.
- Root and Analysis-owned scrollbars use a quiet thin rail so scrolling remains discoverable without competing with workspace content.
- The R62 workspace-tab scrollbar remains intentionally hidden because the tabs already use direct horizontal navigation and that behavior is approved.
- Verify/Re-run contrast and the full human-source description from R63 remain unchanged.
- No backend, Qwen, LangGraph, retrieval, Human Authority, learning, adoption, recall, or Audit semantics changed.

## UI-R64 — Case Context hierarchy + action system

R64 is a precision Impeccable **CLARIFY → DISTILL → TYPESET** pass on the isolated Case Context workspace.

- Human Source owns slightly more horizontal reading space because the operator must understand the original reported issue before interpreting model output.
- Verify is the single Azure primary action. Re-run is a dark secondary action and keeps the existing real runtime guard/disabled state.
- `Inspect model interpretation` is a quiet progressive-disclosure action rather than a third competing button.
- The Qwen glance shows confidence and structured-output status first; generic warning chips do not compete with those primary signals.
- A client extraction mismatch is rendered adjacent to the client comparison itself (`Qwen client` vs `Source client`) instead of as an unrelated top-level warning.
- Product, Module, Issue type and Function are presented as lightweight definition fields rather than nested mini-cards.
- `Not extracted` remains truthful but visually recedes so missing optional extraction fields do not outrank useful values.
- The complete human-supplied issue description remains default-visible, and the complete persisted Qwen interpretation remains available behind Inspect.
- No backend, Qwen/Ollama, LangGraph, retrieval, impact, Human Authority, learning, adoption, recall or Audit semantics change.

## UI-R65 — Evidence workspace visual distillation

R65 is a precision Impeccable **DISTILL → LAYOUT** pass on the isolated Evidence workspace.

- The workspace opens with one quiet retrieval summary (`sources · chunks searched`) instead of repeating an Evidence title already present in the workspace navigator.
- Search concepts and the retrieval-score boundary remain behind `Retrieval details` so retrieval mechanics do not compete with source inspection.
- Ranked source rows show only rank, document identity, one persisted match reason and retrieval match percentage.
- The selected source inspector leads with document identity, source/type context, match, and a short persisted retrieval excerpt.
- The default excerpt is limited to three lines; the complete retrieved source text remains available verbatim behind `Read full excerpt`.
- `Open source` is a clear secondary handoff to Knowledge without becoming the primary Analysis action.
- Semantic/keyword/metadata scores, score adjustments, document/chunk IDs, matched queries, SHA-256, embedding state, parse/index state and stored provenance remain behind `Inspect proof`.
- Retrieval ranking remains prioritisation only; it does not establish source correctness, Human Authority, or an affected verdict.
- No evidence text is rewritten, summarized, fabricated or re-ranked by the frontend.
- No backend, retrieval algorithm, Qwen/Ollama, LangGraph, impact, Human Review, learning, adoption, recall, API or Audit semantics change.

## UI-R66 — Investigation comparison matrix refinement

R66 is a precision Impeccable **LAYOUT → TYPESET → DISTILL** pass on the isolated Investigation workspace.

- Candidate comparison remains the default glance state and is reduced to four aligned facts: implementation, persisted priority, persisted AI finding label, and persisted Human Authority state.
- The decorative row arrow is removed; selected-row treatment alone communicates which implementation is being inspected.
- The selected implementation is a compact orientation rail rather than a second dashboard: implementation/client identity plus Priority, AI finding and evidence-reference count.
- Default-visible detail is limited to two areas: the three strongest deterministic priority drivers and a two-line persisted AI finding.
- Lower-weight scoring signals remain behind `All signals`; the complete persisted Qwen statement and validation status remain behind `Inspect AI analysis`.
- Evidence IDs are removed from the default investigation view. The evidence count remains visible, while complete persisted references stay behind `Inspect proof`.
- Priority remains investigation priority, not a defect verdict. Human Authority remains separate from the AI finding and is never inferred from score or model output.
- No impact values, finding labels, confidence values, evidence references, Human Authority records, or model statements are rewritten or fabricated by the frontend.
- No backend, deterministic impact, Qwen/Ollama, LangGraph, retrieval, Human Review, learning, adoption, recall, API or Audit semantics change.

## UI-R67 — Human Decision task flow refinement

R67 is a precision Impeccable **CLARIFY → DISTILL** pass on the isolated Human Decision workspace.

- Human review opens as a governed task, not an AI explanation surface: review progress, review queue, selected implementation, human outcome, rationale, then atomic submission.
- Review progress is calculated only from persisted decisions or local draft decisions whose rationale satisfies the existing minimum-length rule; it does not invent workflow completion.
- The review queue remains a selector and visually recedes. The selected implementation carries only orientation signals: deterministic priority, persisted AI advisory label and persisted evidence-reference count.
- The three approved Human Authority outcomes are the strongest controls. Semantic color supports recognition but never changes or infers the backend decision value.
- Decision rationale appears only after a human outcome is selected and retains the approved 3–3000 character contract.
- Full AI finding text, confidence and evidence references remain behind `Why did AI suggest this?`; the model remains advisory and cannot submit or approve a human outcome.
- Submission remains one atomic `resumeHumanReview(...)` action and is available only when every real review item has both a decision and valid rationale.
- Persisted Human Authority records and the governed learning handoff remain unchanged after submission.
- No backend, Qwen/Ollama, LangGraph, SSE, retrieval, impact, investigation, evidence-validation, learning, adoption, recall, API or Audit semantics change.

## UI-R68 — Agent Execution Task refinement
The Analysis rail is the single lifecycle authority. Default-visible content is limited to the current persisted task, its actual state/duration, lifecycle counts, and the compact stage timeline. Run/model/retrieval facts remain under `Execution details`. The rail is narrower on wide screens and yields to normal document flow earlier when the permanent app sidebar reduces real working width. `WAITING_HUMAN` remains an action state, not a failure.

## UI-R69 — Analysis visual system normalization

R69 is a precision Impeccable **POLISH** pass across the already-approved Analysis information architecture. It does not redesign the four workspaces; it makes them visually behave as one product.

- One action hierarchy is used across Analysis: Azure-filled for primary governed/task actions, dark Azure-outline for secondary navigation/handoffs, and quiet text disclosure for Inspect/Proof.
- Workspace tabs, selected evidence rows, selected investigation candidates, and selected Human Review cases share one Azure selection language rather than separate component-specific effects.
- Status chips, source badges and stream state use one compact badge scale.
- Borders are normalized to restrained hairlines; nested chrome is reduced without removing evidence/governance boundaries.
- Progressive disclosures use one quiet rhythm across source, retrieval, AI, Human Authority, learning and execution proof.
- Typography roles are normalized: metadata/kickers recede, task labels remain readable, and `Not extracted` stays truthful but subordinate.
- Human Decision no longer repeats a visible `AI advisory only` label because `AI advisory` is already present in the selected-case signals; the accessibility boundary and full AI proof remain intact.
- Agent Execution Task remains secondary proof and does not compete with the selected workspace.
- No backend, Qwen/Ollama, LangGraph, SSE, retrieval, impact, Human Authority, learning, adoption, recall, API, persistence or Audit semantics change.

## UI-R70 — Analysis responsive + pixel polish closure

R70 is the final Impeccable **ADAPT → POLISH** pass for the approved Analysis information architecture.

- No new Analysis views or backend behaviors are introduced; the R62 four-workspace navigator remains the information architecture.
- The operational case header is restrained at desktop sizes and reflows structurally at laptop/mobile widths rather than shrinking important text.
- Workspace navigation retains stable 44px touch targets on constrained widths and remains horizontally navigable without exposing a competing scrollbar.
- Human Source, evidence excerpts, investigation findings, hashes, run IDs, model names and governance proof values are hardened against overflow while preserving complete persisted content behind the approved disclosure boundaries.
- Case Context actions become a clear two-action mobile row, then stack only at very narrow widths; primary/secondary action semantics from R69 remain unchanged.
- Agent Execution Task continues to yield below the selected workspace at the approved R68 breakpoint and remains lifecycle proof rather than a fifth workspace.
- Mobile decision submission becomes full-width and task oriented; no Human Authority state or submission rule changes.
- Reduced-motion behavior and the thin-scrollbar treatment from R63 REV1 remain preserved.
- No backend, Qwen/Ollama, LangGraph, SSE, retrieval, impact, investigation, Human Review, learning, adoption, recall, API, persistence or Audit semantics change.

## UI-R71 — Editorial Header + Metadata Distillation

This module applies the Impeccable DISTILL direction without changing product semantics or the approved palette.

Rules:
- Route-level headings stand on their own; redundant uppercase eyebrow/kicker labels are removed from page heroes and AI Runtime proof subsections.
- Preserve information carried by a removed label when it is not redundant: for example, the case record ID remains visible as quiet inline metadata.
- Decorative count/status pills in headers become quiet inline metadata.
- Keep compact semantic badges where they encode operational classification or governed state inside dense work surfaces (severity, issue type, AI finding, human decision, impact band, parse/index state).
- Do not use R71 to change sidebar selection treatment, AI Runtime grid/alignment, color tokens, runtime behavior, evidence behavior or governance semantics.


## UI-R72 — Sidebar Active-State / Accent Cleanup

R72 is a narrow Impeccable **QUIETER** pass on the persistent primary navigation only.

- The selected workspace no longer relies on the bright Azure selection stripe or an Azure-tinted active fill.
- Active navigation is expressed with the existing raised navy surface, primary text and a restrained neutral inset rule; the icon follows the supporting text tone.
- Hover remains visibly distinct from selected state but is deliberately quieter than a primary action.
- `aria-current="page"`, navigation destinations, touch-target sizing, mobile drawer behavior, focus-visible treatment and Lucide iconography remain unchanged.
- Increased-contrast mode keeps a stronger neutral inset indicator without reintroducing a bright active accent.
- No route/page content, Analysis workspace state, AI Runtime layout, runtime execution, evidence, Human Authority, governance, palette tokens or backend behavior changes in R72.

## UI-R73 — AI Runtime / Execution Proof Alignment Correction

R73 is a narrow Impeccable **LAYOUT** pass on the runtime execution-proof surface.

- `Recent Qwen calls`, the selected execution heading, selected metrics and `Runtime provenance` share one measured horizontal content rail.
- Recent execution rows keep identity first and align real duration/timestamp metadata as a stable secondary column; numeric timing uses tabular figures.
- Duration, Tokens and Structured are one comparison strip separated by hairlines rather than three nested cards.
- Runtime provenance is the next band in the same selected-execution surface, not another nested card shell.
- Expanded provenance facts use a ruled data grid and reflow structurally from three columns to two and one as the proof container narrows.
- Existing R35/R36/R38 long-value containment remains in force; R73 changes rhythm and geometry, not runtime truth.
- No Qwen/Ollama execution semantics, backend state, Analysis architecture, sidebar treatment, off-white palette tokens, governance behavior or Demo-route policy changes in R73.

## UI-R74 — Off-White Palette Migration

R74 is the approval-gated Impeccable **COLORIZE** migration from the former Deep Navy + Azure emphasis system to the approved off-white-led dark palette. It changes shared color roles only; R75 remains the exhaustive component-consistency pass.

Canonical R74 tokens:
- Background `#071019`
- Surface `#0B1724`
- Raised surface `#102033`
- Primary off-white `#F3EDE3`
- Secondary text `#A8B5C3`
- Muted text `#7D8A98`
- Hairline border `#1B2A3A`
- Action accent `#7CC7D9`
- Success `#6FBF9E`
- Warning `#D6A86B`
- Danger `#C96B6B`

Rules:
- Off-white carries titles, important values and active text; cyan is reserved for action, focus and selected/proof accents.
- Dark navy remains the structural foundation. Surface and raised-surface roles are explicit; no light/porcelain background migration occurs in R74.
- Semantic status meaning is unchanged: success/trusted uses green, waiting/degraded uses amber, and failure/destructive uses red.
- Existing historical color aliases remain mapped to the new canonical tokens so approved components retain their contracts without backend or interaction rewrites.
- R72's quiet sidebar active state and R73's Execution Proof geometry remain intact.
- R75 is reserved for exhaustive removal/normalization of any residual component-local legacy color treatment after this token migration.
- No Qwen/Ollama, LangGraph, retrieval, evidence, impact, Human Authority, adoption, recall, Audit, persistence, API or Demo-route behavior changes in R74.

## UI-R75 — Full Theme Consistency Pass

R75 is the approval-gated Impeccable **POLISH → AUDIT** closure after the R74 off-white palette migration. It does not redesign CREED. It normalizes the active visual system so the approved product reads as one intentional enterprise interface rather than a collection of historical module treatments.

Rules:
- Shared surfaces resolve to the R74 Background / Surface / Raised hierarchy with hairline borders and no decorative panel shadows.
- Off-white remains the primary hierarchy color. Secondary and muted text roles are applied consistently to support copy and metadata.
- Remaining semantic badges use compact small-radius treatment rather than decorative pill chrome. Success, warning, danger and running/info retain their existing meanings and use restrained state washes.
- Hover and selected rows across Overview, Issues, Knowledge, Change Radar, Audit and AI Runtime share the same quiet hover / selected-surface vocabulary. Selected state never changes product semantics.
- Filter/mode controls and Audit pagination use the same small-radius enterprise treatment. Active pagination is navigation state, not a filled primary CTA.
- Progressive disclosures keep all approved evidence/governance proof and use one border/text rhythm. R73's Execution Proof geometry is preserved.
- Analysis keeps the approved R62 information architecture and R69 selection topology; R75 only resolves those visuals to the final R74/R75 theme roles.
- No Qwen/Ollama execution, LangGraph lifecycle, persisted Human Review interrupt/resume, retrieval, evidence, impact scoring, Human Authority, learning, adoption, recall, Audit persistence, API/database behavior, Demo-route policy or Lucide icon policy changes in R75.

## UI-R76 REV1 — Analysis Case Context precision fix

- Baseline restored from `CREED-UI-R75.zip`.
- Scope limited to `Analysis > Case Context`.
- Increased internal breathing room for the Human Source / AI Interpretation comparison panes.
- Neutralized AI-adjacent informational typography and icons so cyan remains reserved for primary action/focus rather than decorative “AI” signaling.
- Preserved the approved four-workspace Analysis architecture and `Agent Execution Task` lifecycle rail.

## UI-R76 REV2 — Case Context rendering correction

- Built from UI-R76 REV1, which itself was built from the restored R75 baseline.
- Added parent-owned inset around the Case Context comparison surface so the two panes no longer sit flush against the Analysis zone boundary.
- Increased contrast only for operational proof values (ticket IDs, unknown/unverified extracted values, model proof metadata); field labels remain muted.
- Unknown/unverified remains neutral and is not promoted to warning/danger semantics.
- No Evidence, Investigation, Human Decision, Agent Execution Task, backend, Qwen, LangGraph, retrieval, or governance behavior changed.

## UI-R77 REV1 — Evidence overflow + reading width hardening

- Baseline: approved `CREED-UI-R76-REV2.zip` after the R75 rollback.
- Scope limited to `Analysis > Evidence`.
- Impeccable `layout` + `harden` + `typeset` + `quieter` pass.
- Dynamic document identifiers are clamped to two lines inside a bounded source column; secondary reasons remain one-line ellipsis and retrieval percentages keep a fixed numeric rail.
- The Evidence inspector excerpt is capped at a readable ~72ch measure with relaxed line-height.
- Ordinary Evidence typography is neutral/off-white; cyan remains reserved for selected-source location, action/focus, and retrieval visualization.
- No retrieval, ranking, evidence, provenance, Qwen, LangGraph, Human Review, or governance semantics changed.

## UI-R78 REV1 — Investigation AI-signal + semantic color cleanup

- Baseline: approved `CREED-UI-R77-REV1.zip`.
- Scope: Analysis > Investigation only.
- `POTENTIALLY_AFFECTED` and `INSUFFICIENT_EVIDENCE` use restrained warning semantics because they require investigation/review; neither is a defect verdict.
- `NO_SUPPORTING_EVIDENCE_OF_IMPACT` is neutral rather than green because absence of supporting evidence is not a governed `NOT_AFFECTED` decision.
- Cyan remains an interaction/current-location accent, not an AI identity color.
- Priority remains deterministic investigation priority and uses a restrained amber rail; Qwen narrative and metadata use neutral enterprise typography.

## UI-R79 REV1 — Human Decision motion + authority hierarchy

- Built on approved `CREED-UI-R78-REV1.zip`.
- Scope: `Analysis > Human Decision` only.
- Replaced progress `width` animation with `transform: scaleX(...)` while preserving the exact review-completeness calculation and progressbar semantics.
- Kept `ACTION REQUIRED` and review progress amber; made surrounding governed-review metadata neutral.
- Made the review queue and selected implementation orientation secondary to the governed decision task.
- Human outcome colors now appear only after an outcome is selected: Affected=red, Not affected=green, Needs more investigation=amber.
- AI advisory/proof typography is deliberately subordinate and neutral; AI remains advisory, human authority remains final.

## UI-R80 REV1 — Client Registry

R80 REV1 introduces the first registry administration surface as an Impeccable **Operate + Layout + Harden** module. It is intentionally limited to client records; implementation registration remains a separate approval-gated module.

Rules:
- Route: `/clients`; primary navigation label: `Clients`.
- The registry reads persisted clients from the existing `GET /api/v1/domain/clients` endpoint and creates clients through the existing `POST /api/v1/domain/clients` endpoint. No mock client state or fake persistence is introduced.
- Registration uses one inline task panel rather than a modal/card stack: client name, client type, cancel and submit.
- `BANK` and `FINANCIAL_INSTITUTION` are presented as human-readable labels while the persisted API values remain unchanged.
- The ledger exposes only fields the current API actually returns: client name, client type and client ID. Implementation counts, release state, product assignments and ownership are not inferred in this module.
- Search and type filtering are local views over the loaded persisted records; they do not alter backend data.
- Load/create failures remain visible and actionable. A failed initial registry read disables client creation until the operator retries, avoiding a misleading partial registry.
- Existing backend client-name idempotency is preserved. If `POST /clients` returns a client already present in the loaded registry, the UI reports that it already exists rather than claiming a new record was created.
- Visual hierarchy follows R74/R75: off-white hierarchy, restrained cyan for action/focus only, semantic green/red only for actual success/failure, hairline structure, small radii and no decorative card soup.
- Lucide is the only icon source.
- No Implementation Registry UI, implementation API, Qwen/Ollama, LangGraph, retrieval, evidence, impact, Human Review, governance, adoption or recall behavior changes in R80 REV1.

## UI-R81 REV1 — Implementation Registry

Implementation Registry is an **Operate-mode deployment identity surface** and remains separate from Client Registry and Local A-BOM governance.

Primary jobs:
1. **Register** — persist an implementation against an existing client, product, module and release label.
2. **Scan** — search/filter deployed implementation identities without converting them into impact findings.
3. **Harden** — surface missing client/catalog prerequisites and backend failure states rather than presenting an unusable form.
4. **Separate concerns** — creating an implementation does not create a MethodVersion dependency or Local A-BOM edge.

Rules:
- Client records are selected from persisted `/domain/clients`; this module does not create clients.
- Product/module choices come from the existing domain catalog; this module does not create product or module records.
- Module choices are constrained to the selected product and the backend rejects product/module mismatch.
- New implementations default to the backend's `ACTIVE` state; this registry does not invent a lifecycle-management UI.
- Duplicate client/module/release registration remains idempotent at the backend service boundary.
- Method-version adoption, A-BOM dependency edges, investigation findings and human authority remain separate governed records.
- Dynamic IDs, names and release labels must reflow without horizontal page overflow.
- All interface icons remain from `lucide-react`.

## UI-R82 REV1 — Delivery Method + Version Registry

Method Registry is an Impeccable **Operate-mode reusable-method administration surface**. It follows Client and Implementation Registry but remains intentionally separate from Local A-BOM adoption and governed learning approval.

Primary jobs:
1. **Register method identity** — persist a reusable delivery method under an existing product/module catalog scope.
2. **Create controlled draft versions** — add method-version candidates without presenting them as approved organisational knowledge.
3. **Scan lifecycle** — expose actual DRAFT / PROPOSED / APPROVED / REVOKED states already persisted by CREED.
4. **Preserve boundaries** — method/version registration never creates `USES_METHOD_VERSION`, impact evidence, an AI finding, or a human decision.

Rules:
- Route: `/methods`; primary navigation label: `Methods` with Lucide `GitBranch`.
- Product/module are catalog context. Creating a method does not create or modify product/module records.
- A newly-created method version is forced to `DRAFT` by the backend. There is no status selector on the registration surface.
- Existing APPROVED / PROPOSED / REVOKED states are read-only here; approval/revocation remains governed by learning/recall workflows.
- Method creation is idempotent on module + method name; version creation is idempotent on method + version label.
- The ledger can show a method with zero versions; operators may create the first draft directly in that method's row.
- Creating a draft version does not assign it to an implementation. Local A-BOM dependency authoring remains a separate module.
- Semantic status colour is restrained and truthful: approved=success, proposed=warning, revoked=danger, draft=neutral. Cyan remains interaction/focus only.
- Long IDs, method names, version labels and summaries must wrap without horizontal page overflow.
- All interface icons remain from `lucide-react`.

## UI-R85 REV1 — Human Authority Enforcement

R85 converts the R84 authority directory from configuration-only eligibility into enforced governance policy for the three existing human-controlled actions.

- Human Decision resume requires an active registered principal with `can_submit_human_decision`.
- Learning approval/rejection requires an active registered principal with `can_approve_learning`.
- Knowledge revocation/recall requires an active registered principal with `can_authorize_recall`.
- Governed frontend actions select only eligible active principals; free-text reviewer identity is removed from those action surfaces.
- The API requires `X-CREED-Principal` and verifies it matches the payload reviewer identity before the business action is evaluated.
- Persisted Human Decision records use the immutable authority principal as reviewer identity and retain authority ID, display name and role in decision metadata.
- This is authorization enforcement, not authentication. The principal header remains caller-supplied until a real identity provider/session layer is introduced.
- Missing, unknown, inactive, mismatched or under-privileged principals fail closed with explicit 403 governance errors.
- Existing Qwen, LangGraph, impact, evidence, adoption-hash and recall-hash semantics remain unchanged.
- Operate-mode hierarchy applies: show authority state at the action boundary, not as another dashboard metric or decorative permission card.

## UI-R86 REV1 — Release / Deployment Registry

Release / Deployment Registry is an Impeccable **Operate-mode deployment-provenance surface**. It records where an already-registered implementation release was actually promoted without creating a second source of release truth.

Primary jobs:
1. **Record** — persist an implementation deployment against a controlled environment and timestamp.
2. **Prove** — require a supporting Knowledge document for every deployment fact.
3. **Scan** — filter deployment history by client and environment while retaining release, timing and provenance in one ledger row.
4. **Preserve identity** — release version is inherited from the Implementation Registry and cannot be overridden in the deployment form.

Rules:
- Route: `/deployments`; primary navigation label: `Deployments` with Lucide `Rocket`.
- Supported environment values are `DEVELOPMENT`, `SIT`, `UAT`, `PRODUCTION`, and `DR`; the backend validates them.
- Deployment registration requires an existing implementation and an existing evidence document.
- Release version, client, product and module are derived from the selected implementation rather than duplicated in the deployment record.
- An identical deployment submission is idempotent. The same implementation/environment/timestamp cannot silently replace different provenance.
- Registration creates `RELEASE_DEPLOYMENT_RECORDED` audit provenance; it does not create A-BOM edges, AI findings, impact results, Human Decisions, learning approval or recall authorization.
- Environment colour is restrained: production uses success semantics, SIT/UAT use interaction accent, DR uses warning semantics, development remains neutral.
- Long implementation IDs, deployment references, evidence titles and hashes must reflow without horizontal page overflow.
- All interface icons remain from `lucide-react`.


## UI-R87 — Ownership & Responsibility Registry

Ownership is an accountability map, not an authorization system.

- A current responsibility assignment binds one persisted delivery asset and responsibility role to one named Human Authority principal.
- Supported scopes are Product, Module, Implementation and Delivery Method; role choices are constrained by scope.
- Existing ownership cannot be silently replaced: transfer requires an explicit reassignment reason and is written to Audit.
- Removing current ownership also requires a reason; historical change evidence remains in Audit.
- Inactive principals remain visible on existing assignments as an attention condition but cannot receive new assignments.
- Optional team labels add operating context only; the named principal remains the accountable identity.
- Ownership does not grant Human Decision, learning approval or recall authorization permissions.
- Follow the Operate mode: stable ledger density, explicit state, strong scan order, responsive linearity, Lucide-only iconography.


## UI-R88 REV1 — Sidebar Information Architecture

R88 is an Impeccable **DISTILL / Operate** refinement of the persistent shell. It reduces first-level navigation density without removing any approved route or changing business logic.

Rules:
- Daily assurance work remains first-level: Overview, Issues, Change Radar, Knowledge and Recalls.
- Registry is a collapsible parent for Clients, Implementations, Methods, Deployments and Dependencies.
- Governance is a collapsible parent for Authority, Ownership and Audit.
- Registry and Governance are closed by default; the parent containing the active route auto-opens and the child retains `aria-current=page`.
- AI Runtime is a separate utility destination adjacent to live System status rather than competing with the daily work sequence.
- Parent controls use Lucide icons, explicit `aria-expanded` / `aria-controls`, and keyboard-native buttons. Hidden children are removed from the focus order.
- The primary navigation region may scroll only as a bounded fallback on short viewports or when operators manually expand multiple groups; collapsing hierarchy, not scrolling, is the primary density solution.
- The existing 244px sidebar width, R72 quiet selected treatment, R74/R75 palette, mobile drawer, routes, backend APIs, Qwen, LangGraph, evidence, governance semantics and Demo-route policy remain unchanged.

## UI-R88 REV2 — No-Scroll Sidebar

R88 REV2 supersedes the unapproved R88 REV1 sidebar interaction while preserving the same route hierarchy. It applies Impeccable **DISTILL + Operate + Harden** to remove navigation scrolling as a normal desktop behavior instead of compressing labels or interaction targets.

Rules:
- Daily assurance work remains permanently visible: Overview, Issues, Change Radar, Knowledge and Recalls.
- Registry and Governance remain parent destinations, but their children no longer expand inline on desktop. They open contextual flyouts to the right of the persistent rail.
- Registry flyout contains Products, Clients, Implementations, Methods, Deployments and Dependencies. Governance flyout contains Authority, Ownership and Audit.
- When a child route is active, its parent receives a quiet active-parent treatment and may show the current child label without consuming another navigation row.
- Desktop flyouts open by pointer hover or explicit button activation, remain keyboard-operable with native buttons/links, close on Escape/outside interaction, and preserve `aria-expanded`, `aria-controls` and child `aria-current=page` semantics.
- The live API / Database / Qwen / Knowledge Source status cards are distilled into one compact System control. Detailed truthful service state stays inside the contextual health popover; AI Runtime remains a separate utility destination.
- The desktop primary navigation does not use an internal scrollbar. At short laptop heights, spacing compresses only to the approved 44px interaction floor.
- Mobile keeps the existing drawer. Registry, Governance and System details open as bounded overlay panels within that drawer rather than adding long nested rows.
- No route, backend API, Qwen/Ollama execution, LangGraph lifecycle, evidence, Human Decision, governance authorization, A-BOM, deployment or ownership behavior changes in R88 REV2.
- The existing 244px sidebar width, R72 selected-state restraint, R74/R75 palette, Lucide-only icon policy and Demo-route exclusion remain unchanged.

## UI-R88 REV3 — Hydration-Safe System Health Timestamp

R88 REV3 is a targeted correctness patch to the approved no-scroll sidebar. It does not change navigation information architecture or visual hierarchy.

Rules:
- Server-rendered sidebar markup must not depend on browser locale formatting.
- The System Health timestamp renders a deterministic hydration-safe placeholder (`Latest health check` or `Checking live services`) during SSR and the client's first render.
- Locale-aware `toLocaleTimeString` formatting runs only after hydration in `useEffect`, then updates the label for the user's browser locale.
- The System Health data, flyout behavior, Registry/Governance navigation, mobile overlay behavior, backend APIs and all CREED governance semantics remain unchanged.


## UI-R89 REV1 — Product Registry

Product Registry is an Impeccable **Operate-mode catalog administration surface**. It removes the previous SQL/bootstrap dependency for creating top-level delivery products while preserving Module Registry as a separate next step.

Primary jobs:
1. **Register product identity** — create a persisted delivery product with stable name, factual description and explicit catalog status.
2. **Scan catalog state** — search and filter products without turning the page into a dashboard.
3. **Control lifecycle metadata** — activate/deactivate a product without deleting historical implementations, methods, ownership or evidence.
4. **Preserve hierarchy** — product creation never creates a Module, Method, Implementation, A-BOM edge, AI finding or governance decision.

Rules:
- Route: `/products`; Registry flyout label: `Products` with Lucide `Package`.
- Product names are unique. Exact repeat submissions are idempotent; conflicting reuse of the same name fails rather than silently replacing the existing definition.
- New records persist through the real domain API and emit `PRODUCT_CREATED`; status/description changes emit `PRODUCT_UPDATED`.
- `active` is catalog lifecycle metadata. R89 does not delete dependent records or claim downstream impact when a product is deactivated.
- Product description is factual catalog context, not marketing copy or generated AI interpretation.
- Modules remain a separate governed catalog task and are not created inline from Product Registry.
- Operate-mode hierarchy applies: one primary creation action, one inline creation surface, one scan-first ledger, explicit empty/error/loading states, and no modal-first workflow.
- Responsive behavior must preserve readable product names, descriptions, status, IDs and actions without page-level horizontal overflow. Adding Products to Registry must also keep the R88 flyout viewport-clamped at short laptop heights without reintroducing sidebar scrolling.
- All interface icons remain from `lucide-react`.


## UI-R90 REV1 — Module Registry

Modules are explicit product-scoped catalog records. The Module Registry follows Operate mode: predictable inline creation, restrained hierarchy, factual catalog copy, visible lifecycle state, and recovery-oriented empty/error states.

Rules:
- Every Module belongs to exactly one Product.
- New Modules can only be registered under an active Product; deactivating a Product does not delete historical Modules.
- Module creation never creates a Method, Method Version, Implementation or A-BOM relationship.
- Module names are unique within their parent Product, not globally.
- Duplicate submissions with the same catalog definition are idempotent; conflicting definitions return an explicit conflict.
- Module deactivation is catalog metadata only; existing dependent records remain traceable.
- Newly registered Modules become available to downstream catalog consumers through the real domain API.
- All interface icons remain from `lucide-react`.

## UI-R91 REV1 — Governed Baseline Method Approval

The Methods registry now supports a one-time human-governed approval for the first baseline version of a delivery method so an empty CREED installation can be prepared entirely through the product UI.

Rules:
- New method versions are still always created as `DRAFT`.
- `Approve baseline` is shown only while that Method has never established an `APPROVED` or `REVOKED` baseline.
- Baseline approval requires an active Human Authority with `can_approve_learning` and a human rationale.
- The submitted `X-CREED-Principal` must match the selected authority principal; failures are fail-closed.
- Baseline approval changes only the selected Method Version from `DRAFT` to `APPROVED` and writes `BASELINE_METHOD_VERSION_APPROVED` provenance.
- The action does not create an A-BOM dependency, implementation adoption, AI finding, Human Decision, Learning Proposal or Adoption Receipt.
- Once a baseline has been approved or later revoked, all future version approval must go through the governed learning workflow; the baseline shortcut cannot be reused.
- The approval form is inline in Operate mode rather than modal-first, preserves the existing Methods ledger hierarchy, and remains usable on mobile.

## UI-R92 REV1 — Registry/Governance Flyout Interaction Fix

R92 hardens only the R88 desktop flyout interaction model while preserving the approved no-scroll sidebar information architecture.

Rules:
- Registry and Governance still open on desktop hover.
- The rail-to-flyout gap has an invisible pointer-safe bridge so horizontal movement does not create a dead zone.
- Pointer leave uses a 280ms grace period; re-entry cancels the pending close so diagonal movement to child workspaces remains usable.
- Clicking a Registry/Governance trigger pins that flyout open until the same trigger is toggled, a different flyout is explicitly pinned, Escape is pressed, navigation occurs, or the user clicks outside the sidebar.
- A pinned flyout is not replaced by incidental hover over the other grouped destination.
- Keyboard focus entering a grouped destination keeps its flyout available; focus leaving the group follows the same bounded close policy.
- Mobile remains tap-driven with the existing bounded overlay panels; desktop pointer bridging is not applied to mobile.
- R92 does not change navigation membership, route behavior, System Health contents, Product/Module/Method registries, governed baseline approval, Qwen/Ollama, LangGraph, evidence, Human Authority, learning, recall, A-BOM, backend APIs or persistence semantics.

## UI-R93 REV1 — AI Runtime Deduplication

R93 applies a narrow **DISTILL / Clarify** pass to the shell so System health and AI execution proof no longer compete as duplicate navigation paths.

Rules:
- AI Runtime remains the single primary shell destination for runtime execution proof.
- System answers **“Is CREED healthy?”** and contains service health only: API, Database, Qwen and Knowledge Source.
- The duplicate `View AI Runtime` action is removed from the System Health popover.
- System Health does not become a runtime execution surface and AI Runtime does not become a general health panel.
- Registry/Governance flyout behavior from approved UI-R92 REV1 remains unchanged.
- No Qwen/Ollama status calculation, structured inference, LangGraph lifecycle, agent-status presentation, governance, API, database or persistence behavior changes.
- Demo remains removed and active interface icons remain Lucide-only.


## UI-R95 REV1 — In-place source provenance

`Analysis > Evidence` and `Analysis > Investigation` now keep source inspection inside the active workbench. `Open source` opens a read-only dark source modal containing the persisted document record, relevant retrieved excerpt, full extracted source text, and SHA-256. `Inspect AI analysis` includes the persisted evidence references used by the selected investigation and lets the operator open those sources without leaving Analysis. This is a presentation/provenance refinement only; no retrieval, AI, investigation, Human Authority, learning, adoption, or Recall behavior changes.


## UI-R96 REV1 — Original source fidelity

`Open source` distinguishes **Original document** from **Extracted text**. The Original view is backed by a read-only endpoint that recalculates SHA-256 and refuses to serve bytes that no longer match the persisted ingestion hash. PDFs render from those original bytes in-place; text/Markdown/JSON render the original stored text; DOCX is preserved as the original file but is not represented as browser-layout-exact. Investigation source evidence uses the identical viewer. Extracted text remains available as a parser-derived representation for retrieval transparency, never as a substitute claim for the original artifact.
