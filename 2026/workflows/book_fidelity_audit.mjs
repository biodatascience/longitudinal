export const meta = {
  name: 'book-fidelity-audit',
  description: 'Per-deck audit of departures from the FLW textbook across the six reviewed decks (L01-L06); propose-only.',
  phases: [
    { title: 'Audit', detail: 'one agent per deck: compare the deck to its FLW chapter (RAG + chapter PDF), list departures' },
    { title: 'Synthesize', detail: 'merge departures, find patterns, propose framework updates' },
  ],
}

const BASE = '/home/naimrashid/Dropbox/UNC_bios_line/BIOS667/new'
// Batch-parameterized: pass args = {decks:[{id,ch,file,pdfkey}, ...]}. Defaults to B1-B2 (L01-L06).
const A = (typeof args === 'string') ? (args.trim() ? JSON.parse(args) : {}) : (args || {})
const DEFAULT_DECKS = [
  { id: 'L01', ch: 1, file: 'BIOS667_L01_Intro_ch1.qmd', pdfkey: 'Longitudinal and Clustered Data' },
  { id: 'L02', ch: 2, file: 'BIOS667_L02_BasicConcepts_ch2.qmd', pdfkey: 'Basic Concepts' },
  { id: 'L03', ch: 3, file: 'BIOS667_L03_LinearModelsOverview_ch3.qmd', pdfkey: 'Overview of Linear Models' },
  { id: 'L04', ch: 4, file: 'BIOS667_L04_EstimationInference_ch4.qmd', pdfkey: 'Estimation and Statistical Inference' },
  { id: 'L05', ch: 5, file: 'BIOS667_L05_ResponseProfiles_ch5.qmd', pdfkey: 'Analyzing Response Profiles' },
  { id: 'L06', ch: 6, file: 'BIOS667_L06_ParametricCurves_ch6.qmd', pdfkey: 'Parametric Curves' },
]
const DECKS = ((A.decks && A.decks.length) ? A.decks : DEFAULT_DECKS).map(d => ({
  ...d, path: d.path || `${BASE}/2026/lectures/${d.file}`,
}))
log('book-fidelity-audit: ' + DECKS.map(d => d.id).join(', '))

const DEP_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    deck: { type: 'string' }, chapter: { type: 'number' },
    status: { type: 'string', enum: ['faithful', 'departures_found'] },
    departures: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        location: { type: 'string' },
        type: { type: 'string', enum: ['beyond-flw-unflagged', 'contradicts-flw', 'formula-or-constant', 'definition-or-terminology', 'example-or-dataset-mismatch', 'method-not-in-book'] },
        description: { type: 'string' },
        flw_basis: { type: 'string' },
        severity: { type: 'string', enum: ['high', 'medium', 'low'] },
        suggested_fix: { type: 'string' },
      },
      required: ['location', 'type', 'description', 'flw_basis', 'severity'] } },
    notes: { type: 'string' },
  },
  required: ['deck', 'chapter', 'status', 'departures'],
}

phase('Audit')
const audits = await parallel(DECKS.map(d => () => agent(
  `You audit ONE BIOS 667 reference deck for DEPARTURES from the Fitzmaurice, Laird & Ware (2011) textbook ("FLW"). ` +
  `Deck: ${d.path} (maps to FLW Chapter ${d.ch}). ` +
  `Read the deck in full. Then ground every check in the actual textbook two ways:\n` +
  `1. RAG (authoritative, run via the venv, NOT the MCP): \`cd ${BASE}/rag && .venv/bin/python -c "from bios667_rag.corpus_query import CorpusQuery; q=CorpusQuery(store_dir='data'); import json; print(json.dumps([{'score':r['score'],'text':r['text'][:400]} for r in q.search_all('<your query>', source_type='textbook', chapter=${d.ch}, top_k=5)], indent=1))"\`. Run several searches for the deck's key claims/methods/formulas.\n` +
  `2. The chapter PDF: \`ls "${BASE}/book/" | grep -i "${d.pdfkey}"\` to get the exact filename, then Read targeted pages of that PDF to verify wording/formulas where the RAG is ambiguous.\n\n` +
  `Find DEPARTURES, each in one of these classes: (a) **beyond-flw-unflagged** = a method/topic NOT in this FLW chapter that is taught as if it were chapter content and is NOT flagged "beyond FLW" with a citation (e.g. an instructor extension); (b) **contradicts-flw** = a statement, emphasis, or procedure that disagrees with the book; (c) **formula-or-constant** = a formula, constant, df, or distribution that differs from FLW; (d) **definition-or-terminology** = a definition/term used differently than FLW; (e) **example-or-dataset-mismatch** = an example/dataset/number that does not match the chapter's; (f) **method-not-in-book** = an R/SAS technique presented as the book's approach when the book uses a different one. ` +
  `For each: give the slide title/location, the class, a precise description, the FLW basis (what the book actually says + section/table/page if you can), severity, and a suggested fix. ` +
  `Calibrate: a clearly-labeled "beyond FLW (citation)" extension is NOT a departure; a genuinely-wrong or unflagged one IS. Be specific and conservative (only real departures). Propose only; do NOT edit any file. ` +
  `Note the project rule: course L17-L19 labels do not match FLW Ch.17-19, but that does not affect L01-L06.`,
  { label: `fidelity:${d.id}`, phase: 'Audit', schema: DEP_SCHEMA })))

const results = audits.filter(Boolean)

phase('Synthesize')
const SYNTH_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    summary: { type: 'string' },
    confirmed_departures: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: { deck: { type: 'string' }, location: { type: 'string' }, type: { type: 'string' }, severity: { type: 'string' }, description: { type: 'string' }, fix: { type: 'string' } },
      required: ['deck', 'location', 'severity', 'description', 'fix'] } },
    patterns: { type: 'array', items: { type: 'string' } },
    framework_recommendations: { type: 'array', items: { type: 'string' } },
    overall_verdict: { type: 'string', enum: ['faithful', 'minor departures', 'needs work'] },
  },
  required: ['summary', 'confirmed_departures', 'patterns', 'framework_recommendations', 'overall_verdict'],
}
const synth = await agent(
  `You are the synthesizer for a book-fidelity audit of BIOS 667 decks ${DECKS.map(d => `${d.id} (FLW Ch.${d.ch})`).join(', ')}. ` +
  `Merge and dedupe the per-deck departure findings below. Keep only real departures (drop false positives, e.g. correctly-flagged beyond-FLW extensions). ` +
  `Identify cross-deck PATTERNS (recurring kinds of departure). Then propose FRAMEWORK RECOMMENDATIONS: concrete, checkable steps to build a "book-departure check" into per-deck creation/review (POST_LECTURE_REVIEW.md) and per-batch lint (SCALING_PLAN.md), e.g. a required RAG/PDF fidelity pass and a "beyond-FLW must be flagged + cited" gate. ` +
  `Findings JSON: ${JSON.stringify(results)}`,
  { label: 'fidelity:synthesis', phase: 'Synthesize', schema: SYNTH_SCHEMA })

return { audits: results, synthesis: synth }
