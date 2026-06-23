# Post-Lecture-Creation Review (reference decks)

**Run this after a reference deck is drafted or substantially edited, before handing it to David.**
It is a repeatable QA pass over four substantive dimensions plus a render/pacing gate. The output is
a per-deck audit file `2026/lectures/<DECK>_reference_audit.md` (see `BIOS667_L08_reference_audit.md`
as the worked example). "Reviewed" means that dated audit file exists and every dimension is signed
off, not just a mental check.

It can be run by David by hand, or handed to Claude as: "review `<DECK>.qmd` against
`2026/POST_LECTURE_REVIEW.md` and write the audit file." Either way, record evidence, not opinions.

The four dimensions below are the ones that matter most: does it match the book, is the notation and
language correct, are the examples right and on-point, and is the R code actually instructive.

---

## Gate 0: it renders

The deck must build before anything else is judged.

```bash
quarto render 2026/lectures/<DECK>.qmd --to revealjs   # must exit 0
```

If a chunk fails on a missing package, install it (the course stack is in CLAUDE.md) and re-render.
A non-zero exit blocks the review. Record the exit status in the audit.

## Gate 0b: narrative matches the computed output (REQUIRED; the B4 L10/codex lesson)

A clean render and correct formulas are NOT enough. **Execute the chunks and confirm that every
analysis-derived number and every data-derived verdict on each slide matches what the chunk actually
produces on the actual dataset.** This is the step that caught L10's two real defects (a variogram slide
asserting "the random-intercept-only model drifts off 1" when re-running gave both models hovering near 1;
an ACF slide saying "lag-1 within bands, no `corAR1` needed" when the normalized-residual lag-1 was about
-0.47, outside the band). Procedure:

- Re-run each chunk (or render with results visible) and read the OUTPUT, not just the code.
- For every stated number, pattern word ("rises", "flat", "drifts", "within bands"), or verdict
  ("adequate", "needed", "no `corAR1`"), confirm the chunk's result on the actual data supports it. A
  pattern the data does not show is a defect even if the code runs and the math is right.
- **Prefer inline R over hardcoded values** for any analysis-derived quantity (`` `r round(...)` `` from the
  fitted object), so the slide cannot drift from the code; reserve hardcoded constants for fixed inputs
  (`set.seed`, $\rho=0.8$), never estimates. Grep the deck for hardcoded ORs/RRs/variance components.
- If a real dataset does not exhibit the intended teaching pattern, report it honestly or use a clearly
  labeled simulation to isolate the pattern; never assert a contrast the data does not produce.
- This is a REQUIRED reviewer step you perform; it is NOT fully automated. The on-commit codex hook
  (`lecture-stat-review.sh`, lens 4) now ATTEMPTS the re-run, but only best-effort: it needs codex's
  read-only sandbox to initialize AND to run R (the bwrap sandbox is flaky here), and the same-model claude
  fallback cannot run chunks at all. So do the re-run yourself during the review; treat a clean hook pass
  as no evidence that this gate was checked.

## Dimension A: reflects the book correctly (textbook fidelity)

- **Outline coverage.** Get the FLW chapter outline and map every deck section to it; flag any major
  section unaddressed.
  - `get_chapter_outline(chapter=N)` (bios667-textbook), or `search_all(..., source_type='textbook', chapter=N)`.
- **Sync check (RAG).** Run `check_lecture_sync` by chapter/topic/path; review `gaps` and
  `possible_mismatches`. Reliable for FLW Ch. 1-16; see the CLAUDE.md caveats for the resequenced
  late topics (course L17-L19 labels do not match FLW Ch. 17-19) and the dense-PDF-fragment false gaps.
  - **Run it in the orchestrator (main session), not the headless panel.** The `bios667-corpus`/
    `bios667-textbook` MCP servers are frequently NOT reachable from headless workflow subagents (the
    panel's faculty agent then reports `rag_used=false`), so do the RAG check here. If the MCP is not
    connected, call it directly through the venv (no MCP needed), e.g.
    `rag/.venv/bin/python -c "from bios667_rag.corpus_query import CorpusQuery; print(CorpusQuery(store_dir='rag/data').check_lecture_sync(N))"`.
  - **Refresh the index first** after editing a deck (`rag/.venv/bin/bios667-index-corpus`, incremental)
    so the sync reflects the current text. A `covered=0` for a chapter usually means a stale index or a
    chapter-tagging gap (the lecture's chunks are not tagged to that chapter), not a true coverage gap;
    investigate before treating it as missing content.
  - Also **check against the consistency docs**: `2026/CONSISTENCY_LEDGER.md`, `NOTATION_REFERENCE.md`,
    and `REFERENCE_DECK_SPEC.md` (the cross-lecture sweep does this; the per-deck pass should too).
- **Claim-level wording.** For each key definition or result, confirm the wording against the book
  with `search_textbook` / `get_concept`. Cite the section, do not paraphrase from memory.
- **Book-departure scan (REQUIRED).** Go method-by-method, slide-by-slide, and classify EACH technique,
  formula, diagnostic, and claim as either **in this FLW chapter** or **beyond it**. Ground each call in
  the textbook (RAG `search_all(..., source_type='textbook', chapter=N)` plus the chapter PDF in
  `book/`), not memory. Then:
  - Anything **beyond the chapter** (an instructor extension) must be explicitly flagged "beyond FLW"
    with an external citation, or removed. An unflagged beyond-FLW item is a departure.
  - Anything that **contradicts or misrepresents** the book (a different procedure, emphasis, formula,
    constant, df, or definition) is a departure and must be fixed.
  - Prefer the book's own method when the deck invents an alternative: e.g. FLW Ch. 6 judges whether a
    curve term belongs via the **likelihood-ratio test** and the **observed-vs-fitted overlay**, NOT a
    partial-residual / component-plus-residual plot (a real B2 catch: L06 had an unflagged, and
    incorrect, partial-residual diagnostic). Record confirmed departures in the audit.
  - **Two sources, not memory.** Cross-check every numeric value, table, constant, and stated conclusion
    against (a) the chapter **PDF** in `book/` (read the actual table/figure) and (b) the **RAG**. The
    RAG alone misses numeric/table mismatches; the L05 Table 5.6 means and the L06 quadratic-vs-linear
    conclusion were only caught by reading the PDF.
  - **Also check the AUTHORS' slides (REQUIRED).** Query the FLW authors' BIO 226 slides, now indexed:
    `search_all(..., source_type='author_slides')` (no chapter filter; the PDF is one whole-course deck,
    66 chunks). Check both DEPARTURES (does the deck's method/dataset/conclusion match the authors'
    presentation?) and OMISSIONS (does the authors' slide for this topic emphasize something the deck
    skips, or vice versa?). The B2 author-slides pass confirmed FLW's Ch. 6 example is the smoking
    (Vlagtwedde-Vlaardingen) data with unstructured covariance + REML, which drove the L06 fixes.
  - **CLAUDE.md constants are themselves fidelity sources, not ground truth.** A constant/formula
    enshrined in the project standards can be wrong-as-general: `RE = 2/(1+\rho)` is only the
    single-follow-up (n=2) case of the ANCOVA-vs-change *efficiency* `n/{1+(n-1)\rho}` (the reciprocal of
    FLW eq (5.3)'s variance ratio `(1/n){1+(n-1)\rho}`), presented as if general. When an audit flags a
    formula/constant, VERIFY against the PDF before dismissing it (the B2 audit was right; the first
    instinct to wave it off was wrong).
  - **Worked-example method attribution.** When a deck shows R/SAS for a chapter's example, the method
    must match what FLW uses for THAT example or the deviation must be stated: estimation mode (REML for
    reported coefficients, ML only for mean-structure LRTs), working covariance (FLW Ch. 6 case studies
    use unstructured, not CS), and test framing (FLW Ch. 5 = Wald CHISQ, not `ddfm=kr` Kenward-Roger).
- **Caution-reversal scan (REQUIRED, highest severity; B4 lesson).** Query the RAG/PDF for the chapter's
  explicit cautions ("we caution", "should not be used", "do not") and verify the deck does NOT teach the
  opposite. Check every covariance/diagnostics/GLMM deck against the running list in
  `CONSISTENCY_LEDGER.md` ("FLW explicit cautions"). L10 originally taught BLUP/empirical-Bayes QQ plots to
  judge random-effects normality, which FLW p.273 explicitly cautions AGAINST (shrinkage).
- **Core-method coverage (REQUIRED; B4 lesson).** Identify the chapter's PRIMARY method (its defining
  equations/figures, via the chapter outline) and confirm the deck CENTERS it. The dominant B4 departure
  was "the chapter's actual core method is missing, replaced by an adjacent-tradition substitute" (L10
  omitted FLW Ch.10's transformed-residual eq 10.2 + Mahalanobis eq 10.3 in favor of a software-vocabulary
  marginal/conditional taxonomy + recursive CUSUM).
- **Forward-/backward-chapter leakage (REQUIRED).** Content FLW defers must be flagged as a preview, not
  presented as this chapter's. Verify every inline FLW page citation falls within the deck's chapter page
  range (L12 cited "FLW p.528" on a Ch.12 deck; p.528 is in the missing-data chapters).
- **Gate: no fabricated diagnostics/results.** `grep -nE 'rnorm|sample\(|runif'` the deck; every hit must
  be a clearly-labeled illustrative DGP, never a fabricated diagnostic/estimate plotted or reported as
  computed (the L10 `abs(rnorm())` "cluster influence" plot). A "pre-computed for speed" stand-in must be
  the real (subsetted) computation. This is a hard gate, like Gate 0.
- **Precision standards (must hold).** `re.form=NA` is not a marginal mean; **`residuals.lme()` defaults to
  CONDITIONAL (innermost), `level=0` for marginal** (the nlme analog of the `re.form=NA` trap); attenuation
  c approx 0.346 (probit) or note FLW p. 477 k approx 0.588; "invalid inference"/"incorrect SEs" not
  "biased SEs"; REML for variance components, ML for LRT of fixed effects; boundary/mixture caveat for
  variance-component tests (dropping a random slope removes TWO parameters -> 1/2 chi^2_1 + 1/2 chi^2_2);
  standard GEE needs MCAR (IPW-GEE for MAR). See the CLAUDE.md Statistical Precision Standards.
- **No unattainable output.** A deck must not recommend output the shown package cannot produce. If it
  recommends Kenward-Roger or Satterthwaite df, it must state that `nlme::lme` provides neither
  (containment df only) and that they require `lme4` + `lmerTest` or `pbkrtest`.

## Dimension B: correct expression and notation

- **Canonical notation.** The deck includes the shared notation slide
  (`{{< include _notation_box.qmd >}}`) and uses symbols consistent with `2026/NOTATION_REFERENCE.md`
  (bold = vector/matrix; $i$ subject, $j$ time, $k$ state, $g$ group).
- **No drift.** Grep the deck for the same object written two ways (e.g. `Z_i` vs `\mathbf{Z}_i`,
  $D$ vs $G$ mid-deck). Symbols defined at first use.
- **Math renders.** Confirm in the rendered HTML (browser) that every `$$...$$` and `$...$` displays;
  no raw TeX or "Math input error".
- **Language.** Plain, instructor voice. No em-dashes, no gratuitous semicolons, no AI-tells
  (see the spec's Writing Voice section). Interpretations state units and direction.

## Dimension C: examples are correct and support the concept

- **Correctness.** Each worked example uses a real FLW dataset; spot-check that the reported numbers
  match the code output and, where the book analyzes the same data, match (or are reconciled with) FLW.
  - `get_examples(...)` / `find_examples(...)` to compare against the book's worked example.
- **On-point.** Each example sits next to the concept it demonstrates and actually demonstrates it
  (concept -> example linkage is explicit, not incidental). The interpretation answers a real
  question, not just "the p-value is small."
- **Coverage.** At least one full Case Study on real data (matches the FLW "Case Studies" section),
  distinct from small illustrative snippets.

## Dimension D: R code is informative (common and unique tasks)

- **Runs clean** (Gate 0) and follows the course stack (`nlme`/`lme4`/`geepack`/`emmeans`) and style
  (code slide -> output slide via `#| output-location: slide`; comments explain each step).
- **Common tasks shown.** The bread-and-butter workflow for the chapter: fit, summarize, predict,
  test, diagnose.
- **At least one less-obvious task shown.** Something a student would not guess from the basics, e.g.
  heteroscedastic residuals (`varIdent`), residual `corAR1`, `emmeans` contrasts, a boundary-aware
  LRT, extracting EBLUPs, or recreating a spline basis in `newdata`. Note which "unique" task(s) the
  deck teaches.
- **SAS reference.** A static, non-executed SAS-equivalent slide is present and is a **complete
  standalone program** (a full PROC MIXED block, not a cheat-sheet fragment table), per the spec
  (mirrors FLW's Computing section and 2025 practice). A translation table may accompany it but does
  not satisfy this item on its own.
- **Beyond-FLW extensions flagged.** Any material beyond the FLW chapter (instructor enrichment, e.g.
  Lord's paradox in Ch. 5) is labeled as such and carries an external citation.
- **Reused control objects are self-documenting.** If a shared control/options object (e.g. an `nlme`
  `lmeControl` object) is reused across many fits, it is explained once at first appearance, and any
  setting that can mask failure (e.g. `returnObject=TRUE` masking non-convergence) is flagged.
- **Each diagnostic plot has a per-slide reading rule.** Every diagnostic slide (ACF, semivariogram,
  residual, QQ) states the good vs problematic pattern and what each reference line means, not just one
  general annotation somewhere in the deck (CLAUDE.md "annotate diagnostic plots").

## Gate E: pacing, density, and visual engagement

- **75-minute fit.** Slide count and Part dividers are consistent with `LECTURE_TIMING_PLAN.md`
  (about 25-40 slides per 75-minute block; multi-period decks carry `# Part N (Day N): ...` seams).
- **Density / "boring" check (automatic).** Run `python3 2026/workflows/slide_density_check.py <deck>`.
  It flags slides that are too dense (too many words/bullets) or are a wall of prose with NO visual.
  For each flagged CONTENT slide, either **split** it into two slides or **add a visual** (an R plot, a
  diagram/schematic, an annotated figure, or at least a table). The course style is illustrations over
  text (CLAUDE.md "Visual Learning First", "Illustrations are preferred over text"); a deck that is a
  wall of bullets is the most common student complaint ("boring"). Structural slides (objectives,
  prerequisites, summary, Check-Your-Understanding) are exempt from the needs-a-visual flag but a very
  long one can still be split. Generate diagrams with the `scientific-schematics` skill or a `ggplot`.
- **Notation is graduated to what is introduced.** The notation slide shows ONLY symbols introduced by
  this lecture: an intro/Ch.1 deck may have NO notation slide; `_notation_box_intro.qmd` (lite) once the
  basic notation is introduced; the full `_notation_box.qmd` from L08. Do not front-load later symbols.
- **No empty slides.** `slide_density_check.py` flags a `---` placed immediately before a `# ` section
  divider (and doubled `---`), which renders a BLANK slide; remove the stray `---`. A clean render does
  not catch this, so it is a required check.
- **Visual scan (step through every slide).** Open the rendered deck in Chrome and step through ALL
  slides (not just the changed ones) looking for blank slides, content overflowing the frame, clipped
  tables, dense code, or broken math/layout. Fix what you find. Repeat for every deck in the batch.
  - **A clean render (exit 0) does NOT mean every slide is visible.** A large figure placed under prose
    on a `scrollable` slide renders but overflows off-view (this happened to L03's block-diagonal
    heatmap). Put a substantial figure on its OWN slide (a dedicated `## ` chunk slide; note
    `#| output-location: slide` is unreliable for an `echo:false` chunk). Only the visual step-through
    catches this.
  - **How to step through.** Serve the rendered HTML over a local http server (`python3 -m http.server`)
    and open it in Chrome; the `file://` scheme is blocked by the navigate tool. The decks are
    `incremental: true`, so disable fragments before capturing so each slide shows its full content at
    once: in the browser console run `Reveal.configure({fragments:false, transition:'none'})`, then jump
    by slide id or step with the arrow keys.

---

## Audit file template

Write findings to `2026/lectures/<DECK>_reference_audit.md`:

```markdown
# <DECK> Reference-Deck Audit
**Deck / Chapter / Date / Reviewer:** ...
**Gate 0 (renders):** quarto exit 0 (or the failure + fix)
## A. Textbook fidelity
- Outline coverage: ... ; check_lecture_sync gaps/mismatches reviewed: ... ; precision standards: ...
## B. Expression and notation
- Canonical notation included; drift grep: ... ; math renders: ... ; voice: ...
## C. Examples
- Correctness (numbers match): ... ; on-point: ... ; Case Study present: ...
## D. R code
- Runs clean: ... ; common tasks: ... ; unique task(s) taught: ... ; SAS slide: ...
## E. Pacing / visual
- Slides / periods vs timing plan: ... ; visual scan: ...
## Verdict
- Meets spec: yes/no. Open items: ...
```

A deck is **review-complete** when this file exists, every dimension is addressed with evidence, and
there are **no open must-fix items**. An open must-fix item (a correctness or notation error, not a
polish suggestion) makes the verdict **conditional**, not complete: list it explicitly and resolve it
before the deck is considered done. Improvement-only items may remain as a documented backlog without
blocking completion.

---

## Multi-perspective review panel (deeper pass)

The single-reviewer pass above is the baseline. For a higher-stakes or final review, run the
four-role **panel**, orchestrated by `2026/workflows/lecture_review_panel.mjs`. It is **propose-only**:
it never edits files. It produces two independent reviews, a change plan, and a consistency report
that you approve before anything is changed.

**Roles**

1. **UNC Gillings BIOS masters student (learnability).** Reviews only as the learner: can the deck be
   followed cold, is notation defined before use, is the 75-minute pacing realistic, do the examples
   build intuition, is the R code adaptable. Does not judge research rigor.
2. **Harvard biostatistics faculty, FLW course (rigor + fidelity).** Expert reviewer. Checks fidelity
   to FLW (via the RAG: `check_lecture_sync`, `search_textbook`), correctness of expression and
   notation, whether each example is correct and supports its concept, statistical rigor, and the
   precision standards. Cites FLW sections.
3. **Adjudicator (synthesis).** Turns the two reviews into a concrete change plan, separating **LOCAL**
   changes (this deck/chapter, slide-level) from **GLOBAL** changes (template, spec, notation master,
   timing plan, or all decks). Resolves student-vs-faculty conflicts with an explicit recommendation.
4. **Consistency reviewer (guardrail).** Checks each proposed change against the rules (spec, CLAUDE.md
   writing rules + precision standards, the notation master and shared partial). Marks each `ok`,
   `violates_rule`, or `needs_companion_change`, and lists the **global obligations**: the exact set of
   files that must change together so a global edit stays consistent (e.g. a notation change must touch
   `NOTATION_REFERENCE.md` AND `_notation_box.qmd` AND every deck that includes it).

**Flow.** Student + faculty run in parallel (independent lenses), then the adjudicator (needs both),
then the consistency reviewer (needs the adjudicator's plan).

**Local vs global.** Local items are applied to the one deck. Global items change the shared framework
and must follow the consistency reviewer's global obligations so all decks stay in sync.

**How to run.**

```
Workflow({ scriptPath: "2026/workflows/lecture_review_panel.mjs" }, { deckPath: "<deck>.qmd", chapter: N })
```

The run returns `{ student, faculty, adjudicator, consistency }`. Record the result in the deck's audit
file, apply the approved LOCAL changes to the deck, and apply approved GLOBAL changes across the files
named in the global obligations (then re-run the single-reviewer pass to confirm). Nothing is edited
until you approve.

---

## Commit-time statistical review (project hook)

`2026/workflows/lecture-stat-review.sh` is a project-scoped commit hook that adds a **statistical /
methodological / consistency** lens to every commit touching course content, complementing the global
code/prose commit review. It is read-only and advisory (proposes, never edits). Two modes, matching the
first-version-vs-subsequent rule:

- **A content file is modified (subsequent version):** it reviews the *diff* for statistical and
  methodological correctness (boundary mixtures and df, ML vs REML, KR/Satterthwaite availability,
  re.form/level marginal-mean claims, GEE MCAR, constants, valid-inference language), notation and
  terminology consistency with `NOTATION_REFERENCE.md` / `_notation_box.qmd`, and cross-reference
  integrity.
- **A new lecture/homework file is added (first version):** a diff review is insufficient, so it
  **flags** that the full first-version panel (above) should be run on the new file. It does not
  auto-launch the panel.

This is the cheap, automatic guard that catches statistical errors at commit time (the kind a code-only
review misses); the full panel remains the deep, on-demand review. **Enable it once per machine** by
wiring it into `.claude/settings.json` (gitignored, per-machine) per the setup note in the script
header, then approve the hook when Claude Code prompts.
