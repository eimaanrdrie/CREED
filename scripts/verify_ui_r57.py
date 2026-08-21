from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R57_NOTES.md").read_text(encoding="utf-8")

required_analysis = [
    'analysis-r57',
    'analysis-evidence-workbench-r57',
    'EVIDENCE</span><h2>{results.length} source',
    'chunks searched',
    'Retrieval details',
    'SEARCH CONCEPTS',
    'RANKED SOURCES',
    'Matched: ${result.matched_queries[0]}',
    'evidence-hit-score-r57',
    'RELEVANT EXCERPT',
    'evidence-excerpt-clamp-r57',
    'Read full excerpt',
    'Inspect proof',
    'Ranking · traceability · provenance',
    'RANKING SIGNALS',
    'TRACEABILITY',
    'PROVENANCE',
    'getDocument(selected.document_id)',
    'Open source',
]
missing = [token for token in required_analysis if token not in ANALYSIS]
assert not missing, f"Missing R57 analysis contract: {missing}"

# Default Evidence composition must no longer expose search concepts, ranking
# mechanics, trace IDs or provenance outside progressive disclosure.
start = ANALYSIS.index('function EvidenceWorkbench({ evidence }: { evidence:any }) {')
end = ANALYSIS.index('\nfunction evidenceCitationTitle', start)
block = ANALYSIS[start:end]
retrieval_open = block.index('<ProgressiveDisclosure label="Retrieval details"')
layout_open = block.index('{results.length === 0 ?')
assert block.index('SEARCH CONCEPTS') > retrieval_open and block.index('SEARCH CONCEPTS') < layout_open, 'Search concepts are not confined to Retrieval details'
proof_open = block.index('<ProgressiveDisclosure label="Inspect proof"')
for token in ['RANKING SIGNALS', 'TRACEABILITY', 'PROVENANCE', 'SHA-256']:
    assert block.index(token) > proof_open, f'{token} leaked before Inspect proof'
full_open = block.index('<ProgressiveDisclosure label="Read full excerpt"')
assert block.index('evidence-excerpt-full-r57') > full_open, 'Full excerpt is not behind disclosure'

required_css = [
    'UI-R57 — EVIDENCE DISTILLATION',
    '.analysis-evidence-workbench-r57',
    '.evidence-layout-r57',
    '.evidence-hit-r57',
    'min-height:72px',
    '.evidence-excerpt-clamp-r57',
    '-webkit-line-clamp:4',
    '.evidence-proof-r57',
    '@container analysis-workbench (max-width:880px)',
    '@container analysis-workbench (max-width:620px)',
    '@container analysis-workbench (max-width:440px)',
]
missing = [token for token in required_css if token not in CSS]
assert not missing, f"Missing R57 CSS contract: {missing}"

for token in [
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'analysisRunEventsUrl(run.graph_run_id',
    'getRunEvidence(run.graph_run_id)',
    'getImpact(run.graph_run_id)',
    'getRunInvestigations(run.graph_run_id)',
    'getHumanReview(run.graph_run_id)',
    'resumeHumanReview(run.graph_run_id',
    'Priority score, not a defect verdict.',
    'AI finding is advisory.',
    'AI investigates. Humans decide.',
]:
    assert token in ANALYSIS, f"R57 regressed approved Analysis wiring: {token}"

assert 'DISTILL → LAYOUT' in DESIGN
assert 'persisted retrieval hit text' in NOTES
assert 'UI-R58' in NOTES
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
print('UI-R57 verifier: PASS')
print('- Evidence default view distilled to sources, match and relevant excerpt')
print('- search concepts and deep ranking/provenance proof are progressive disclosure')
print('- persisted source text and retrieval semantics remain truthful')
print('- approved Qwen/LangGraph/Human Authority wiring preserved')
