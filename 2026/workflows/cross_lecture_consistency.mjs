export const meta = {
  name: 'cross-lecture-consistency',
  description: 'Cross-lecture consistency sweep over a batch of reference decks (or all decks): notation, cross-references, definitions, coverage, progression. Propose-only; emits ledger updates.',
  whenToUse: 'Run at each batch boundary and once globally at the end. Pass args={deckPaths:[...], batchLabel}. Catches cross-deck problems the per-lecture panel cannot see.',
  phases: [
    { title: 'Scan', detail: 'one agent per cross-cutting dimension, reading across the decks (grep-driven)' },
    { title: 'Synthesize', detail: 'merge findings + propose ledger updates, checked against the rules' },
  ],
}

// ---- Inputs ----
// The Workflow tool delivers `args` as a JSON-encoded STRING; parse it (object/undefined tolerated).
const A = (typeof args === 'string') ? (args.trim() ? JSON.parse(args) : {}) : (args || {})
const DEFAULT_BASE = '/home/naimrashid/Dropbox/UNC_bios_line/BIOS667/new'
const deckPaths = (A.deckPaths && A.deckPaths.length) ? A.deckPaths : [`${DEFAULT_BASE}/2026/lectures/BIOS667_L08_Covariance_ch8_LME.qmd`]
const batchLabel = A.batchLabel || 'unnamed batch'
const BASE = A.base || (deckPaths[0].includes('/2026/') ? deckPaths[0].split('/2026/')[0] : DEFAULT_BASE)
log('cross_lecture_consistency batch "' + batchLabel + '": ' + deckPaths.length + ' decks')
const LEDGER = `${BASE}/2026/CONSISTENCY_LEDGER.md`
const NOTATION = `${BASE}/2026/NOTATION_REFERENCE.md`
const SPEC = `${BASE}/2026/REFERENCE_DECK_SPEC.md`
const TIMING = `${BASE}/2026/LECTURE_TIMING_PLAN.md`
const CLAUDEMD = `${BASE}/CLAUDE.md`
const deckList = deckPaths.join('\n')

// ---- Schemas ----
const DIM_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    dimension: { type: 'string' },
    status: { type: 'string', enum: ['consistent', 'issues_found'] },
    findings: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        decks: { type: 'array', items: { type: 'string' } },
        issue: { type: 'string' },
        severity: { type: 'string', enum: ['high', 'medium', 'low'] },
        suggestion: { type: 'string' },
      },
      required: ['decks', 'issue', 'severity'] } },
    notes: { type: 'string' },
  },
  required: ['dimension', 'status', 'findings'],
}
const SYNTH_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    summary: { type: 'string' },
    cross_lecture_issues: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        dimension: { type: 'string' }, decks: { type: 'array', items: { type: 'string' } },
        issue: { type: 'string' }, severity: { type: 'string', enum: ['high', 'medium', 'low'] },
        fix: { type: 'string' }, is_global: { type: 'boolean' },
      },
      required: ['dimension', 'issue', 'severity', 'fix'] } },
    ledger_updates: { type: 'array', items: { type: 'string' } },
    overall_verdict: { type: 'string', enum: ['consistent', 'minor issues', 'needs work'] },
  },
  required: ['summary', 'cross_lecture_issues', 'overall_verdict'],
}

const common = `These are the BIOS 667 reference decks in batch "${batchLabel}":\n${deckList}\n\n` +
  `Read the consistency ledger ${LEDGER} (prior cross-lecture decisions you must respect) and the ` +
  `notation master ${NOTATION}. Be GREP-DRIVEN: use Grep across the listed decks for the specific ` +
  `patterns rather than reading every deck end to end, then Read only the spans you need. Report ` +
  `specific deck files and slide titles. Propose only; do not edit files.`

const DIMENSIONS = [
  { key: 'notation-terminology',
    prompt: `You check NOTATION and TERMINOLOGY consistency across decks. ${common}\n` +
      `Verify: every deck renders its notation via the shared include ({{< include _notation_box.qmd >}} for methods decks, or {{< include _notation_box_intro.qmd >}} for intro/overview decks per the ledger) and NOT a hand-pasted table; flag any deck that hand-pastes a notation table or uses an inline symbol that collides with a reserved canonical symbol (e.g. a fixed covariate written as z_{ij}, or an error term written e_i instead of varepsilon, or covariate written as a column when the canon is the row X_{ij}). Preferred terms are used consistently across decks ("empirical BLUP" not just EBLUP at first use; "invalid inference" not "biased SEs"; covariance vs correlation not interchanged). Flag any symbol used inconsistently between decks.` },
  { key: 'cross-references',
    prompt: `You check CROSS-REFERENCE integrity across decks. ${common}\n` +
      `Grep across the decks for forward/backward references ("recall", "Chapter", "Lecture", "we revisit", "we will see", "earlier we"). Build the reference graph and verify each pointer resolves to content that ACTUALLY exists in the named deck/chapter. Flag dangling references (points to a lecture/chapter that does not cover it), contradictory references, and any concept used before the deck that is supposed to introduce it.` },
  { key: 'definitions',
    prompt: `You check for DUPLICATED or CONTRADICTORY definitions across decks. ${common}\n` +
      `Identify key terms/concepts defined in more than one deck (e.g. EBLUP, REML vs ML rule, boundary test, ICC, marginal vs conditional) and verify the definitions agree. Flag any term defined two different or contradictory ways, and any place a later deck redefines something an earlier deck already established differently.` },
  { key: 'coverage',
    prompt: `You check cumulative FLW COVERAGE across the batch. ${common}\n` +
      `Map each deck to its FLW chapter(s) (from titles/YAML). Verify the batch's cumulative coverage has no gap (a chapter topic no deck addresses) and no accidental double-coverage (the same topic taught in depth in two decks without a deliberate recall). Use the spec ${SPEC} for the chapter->lecture expectations. Note the CLAUDE.md caveat that course L17-L19 labels do not match FLW Ch. 17-19.` },
  { key: 'progression',
    prompt: `You check DIFFICULTY/LENGTH/PACING progression across decks. ${common}\n` +
      `Using the timing plan ${TIMING} and the CLAUDE.md timing guidance, verify slide counts and period allocations are consistent with the plan, difficulty progresses sensibly across the batch, and no deck is wildly out of line (too long for its period budget, or too thin). Flag mismatches between a deck's actual slide count and its timing-plan allocation.` },
]

// ---- Phase 1: parallel dimension scans ----
phase('Scan')
const scans = await parallel(DIMENSIONS.map(d => () =>
  agent(d.prompt, { label: `xlec:${d.key}`, phase: 'Scan', schema: DIM_SCHEMA })))
const dimResults = scans.filter(Boolean)

// ---- Phase 2: synthesize + ledger updates (consistency guardrail) ----
phase('Synthesize')
const synthPrompt = `You are the cross-lecture SYNTHESIZER and consistency guardrail for batch "${batchLabel}".` +
  ` You have per-dimension findings (notation/terminology, cross-references, definitions, coverage, progression)` +
  ` over these decks:\n${deckList}\n` +
  `Read the ledger ${LEDGER}, the notation master ${NOTATION}, the spec ${SPEC}, and the CLAUDE.md writing rules` +
  ` (no em-dashes, no gratuitous semicolons, no AI-tells) in ${CLAUDEMD}.\n` +
  `Merge the findings, deduplicate, and for each real issue give: dimension, decks, severity, a concrete fix,` +
  ` and whether it is GLOBAL (changes the template/spec/notation/timing or all decks) vs local to specific decks.` +
  ` Then propose LEDGER UPDATES: the cross-lecture decisions to record so later batches stay consistent` +
  ` (notation/terminology rulings, the cross-reference map, dataset naming, any global change). Ensure every` +
  ` proposed fix respects the rules (no em-dashes, notation no-collision, precision standards). Propose only.\n` +
  `DIMENSION FINDINGS (JSON): ${JSON.stringify(dimResults)}`

const synthesis = await agent(synthPrompt, { label: 'xlec:synthesis', phase: 'Synthesize', schema: SYNTH_SCHEMA })

return { batchLabel, deckPaths, dimensions: dimResults, synthesis }
