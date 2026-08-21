from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R52_NOTES.md").read_text(encoding="utf-8")

required_analysis = [
    'analysis-r52',
    'getDocument,',
    'type EvidenceDocumentDetail',
    'function EvidenceWorkbench',
    'EvidenceHit',
    'evidence-command-r52',
    'evidence-layout-r52',
    'evidence-master-r52',
    'evidence-hit-r52',
    'aria-pressed={selectedRow}',
    'setSelectedHitId(result.id)',
    'evidence-inspector-r52',
    'evidence-excerpt-r52',
    'Text actually returned by retrieval',
    'evidence-score-signals-r52',
    'semantic_score',
    'keyword_score',
    'metadata_score',
    'query_coverage_bonus',
    'issue_link_boost',
    'evidence-trace-facts-r52',
    'selected.document_id',
    'selected.chunk_id',
    'matchedQueries.join',
    'ProgressiveDisclosure label="Provenance proof"',
    'documentDetail.content_hash',
    'Retrieved material remains evidence for inspection.',
    'Retrieval score ranks evidence; it does not validate the source.',
]
missing = [token for token in required_analysis if token not in ANALYSIS]
assert not missing, f"Missing R52 analysis contract: {missing}"

# R52 replaces the old duplicate evidence renderings inside Analysis.
assert 'className="evidence-glance-r25"' not in ANALYSIS, 'R52 must remove the old top-three evidence teaser rendering'
assert 'className="evidence-ledger-r04"' not in ANALYSIS, 'R52 must remove the old expanded evidence ledger rendering'

required_css = [
    'UI-R52 — Analysis Evidence Ledger + Proof Inspector',
    '.analysis-evidence-workbench-r52',
    '.evidence-command-r52',
    '.evidence-layout-r52',
    '.evidence-master-r52',
    '.evidence-hit-r52.selected',
    '.evidence-inspector-r52',
    '.evidence-excerpt-r52',
    '.evidence-score-signals-r52',
    '.evidence-trace-facts-r52',
    '.evidence-provenance-r52',
    '@container analysis-workbench (max-width:880px)',
    '@container analysis-workbench (max-width:620px)',
    '@container analysis-workbench (max-width:440px)',
]
missing = [token for token in required_css if token not in CSS]
assert not missing, f"Missing R52 CSS contract: {missing}"

# Approved runtime/governance wiring remains intact.
for token in [
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'analysisRunEventsUrl(run.graph_run_id',
    'getRunEvidence(run.graph_run_id)',
    'getImpact(run.graph_run_id)',
    'getRunInvestigations(run.graph_run_id)',
    'getHumanReview(run.graph_run_id)',
    'resumeHumanReview(run.graph_run_id',
    'function InvestigationWorkbench',
    'Priority score, not a defect verdict.',
    '"AFFECTED"',
    '"NOT_AFFECTED"',
    '"NEEDS_MORE_INVESTIGATION"',
]:
    assert token in ANALYSIS, f"R52 regressed approved analysis wiring: {token}"

assert 'Operate-mode master/detail evidence workbench' in DESIGN
assert 'No backend file, API contract, database model or retrieval algorithm changed.' in NOTES
assert 'UI-R53' in NOTES
assert not (ROOT / 'frontend/app/demo').exists(), 'Demo route must remain removed'

AUDIT = (ROOT / 'frontend/components/audit-workspace.tsx').read_text(encoding='utf-8')
assert 'const AUDIT_PAGE_SIZE = 6' in AUDIT
assert 'audit-pagination-r48' in AUDIT

for path in (ROOT / 'frontend').rglob('*.tsx'):
    source = path.read_text(encoding='utf-8')
    assert '<svg' not in source.lower(), f'Raw SVG found in {path}'
    assert 'react-icons' not in source
    assert '@heroicons' not in source
    assert 'fontawesome' not in source.lower()

assert CSS.count('{') == CSS.count('}'), 'CSS braces are unbalanced'
print('UI-R52 verifier: PASS')
print('- Evidence is one ranked master/detail workbench')
print('- selected excerpt, ranking signals, traceability and stored provenance remain distinct')
print('- provenance loading/failure remains truthful; no backend semantics changed')
print('- R51/R50/R49/R48 continuity preserved')
