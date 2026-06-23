export const meta = {
  name: 'lecture-review-panel',
  description: 'Multi-perspective reference-deck review: student + faculty audits, adjudicator change plan, consistency check (propose-only)',
  whenToUse: 'Run after a BIOS 667 reference deck is drafted/edited. Pass args={deckPath, chapter}. Returns the two reviews, a local+global change plan, and a consistency report. Proposes changes; does not edit files.',
  phases: [
    { title: 'Audit', detail: 'UNC masters student (learnability) + Harvard faculty (rigor/fidelity), in parallel' },
    { title: 'Adjudicate', detail: 'synthesize both into local + global change plan' },
    { title: 'Consistency', detail: 'check each proposed change against spec / CLAUDE.md / notation / voice rules' },
  ],
}

// ---- Inputs ----
// The Workflow tool delivers `args` as a JSON-encoded STRING, so parse it (an
// object or undefined is also tolerated). Then read deckPath/chapter/base from it.
// Repo root is derived from the (absolute) deck path so the workflow is not tied to one checkout.
const A = (typeof args === 'string') ? (args.trim() ? JSON.parse(args) : {}) : (args || {})
const DEFAULT_BASE = '/home/naimrashid/Dropbox/UNC_bios_line/BIOS667/new'
const deckPath = A.deckPath || `${A.base || DEFAULT_BASE}/2026/lectures/BIOS667_L08_Covariance_ch8_LME.qmd`
const BASE = A.base || (deckPath.includes('/2026/') ? deckPath.split('/2026/')[0] : DEFAULT_BASE)
const chapter = A.chapter || 8
log('lecture_review_panel reviewing: ' + deckPath + ' (Ch. ' + chapter + ')')
const SPEC = `${BASE}/2026/REFERENCE_DECK_SPEC.md`
const TEMPLATE = `${BASE}/2026/lectures/BIOS667_Reference_Deck_Template.qmd`
const NOTATION = `${BASE}/2026/NOTATION_REFERENCE.md`
const NOTATION_PARTIAL = `${BASE}/2026/lectures/_notation_box.qmd`
const CLAUDEMD = `${BASE}/CLAUDE.md`
const TIMING = `${BASE}/2026/LECTURE_TIMING_PLAN.md`

// ---- Schemas ----
const STUDENT_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    learnability_verdict: { type: 'string', enum: ['clear', 'mostly clear', 'confusing in places', 'hard to follow'] },
    strengths: { type: 'array', items: { type: 'string' } },
    friction_points: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: { slide: { type: 'string' }, issue: { type: 'string' }, suggestion: { type: 'string' } },
      required: ['issue', 'suggestion'] } },
    pacing_concerns: { type: 'array', items: { type: 'string' } },
    prereq_or_notation_gaps: { type: 'array', items: { type: 'string' } },
    code_followability: { type: 'string' },
  },
  required: ['learnability_verdict', 'friction_points', 'code_followability'],
}
const FACULTY_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    fidelity_verdict: { type: 'string', enum: ['faithful', 'minor gaps', 'notable gaps', 'inaccurate'] },
    fidelity_findings: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: { flw_section: { type: 'string' }, issue: { type: 'string' }, severity: { type: 'string', enum: ['high', 'medium', 'low'] } },
      required: ['issue', 'severity'] } },
    notation_expression_issues: { type: 'array', items: { type: 'string' } },
    example_assessment: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: { example: { type: 'string' }, correct: { type: 'boolean' }, supports_concept: { type: 'boolean' }, note: { type: 'string' } },
      required: ['example', 'correct', 'supports_concept'] } },
    rigor_gaps: { type: 'array', items: { type: 'string' } },
    precision_standard_flags: { type: 'array', items: { type: 'string' } },
    rag_used: { type: 'boolean' },
  },
  required: ['fidelity_verdict', 'fidelity_findings', 'example_assessment'],
}
const ADJ_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    summary: { type: 'string' },
    local_changes: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        id: { type: 'string' }, slide_or_section: { type: 'string' }, change: { type: 'string' },
        rationale: { type: 'string' }, priority: { type: 'string', enum: ['high', 'medium', 'low'] },
        raised_by: { type: 'array', items: { type: 'string', enum: ['student', 'faculty', 'both'] } },
      },
      required: ['id', 'change', 'priority', 'raised_by'] } },
    global_changes: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        id: { type: 'string' }, target: { type: 'string', enum: ['template', 'spec', 'notation', 'all_decks', 'timing_plan'] },
        change: { type: 'string' }, rationale: { type: 'string' }, priority: { type: 'string', enum: ['high', 'medium', 'low'] },
        raised_by: { type: 'array', items: { type: 'string', enum: ['student', 'faculty', 'both'] } },
      },
      required: ['id', 'target', 'change', 'priority'] } },
    conflicts_resolved: { type: 'array', items: { type: 'string' } },
  },
  required: ['summary', 'local_changes', 'global_changes'],
}
const CONS_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    verdicts: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        change_id: { type: 'string' },
        status: { type: 'string', enum: ['ok', 'violates_rule', 'needs_companion_change'] },
        rule_or_obligation: { type: 'string' }, detail: { type: 'string' },
      },
      required: ['change_id', 'status'] } },
    global_obligations: { type: 'array', items: { type: 'string' } },
    overall: { type: 'string' },
  },
  required: ['verdicts', 'overall'],
}

// ---- Phase 1: parallel audits (barrier: adjudicator needs both) ----
phase('Audit')
const studentPrompt = `You are a capable UNC Gillings Biostatistics MASTERS STUDENT who will be taught from this BIOS 667 lecture deck. You know intro regression and the earlier chapters of this course, but you are NOT an expert.
Use the Read tool to read the deck: ${deckPath}
Review it ONLY from the learner's perspective. Judge:
- Can you follow it cold? Where exactly would you get lost (cite slide titles)?
- Is notation introduced/defined before it is used? Are prerequisites adequate?
- Is the pacing realistic for 75-minute classes (see ${TIMING})?
- Do the worked examples build intuition, or just show output?
- Is the R code followable: could you adapt it to a homework problem? Comment on clarity.
- DENSITY / "BORING": flag any slide that is a wall of text or bullets, or a concept that is told in
  prose where a figure, diagram, schematic, or annotated plot would land better. Name the slide and say
  whether it should be SPLIT into two slides or given a VISUAL. Students most often complain the slides
  are "boring", so be a tough critic here. (Structural slides, objectives/prerequisites/summary/
  check-your-understanding, may stay text; judge content slides.)
- Is notation shown that has NOT been introduced yet (e.g. random-effect or GEE symbols on an early
  lecture)? Flag premature notation.
Do NOT judge research-level statistical rigor or textbook fidelity; a faculty reviewer covers that.
Be specific and constructive. Return structured findings with slide references.`

const facultyPrompt = `You are a BIOSTATISTICS FACULTY member who has taught the Fitzmaurice, Laird & Ware (FLW) longitudinal-data course (Harvard BIO 226). You are an expert reviewer.
Read the deck (Read tool): ${deckPath}
Read the course rules: ${SPEC} ; the notation reference ${NOTATION} ; and honor the Statistical Precision Standards in ${CLAUDEMD}.
Check FIDELITY using the project RAG: via ToolSearch load the bios667-corpus tools and run check_lecture_sync for chapter ${chapter}, and search_textbook/search_all for the key claims and the chapter outline. If the MCP tools are unavailable, set rag_used=false and review from your FLW expertise and the deck text.
Judge:
- Fidelity to FLW Ch. ${chapter}: section coverage and correctness of stated results (cite FLW sections).
- Correctness of mathematical EXPRESSION and NOTATION (consistency, definitions, matrix/vector bolding).
- For EACH worked example: is it correct, and does it actually SUPPORT the concept it accompanies?
- Statistical rigor and any PRECISION-STANDARD violations: re.form=NA misdescribed as marginal mean; attenuation constant; "invalid inference" vs "biased SEs"; REML vs ML usage; boundary/mixture caveat; GEE MCAR vs IPW-GEE MAR.
Be specific; cite FLW sections. Return structured findings.`

const [student, faculty] = await parallel([
  () => agent(studentPrompt, { label: 'student-reviewer', phase: 'Audit', schema: STUDENT_SCHEMA }),
  () => agent(facultyPrompt, { label: 'faculty-reviewer', phase: 'Audit', schema: FACULTY_SCHEMA }),
])

// ---- Phase 2: adjudicate ----
phase('Adjudicate')
const adjPrompt = `You are the ADJUDICATOR for a BIOS 667 reference-deck review. You have two independent reviews of the deck ${deckPath}:
- A student review optimizing for LEARNABILITY.
- A faculty review optimizing for RIGOR and FLW FIDELITY.
Read the spec ${SPEC} and the template ${TEMPLATE} so your plan respects the deck framework.
Synthesize both into a concrete CHANGE PLAN, separating:
- LOCAL changes: specific to THIS deck/chapter, ideally slide-level.
- GLOBAL changes: things that should change the shared TEMPLATE, SPEC, NOTATION reference, TIMING plan, or apply across ALL decks.
For each item give: the change, the rationale, a priority, and which reviewer(s) raised it. Where the two perspectives CONFLICT (e.g. student wants less math, faculty wants more rigor), resolve it with an explicit recommendation and record it in conflicts_resolved. Propose only; do not edit files.
STUDENT REVIEW (JSON): ${JSON.stringify(student)}
FACULTY REVIEW (JSON): ${JSON.stringify(faculty)}`

const adjudicator = await agent(adjPrompt, { label: 'adjudicator', phase: 'Adjudicate', schema: ADJ_SCHEMA })

// ---- Phase 3: consistency check ----
phase('Consistency')
const consPrompt = `You are the CONSISTENCY reviewer. You are given a proposed CHANGE PLAN (local + global) for a BIOS 667 reference deck. Your job is to ensure the changes do not violate the course rules and would be applied consistently.
Read the rule sources (Read tool): ${SPEC} ; ${CLAUDEMD} (writing rules: no em-dashes, no gratuitous semicolons, no AI-tells; and the Statistical Precision Standards) ; the notation master ${NOTATION} ; and the shared notation partial ${NOTATION_PARTIAL}.
For EACH proposed change (use its id), return a verdict:
- ok: consistent with the rules and self-contained.
- violates_rule: name the rule it breaks (e.g. would introduce an em-dash; contradicts the spec; restates re.form=NA as a marginal mean).
- needs_companion_change: it is fine only if other files change together (e.g. a notation change requires editing BOTH ${NOTATION} AND ${NOTATION_PARTIAL} AND every deck that includes the partial; a global template change must also update the spec checklist).
Then list GLOBAL OBLIGATIONS: for each accepted global change, the exact set of files that must be updated together so the change is consistent and no rule is violated.
Propose only; do not edit files.
CHANGE PLAN (JSON): ${JSON.stringify({ local_changes: adjudicator.local_changes, global_changes: adjudicator.global_changes })}`

const consistency = await agent(consPrompt, { label: 'consistency', phase: 'Consistency', schema: CONS_SCHEMA })

return { deckPath, chapter, student, faculty, adjudicator, consistency }
