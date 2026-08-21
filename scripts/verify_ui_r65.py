from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / 'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
DESIGN = (ROOT / 'frontend/DESIGN.md').read_text(encoding='utf-8')
NOTES = (ROOT / 'UI_R65_NOTES.md').read_text(encoding='utf-8')

for token in [
    'analysis-r65',
    'analysis-evidence-workbench-r57 analysis-evidence-workbench-r65',
    'evidence-command-r57 evidence-command-r65',
    'source{results.length === 1 ? "" : "s"}',
    'chunks searched',
    'ProgressiveDisclosure label="Retrieval details"',
    'evidence-layout-r57 evidence-layout-r65',
    'evidence-hit-r57 evidence-hit-r65',
    'evidence-hit-score-r57 evidence-hit-score-r65',
    'evidence-inspector-r57 evidence-inspector-r65',
    'evidence-open-source-r65',
    'RELEVANT EXCERPT',
    'evidence-excerpt-clamp-r57 evidence-excerpt-clamp-r65',
    'ProgressiveDisclosure label="Read full excerpt"',
    'ProgressiveDisclosure label="Inspect proof" meta="Ranking · provenance"',
    'RANKING SIGNALS',
    'TRACEABILITY',
    'PROVENANCE',
    'getDocument(selected.document_id)',
]:
    assert token in ANALYSIS, f'Missing R65 Analysis contract: {token}'

# Default-visible evidence must remain distilled. Technical retrieval proof must
# stay behind progressive disclosure rather than leaking into the glance state.
start = ANALYSIS.index('function EvidenceWorkbench({ evidence }: { evidence:any }) {')
end = ANALYSIS.index('\nfunction evidenceCitationTitle', start)
block = ANALYSIS[start:end]
retrieval_open = block.index('<ProgressiveDisclosure label="Retrieval details"')
layout_open = block.index('{results.length === 0 ?')
assert block.index('SEARCH CONCEPTS') > retrieval_open and block.index('SEARCH CONCEPTS') < layout_open
proof_open = block.index('<ProgressiveDisclosure label="Inspect proof"')
for token in ['RANKING SIGNALS', 'TRACEABILITY', 'PROVENANCE', 'SHA-256']:
    assert block.index(token) > proof_open, f'{token} leaked before Inspect proof'
full_open = block.index('<ProgressiveDisclosure label="Read full excerpt"')
assert block.index('evidence-excerpt-full-r57') > full_open
assert '<ArrowRight size={14}' not in block, 'Decorative Evidence row arrow should be removed in R65'
assert 'Text returned by retrieval' not in block, 'Redundant excerpt helper copy remains visible'

for token in [
    'UI-R65 — EVIDENCE WORKSPACE VISUAL DISTILLATION',
    '.analysis-r65 .analysis-evidence-workbench-r65',
    'border:0;',
    '.analysis-r65 .evidence-layout-r65',
    'grid-template-columns:minmax(238px,.58fr) minmax(0,1.55fr);',
    '.analysis-r65 .evidence-hit-r65',
    'min-height:58px;',
    '.analysis-r65 .evidence-open-source-r65',
    '.analysis-r65 .evidence-excerpt-clamp-r65',
    '-webkit-line-clamp:3;',
    '@container analysis-workbench (max-width:900px)',
]:
    assert token in CSS, f'Missing R65 CSS contract: {token}'

for token in [
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'analysisRunEventsUrl(run.graph_run_id',
    'getRunEvidence(run.graph_run_id)',
    'getImpact(run.graph_run_id)',
    'getRunInvestigations(run.graph_run_id)',
    'getHumanReview(run.graph_run_id)',
    'resumeHumanReview(run.graph_run_id',
    'Agent Execution Task',
]:
    assert token in ANALYSIS, f'R65 regressed approved runtime wiring: {token}'

assert 'Evidence workspace visual distillation' in DESIGN
assert 'No backend source file was changed' in NOTES
assert 'UI-R66' in NOTES
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
print('UI-R65 verifier: PASS')
print('- Evidence default view reduced to retrieval summary, ranked sources and one focused excerpt')
print('- technical retrieval/provenance proof remains behind Inspect')
print('- persisted source text and retrieval semantics remain unchanged')
print('- approved Analysis runtime/governance wiring preserved')
