# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **BIOS 667 Applied Longitudinal Data Analysis** course repository (UNC Gillings School of Public Health). Contains Quarto-based lecture slides (RevealJS format), homework assignments, and curated datasets. Based on Fitzmaurice, Laird & Ware (2011).

## Build Commands

```bash
# Render a lecture deck to RevealJS slides
quarto render BIOS667_L05_ResponseProfiles_ch5.qmd --to revealjs

# Render homework or other documents
quarto render HW3.qmd

# Live preview with auto-reload
quarto preview schedule.Rmd

# Validate Quarto/Pandoc/R setup
quarto check

# Run helper R scripts
Rscript -e "source('Peer_Assessment_Instructions.qmd.R')"
```

After rendering, open `.html` files in a browser to verify math rendering and slide animations.

## Directory Structure

- **Root**: Lecture `.qmd` files named `BIOS667_L##_Topic.qmd` (keep numeric sequence)
- **data/**: Shared datasets (dental.txt, epilepsy.txt, fev1.txt, etc.)
- **figs/**: Reusable figures and templates
- **book/**: Reference PDFs (read-only)
- **rag/**: Textbook RAG system with knowledge graph
- **unc-gillings.css**: Centralized RevealJS styling

Rendered artifacts (`.html`, `_files/` folders) stay adjacent to their source files.

## Code Style

- **YAML**: Two-space indentation, concise keys, `execute` options once per file
- **R chunks**: snake_case for objects, ~90 char line limit, chunk options with `#|` prefix
- **File naming**: `BIOS667_L##_Topic.qmd` pattern, sentence-case section headings

## Core R Packages

Statistical modeling: `nlme`, `lme4`, `glmmTMB`, `geepack`, `MASS`
Data/visualization: `dplyr`, `tidyr`, `ggplot2`
Inference: `emmeans`, `sandwich`, `clubSandwich`, `car`
Model output: `broom`, `broom.mixed`

Target: R 4.5.1, Quarto ≥ 1.5

## Architecture

**Lectures** may optionally follow a pedagogical structure:
1. Retrieval warm-up (no AI)
2. Concept & derivation (no AI)
3. Board → code bridge
4. Worked examples (hand-specified models)
5. AI-augmented practice (marked "AI-on")
6. Exit ticket (no AI)

This structure is a guideline, not a requirement. Adapt based on topic and class needs.

**Homework** emphasizes conceptual depth over mechanics. Key statistical topics:
- Linear mixed effects (LME) with covariance structures (CS/AR1/UN)
- Generalized estimating equations (GEE) with working correlations
- Generalized linear mixed models (GLMM) with attenuation formula
- Model comparison (marginal vs conditional interpretations)

**Homework schedule:** One assignment per every 3 lectures (e.g., HW1 covers L01-L03).

## Commit Messages

Use present-tense, lecture-scoped messages: `Lecture: add L05 response-profile visual`

---

## Lecture Guidelines

When creating or updating lectures, follow these guidelines to ensure consistency and textbook fidelity.

### Reference-Deck Framework and Review (2026 traditional track)

The 2026 reference decks (taught by David Zhang, traditional HW + final project) follow a documented
framework. When authoring or editing a 2026 reference deck, work to these files:

| File | Role |
|------|------|
| `2026/REFERENCE_DECK_SPEC.md` | What a reference deck must contain (the bar) |
| `2026/lectures/BIOS667_Reference_Deck_Template.qmd` | Skeleton to copy; includes the writing-voice guardrail |
| `2026/NOTATION_REFERENCE.md` + `2026/lectures/_notation_box.qmd` (+ lite `_notation_box_intro.qmd`) | Canonical notation; decks render the slide via `{{< include _notation_box.qmd >}}` (or the lite `_notation_box_intro.qmd` for intro decks before random effects/GEE); never hand-paste a notation table |
| `2026/LECTURE_TIMING_PLAN.md` | 75-minute class pacing; per-lecture period counts |
| `2026/POST_LECTURE_REVIEW.md` | The post-creation review pass; output is `2026/lectures/<DECK>_reference_audit.md` |
| `2026/workflows/lecture_review_panel.mjs` | Per-lecture multi-perspective review panel (run via the Workflow tool) |
| `2026/SCALING_PLAN.md` | How to review all 18 decks: lint -> panel-for-all -> per-batch cross-lecture sweep |
| `2026/CONSISTENCY_LEDGER.md` | Persistent cross-lecture decisions (notation, terminology, datasets, cross-ref map, global-change history) |
| `2026/workflows/cross_lecture_consistency.mjs` | Cross-lecture consistency sweep (per batch + final), checks what the per-lecture panel cannot |
| `2026/workflows/lecture-stat-review.sh` | Project commit hook: statistical/methodological/consistency review of each content diff (+ flags new lectures for a full review). Enable per-machine in `.claude/settings.json` |

**After drafting or substantially editing a reference deck, run the post-creation review**
(`2026/POST_LECTURE_REVIEW.md`): a render gate plus four dimensions (textbook fidelity, expression and
notation, examples correct and on-point, R code informative for common and unique tasks) plus a
75-minute pacing check, recorded in a dated per-deck audit file. For a deeper or final pass, run the
**multi-perspective panel** (UNC masters student for learnability + Harvard FLW faculty for rigor ->
adjudicator local/global change plan -> consistency guardrail). The panel is **propose-only**: it never
edits files; apply changes only after approval, and for global changes follow the consistency agent's
"global obligations" so all decks stay in sync. `BIOS667_L08_Covariance_ch8_LME.qmd` and its audit are
the worked exemplars. Honor the writing-voice rules (no em-dashes, no gratuitous semicolons, no AI-tells)
and the R-runnable-plus-static-SAS-slide convention in every deck.

**To review all 18 decks at scale, follow `2026/SCALING_PLAN.md`:** a mechanical lint sweep, the full
panel on every lecture, concept-cluster batches (B1-B6), and an auto cross-lecture consistency sweep
(`cross_lecture_consistency.mjs`) at each batch boundary plus one final global sweep. Every batch
conforms to `2026/CONSISTENCY_LEDGER.md` (the persistent cross-lecture decision record); record new
cross-lecture decisions and global changes there so later batches stay consistent.

### Recurring authoring pitfalls (learned the hard way; avoid these)

These bit us repeatedly while building the 2026 decks. They are enforced by `slide_density_check.py`,
the per-deck review (`POST_LECTURE_REVIEW.md`), and the ledger, but check them as you author so they do
not recur:

1. **Empty slides.** Never put a `---` immediately before a `# ` section divider: the `#` already starts
   its own slide, so the `---` renders a BLANK slide. (`slide_density_check.py` flags it.) Do NOT remove
   the YAML-closing `---`.
2. **A clean render does not mean a visible slide.** `quarto render` can exit 0 while a plot is invisible:
   a large figure crammed under prose on a `scrollable` slide overflows off-view. Put a substantial
   figure on its OWN slide. The robust pattern is a dedicated `## ` slide containing only the chunk;
   `#| output-location: slide` is NOT reliable for an `echo: false` chunk (it may not create a separate
   slide). ALWAYS do a Chrome step-through of every slide (a blank/overflowing slide only shows up visually).
3. **Graduated notation.** Show only notation introduced so far: NO notation slide on a Ch.1 intro deck;
   the lite `_notation_box_intro.qmd` from Ch.2; the full `_notation_box.qmd` from L08. Never front-load
   random-effect/GEE symbols.
4. **Notation canon (no collisions).** Covariate is the row $X_{ij}$ ($1\times p$); write the mean model
   $X_{ij}\beta$, not $\beta^\top x_{ij}$. Error term is $\varepsilon$ (never $e_i$). $Z_i$/$b_i$ are
   random effects ONLY (never a fixed covariate $z_{ij}$). Subject count is $N$ ($i=1..N$); occasion
   count is $n$/$n_i$ (FLW Section 3.2, never $n$ for subjects). $V_i =
   \operatorname{Cov}(Y_i)$ in general; the $Z_i D Z_i^\top + R_i$ decomposition only from Ch.8.
5. **No dashes.** No em-dashes AND no en-dashes; write ranges with a hyphen ("Ch. 7-8", "pp. 43-44").
6. **Density / "boring".** Run `slide_density_check.py`; split wall-of-text slides and add a
   figure/diagram/schematic. Illustrations over text is the single biggest student-satisfaction lever.
7. **Cross-references after edits/splits.** If you move content between lectures, repoint every "recall
   from Lecture N / see Ch. M" reference (a split left dangling L01->L02 pointers).
8. **Statistical precision (the ones that slipped through code review).** Boundary variance-component
   tests use the right 50:50 mixture: dropping a random slope from a random-intercept model removes TWO
   parameters, so it is $\tfrac12\chi^2_1+\tfrac12\chi^2_2$ (Stram-Lee), NOT a simple halving. `nlme::lme`
   reports containment df, not Kenward-Roger/Satterthwaite. Use `set.seed(667)`.
   **`exactRLRT`/`RLRsim` are valid for the Gaussian LMM ONLY** (they exploit the linear-model RLRT
   null distribution). For a **GLMM** variance-component boundary test (e.g. dropping a random slope in a
   Poisson/logistic mixed model, L14/L15), do NOT use `exactRLRT`; use a **parametric bootstrap** of the
   LRT statistic (`pbkrtest::PBmodcomp` or a hand-rolled `simulate()`-refit loop), or report the
   conservative Stram-Lee $\tfrac12\chi^2_1+\tfrac12\chi^2_2$ mixture as an approximation. L14 replaced its
   `exactRLRT` call with a parametric bootstrap for exactly this reason.
9. **FLW data-loading gotchas.** The FLW `.txt` files are not uniform. Some ship with a multi-line comment
   header and some are already WIDE, not long (e.g. `dental.txt` has a comment-header block and one row per
   child with age8/age10/age12/age14 columns). A plain `read.table(header=TRUE)` will fail or mis-parse;
   INSPECT the header first (`readLines`) and reshape as needed. Always load via a download-fallback path
   (`../../data/<file>`, download from the FLW site if missing), and check the dataset actually loads at
   render time before relying on it. The setup chunk downloading a file does not mean a later chunk uses it.
10. **Reuse the running examples and datasets.** Use the same datasets and the same illustrative constants
    across decks (e.g. AR(1) $\rho = 0.8$, `set.seed(667)`, the canonical dataset names) so the course
    reads as one continuous example rather than disconnected one-offs.
11. **A reference deck must not carry 2027-condensed-track machinery (the per-lecture panel will NOT flag
    this).** The reference-deck spec ("No in-class evaluation segments") forbids AI-Augmented Practice,
    AI-Aided Homework Hint, Exit Ticket, AI-mode Tutor/Critic gating, the graded oral retrieval/defense,
    and the productive-failure "first encounter" in the 2026 reference decks (those belong to the 2027
    condensed track). L06 shipped with all of these and a single-deck review missed it; only the
    cross-lecture/spec-conformance check caught it. GREP each deck for forbidden titles before commit:
    `grep -nEi 'AI-Augmented|AI-Aided|Exit Ticket|No Laptops|Tutor/Critic|first encounter'`. Allowed
    substitutes: `Check Your Understanding` boxes, plain "Worked Exercise" slides, discussion prompts.
12. **Every methods deck needs a real FLW Case Study, not simulated-only data.** L06 shipped with only
    `FEV1-like` / `TLC-like` simulated data and no real dataset. The spec requires at least one full worked
    Case Study on a real FLW dataset (fev1/tlc/dental/epilepsy, loaded with the download fallback).
    Simulations are fine for isolating a teaching point, but at least one analysis must run on real data,
    and reuse the canonical dataset another deck already loads (continuity).
13. **"GLM" means the GENERALIZED linear model only (Ch. 11+).** The general (normal) linear model in
    Ch. 3-6 is "LM" or spelled out, never "GLM" (it collides with the later generalized-linear-model
    chapters). Grep new mean-model decks for a stray "GLM".
14. **Notation follows FLW: $N$ = subjects ($i=1..N$), $n$/$n_i$ = occasions.** Do NOT use $n$ for the
    subject count (FLW Section 3.2). When a chapter reuses a non-reserved symbol with a chapter-local
    meaning the book uses (e.g. Ch. 5 $G$ = number of groups; Ch. 4/Missing-Data $R_i$ = response
    indicator), declare it up front on the lecture-specific notation slide; never reassign reserved
    $\mathbf{X}_i/\boldsymbol\beta$, $\mathbf{Z}_i/\mathbf{b}_i$. Cross-reference checks must scan speaker
    `::: {.notes}` too: an L04 note fabricated a "two lectures ago $R_i$ was the residual covariance"
    pointer that resolved to nothing.
15. **YAML conformance is a lint item.** A deck (L06) shipped with `theme: simple`, `author:
    "UNC-CH Biostatistics"`, a non-standard footer, and no `incremental:` while its batch-mates followed
    the CLAUDE.md standard. Diff every deck's YAML against the standard header (theme `[default]`, author
    "Naim Rashid", the standard footer/subtitle, `incremental: true`).
16. **`corCompSymm`/`corAR1` need the `form=` argument.** `corCompSymm(~1|id)` passes the formula
    POSITIONALLY to the wrong slot and silently fits NO working correlation; write
    `corCompSymm(form = ~ 1 | id)`. Any `nlme` correlation/weights structure: name the `form=` argument.
17. **Notation-slide formatting.** (a) Wrap every notation table (the shared include AND each deck's
    lecture-specific "Notation (this lecture)" table) in `::: {.notation-card}` so the `unc-gillings.css`
    rule narrows the Symbol column (Pandoc emits 50/50 `<col>` widths, leaving a wide left gap otherwise).
    (b) Keep the slide a TABLE, not paragraphs: move "why this symbol" prose into `::: {.notes}` speaker
    notes. (c) Inline math ending in a `)` that is immediately followed by text collides ("$(...,N)$ and"
    renders as "N)and"); write the range WITHOUT the wrapping parens (`$i = 1,\dots,N$ and`, math ends in
    a letter) or put the paren at the cell end. (d) The full `_notation_box.qmd` is the
    THROUGH-RANDOM-EFFECTS card: it does NOT front-load GEE/GLM symbols; the introducing deck adds them
    (L11 adds binary $\pi_{ij}$/dispersion $\phi$, L13 adds GEE $\alpha$) as a lecture-specific row.
18. **`{.panelset}` + `output-location: slide` is an anti-pattern (and `{.small}` makes it worse).**
    A panelset puts the CODE in tiny tabs while each `output-location: slide` plot lands on a SEPARATE,
    untitled slide, and any interpretation note is stranded back on the panelset slide. The student then
    sees a sequence of unlabeled plots and cannot tell which is which (this bit L06's "Compare Fits" and
    "Diagnostics" panels). Instead: for a model comparison, build ONE faceted plot
    (`facet_wrap(~ model)` with labeled panels Linear/Quadratic/Spline); for separate diagnostics, give
    each its own normal `## ` slide.
19. **Every plot must be self-identifying, and diagnostics carry their interpretation on the same slide.**
    (a) Always set a `labs(title=...)` (or a facet label) that names exactly what the plot shows; when
    several models/variants are compared, the viewer must be able to tell them apart from the plot alone.
    (b) Put a diagnostic plot and its "Reading it" interpretation (good vs problematic pattern, what each
    reference line means) on the SAME slide: render the plot `echo: false` inline, then a
    `::: {.callout-note}` directly below, rather than splitting plot and reading rule across slides.
20. **Book-fidelity (the B2 audit lessons; run the `POST_LECTURE_REVIEW.md` Dimension-A departure scan).**
    (a) **Dataset provenance:** a dataset must be FLW's actual example for THAT chapter (cite the
    table/figure) or carry a visible label that it is an instructor substitution. See the chapter ->
    canonical-dataset map in `2026/CONSISTENCY_LEDGER.md` (Ch. 2 = TLC placebo Tables 2.2/2.3 not dental;
    Ch. 6 = Vlagtwedde-Vlaardingen smokers not Topeka fev1.txt; fev1.txt = Ch. 9; dental = Ch. 5/7/8). A
    wrong-chapter dataset presented as canonical was the dominant departure and once flipped a conclusion
    (L06 "quadratic needed" vs FLW "linear adequate").
    (b) **Verify constants/formulas against the PDF; CLAUDE.md is a fidelity source, not ground truth.**
    `RE = 2/(1+rho)` is only the single-follow-up (n=2) case of the ANCOVA-vs-change *efficiency*
    `n/{1+(n-1)rho}` (the reciprocal of FLW eq (5.3)'s variance ratio `(1/n){1+(n-1)rho}`), not the general
    result. When an audit flags a formula, read the PDF before dismissing it.
    (c) **Beyond-FLW content must be flagged + cited** (or removed); do not present an instructor
    extension as chapter content (score test/MNAR/MI/IPW in Ch. 4; AR(1)/ACF in Ch. 2; partial-residual
    plots in Ch. 6).
    (d) **Match the book's method for the book's examples:** REML for reported coefficients (ML only for
    mean-structure LRTs), unstructured covariance where FLW uses it (Ch. 6 case studies), Wald CHISQ not
    `ddfm=kr` (Ch. 5 SAS).
    (e) **Three fidelity sources:** RAG textbook + chapter PDF + the authors' BIO 226 slides
    (`source_type='author_slides'`, indexed) for departures AND omissions.
21. **Notation must be standardized across decks AND faithful to FLW (the notation pass; the source of
    truth is `2026/NOTATION_REFERENCE.md`, verified against the FLW PDFs).** FLW is the tie-breaker.
    (a) **Marginal (total) covariance is $\Sigma_i$, NOT $V_i$.** FLW writes
    $\operatorname{Cov}(\mathbf{Y}_i\mid\mathbf{X}_i)=\Sigma_i(\theta)$ (eq 4.2),
    $\operatorname{Cov}(\mathbf{Y}_i)=\Sigma_i$ (Ch. 7), and the LME decomposition
    $\Sigma_i = \mathbf{Z}_i G \mathbf{Z}_i^\top + R_i$ (Ch. 8). $\Sigma_i$ is canonical (no declaration
    needed); the deck may drop the subscript and write $\Sigma$. The old course $V_i$ for this is retired.
    (b) **Random-effects covariance is $G$, NOT $D$;** residual within-subject covariance is $R_i$. FLW
    Ch. 8 names "the covariance matrix, $G$" with elements $g_{jk}$ (Ch. 14/22 use $G$ for GLMM/multilevel).
    (c) **$V_i$ is reserved for the GEE *working* covariance (Ch. 12-13 ONLY):**
    $V_i = \mathbf{A}_i^{1/2}\operatorname{Corr}(\mathbf{Y}_i)\mathbf{A}_i^{1/2}$, a different object from
    $\Sigma_i$; in GEE, $\mathbf{D}_i = \partial\boldsymbol\mu_i/\partial\boldsymbol\beta$ (a derivative).
    Never use $V_i$ for the Gaussian/LME covariance, nor $\Sigma_i$ for the GEE working covariance.
    (d) **Never collide reserved letters.** For the SD-correlation split of a covariance write
    $\Sigma_i = \mathbf{S}\,\mathbf{C}\,\mathbf{S}$ ($\mathbf{S}$ = SD diagonal, $\mathbf{C}$ = correlation),
    NOT $\mathbf{D}\,\mathbf{R}\,\mathbf{D}$ (L05 shipped with the colliding form; a disambiguation footnote
    is not enough, rename the symbols).
    (e) **These problems live in code/figures/tables/captions too, not just prose.** Audit echoed R chunks
    (a random-effects covariance built as `D <- matrix(...)` and a residual variance named `Sigma <- ...`
    both collide; use `G` and `sigma2`), plot titles/labels/legends, `fig-cap`/`tbl-cap`, and markdown
    table cells. Lints: `grep -nP '\\Sigma(?!_)'` (bare $\Sigma$ now OK, it is canonical);
    `grep -nE 'N\(0, ?D\)|\$D\$|Z_i D|\\mathbf\{Z\}_i D'` (random-effects $D$ -> $G$);
    `grep -nE '\\mathbf\{V\}_i|\$V_i'` outside L12/L13 (Gaussian $V_i$ -> $\Sigma_i$);
    `grep -nE 'Sigma *= *D|D *<- *matrix|Sigma *<- *[0-9(]'` (covariance symbols in code).
    (f) **A notation ruling and the decks must change in the SAME commit.** When you change a notation
    rule, edit `NOTATION_REFERENCE.md` + both `_notation_box*.qmd` partials + every affected deck
    (prose AND code/figures/tables/captions) + this file's tables together, and record it in
    `CONSISTENCY_LEDGER.md`. A ruling that contradicts a shipped deck in its own commit is the failure mode.
22. **NEVER fabricate a diagnostic/result with `rnorm()`/`sample()`/a hardcoded vector and plot or report
    it as a computed quantity (the B4 L10 lesson).** L10 shipped a "cluster influence" slide that set up a
    real leave-one-cluster-out loop, then overwrote it with `delta <- abs(rnorm(100, 0.05, 0.03))` behind a
    "pre-computed for speed" comment and plotted random noise as a diagnostic. A clean render hides this.
    Rule: a "pre-computed for speed" stand-in MUST be the real (possibly subsetted) computation, never a
    random draw; simulation is allowed ONLY to illustrate a labeled teaching point, never as a result.
    Lint every deck: `grep -nE 'rnorm|sample\(|runif' <deck>` and confirm each hit is labeled illustrative
    DGP, not a fabricated diagnostic/estimate. (Enforced as a POST_LECTURE_REVIEW gate.)
23. **Book-departure classes that a single-deck render/panel will NOT catch (the B4 fidelity-audit lessons;
    run the `POST_LECTURE_REVIEW.md` Dimension-A scan against the chapter PDF + RAG).**
    (a) **Caution-reversal (highest severity):** do not teach the OPPOSITE of an explicit FLW caution. L10
    taught BLUP/empirical-Bayes QQ plots to assess random-effects normality, which FLW p.273 explicitly
    cautions AGAINST (shrinkage understates RE variance). Maintain the running caution list in
    `CONSISTENCY_LEDGER.md` and check each deck against it.
    (b) **Core-method coverage:** the deck must CENTER the chapter's primary method. Before drafting, get
    the chapter outline and identify its defining equations/figures; verify they are present. L10 omitted
    FLW Ch.10's entire transformed-residual (Cholesky, eq 10.2) + Mahalanobis-distance (eq 10.3) machinery
    in favor of an adjacent-tradition substitute (marginal/conditional taxonomy, cluster-deletion, recursive
    CUSUM). "Adjacent-tradition substitute for the chapter's actual core method" is a recurring departure.
    (c) **Forward-/backward-chapter leakage:** content FLW explicitly defers must be flagged as a preview,
    not mis-attributed to the current chapter. L12 imported missing-data (Ch.17/18) material AND carried a
    concrete mis-citation ("FLW p. 528" on a Ch.12 deck; p.528 is in the missing-data chapters). Verify any
    inline FLW page citation falls within the deck's chapter page range.
    (d) **`nlme::resid()`/`residuals.lme()` default-level trap (precision standard):** the default is the
    INNERMOST level = CONDITIONAL within-group residuals ($Y-X\beta-Zb$); MARGINAL residuals require
    `level=0`. This is the nlme analog of the `re.form=NA` marginal-mean trap. Never state "resid() is
    marginal by default"; label the `level=` on every `resid()` call on an `lme`/`gls` fit.
24. **Every analysis-derived number and every data-derived verdict on a slide must MATCH what the chunk
    actually computes; verify by RUNNING, and prefer inline R over hardcoded values (the B4 L10/codex
    lesson).** A clean render and correct formulas are NOT enough: L10 shipped a variogram-contrast slide
    asserting "the random-intercept-only model drifts off 1" and an ACF slide saying "lag-1 is within the
    bands, no `corAR1` needed", but re-running the chunks gave both variograms hovering near 1 (no visible
    misfit contrast) and a normalized-residual lag-1 of about -0.47 (outside the band). The narratives were
    aspirational, not what the real (dental) data produced. Rules:
    (a) **Run the chunks and read the output before writing the interpretation.** Any stated number,
    pattern word ("rises", "flat", "drifts", "within bands"), or verdict ("adequate", "no `corAR1`
    needed", "X is needed") must be confirmed against the chunk's actual result on the actual dataset. A
    pattern the data does not show is a defect even if the code runs and the math is right.
    (b) **Do not hardcode a number that comes from an analysis; pull it from the fitted object via inline
    R** (e.g. `` `r round(exp(coef(fit))['trt'], 2)` ``, `` `r round(vario$value[1], 2)` ``) so it cannot
    drift from the code. Hardcoded ORs/RRs/variance-component values are a recurring drift source (L11
    originally hardcoded ORs/RRs; they were moved to inline R). Reserve hardcoded constants for fixed
    inputs (e.g. `set.seed(667)`, AR(1) $\rho=0.8$), never for estimates the deck itself computes.
    (c) **When a real dataset does not exhibit the teaching pattern, say so honestly or use a clearly
    labeled simulation to isolate the pattern** - never assert a contrast the data does not produce.
    Enforced as a `POST_LECTURE_REVIEW.md` gate ("narrative-vs-output verification") and a per-batch
    `SCALING_PLAN.md` step; the cheapest implementation is the codex/independent re-run of the chunks.
    (d) **The no-hardcoded-analysis-number rule applies to speaker `::: {.notes}` too,** not just visible
    slides: L10 shipped notes hardcoding `0.7-1.1`, `-0.47`, `-0.32` after the visible slide was already
    inline-R; codex flagged them. Either inline-R the value in the note or keep the note qualitative.
25. **Pandoc pipe-in-table trap: never put a literal `|` inside a code span in a Markdown pipe table (the
    B4 L10 lesson).** `nlme`/`lme4` formulas with grouping (`~ time | id`, `corAR1(form = ~ x | id)`,
    `random = ~ 1 + t | id`) are the common case. Escaping as `\|` does NOT work inside a code span: it
    renders a **literal backslash** (`~ x \| id`), so copy-paste gives invalid R. Decision-tree / "what to
    do" tables are where this bites. Fix: keep the pipe-bearing call OUT of the table cell (describe it,
    e.g. "a random slope grouped by `id`") and put the exact, correct call (`random = ~ 1 + age_c | id`) in
    a speaker note or a callout BELOW the table, where pipes render normally. Lint: `grep -nE '\\\|' <deck>`
    inside table rows. B5's GEE/GLMM decks (lots of `~ ... | id` formulas) will hit this repeatedly.
26. **After REBUILDING a deck, repoint other decks' "recall from L\<N\>" claims to the rebuilt content
    (extends pitfall 7).** The B4 L10 rebuild changed what L10 establishes (now transformed/Mahalanobis
    residuals, not per-observation leverage/Cook's D), which silently falsified L11's prereq slide
    ("leverage, Cook's distance ... introduced in L10"). The cross-lecture sweep caught it. When you
    rebuild a deck, grep the whole corpus for `L<that-number>` / "Lecture <N>" / "recall" pointers into it
    and reconcile each. Also: when a deck needs a NEW cross-deck extension symbol (e.g. the ordinal cutpoint
    $\kappa_k$ shared by L11 and L12), pre-register it in `NOTATION_REFERENCE.md` BEFORE authoring the decks
    that use it, so they do not diverge (L11 first used $\alpha_k$, L12 used $\theta_k$, until reconciled).
27. **Deck filename `_chNN` suffix tracks the FLW CHAPTER, not the course-slot lecture number (the B5 L15
    lesson); and renaming a deck means renaming ALL its siblings + fixing internal chapter labels.** The
    `_chNN` suffix is the FLW chapter the content teaches: L13->`_ch13`, L14->`_ch14`. L15 ("Lecture 15")
    teaches random-slope GLMMs, which are FLW **Ch.14** content (FLW's physical Ch.15 is PQL/MQL approximate
    methods), so the deck is `BIOS667_L15_GLMM_RandomSlopes_ch14.qmd` (lecture-number prefix L15 = course
    slot; chapter suffix ch14 = FLW chapter). When a course slot maps to a different FLW chapter than its
    number, (a) name/rename the `.qmd` AND every sibling together: `_note.md`, `_reference_audit.md`,
    `.html`, `_files/`; (b) fix the chapter label INSIDE the audit header/Deck line and the note
    header/body (the L15 note shipped a factually WRONG "Chapter 15 ... random-slope covariance" claim;
    random-slope covariance is Ch.14/Ch.8, FLW Ch.15 is PQL/MQL); (c) sync the Content Coverage Matrix +
    `LECTURE_TIMING_PLAN.md` + this file's timing-classification table; (d) keep the on-slide FLW-provenance
    note (title/footer/intro stating which FLW chapter the content comes from). **B6 is the high-risk
    batch:** the course L17/L18/L19 labels do NOT track FLW's physical chapters (FLW Ch.18 = Missing-Data/MI,
    Ch.19 = Smoothing), so decide each deck's FLW-chapter suffix and provenance note up front. **Git
    discipline for renames:** after `git mv` + editing the renamed files, a single `git add` that still
    lists the STALE old path aborts and stages NOTHING (the rename from `git mv` is already staged, so the
    commit silently records rename-only). ALWAYS run `git diff --cached --stat` and confirm the expected
    CONTENT hunks are staged (not rename-only, not empty) before `git commit`.

### Textbook Fidelity (Using the RAG System)

The `bios667-textbook` MCP server provides tools to query the Fitzmaurice textbook. **Always use these tools** when working on lectures to ensure accuracy:

| Tool | When to Use |
|------|-------------|
| `get_chapter_outline` | Start here - get the chapter's section structure to plan slide coverage |
| `search_textbook` | Find specific content, definitions, or explanations |
| `get_concept` | Get precise definitions with related concepts |
| `find_prerequisites` | Ensure earlier material was covered before introducing a topic |
| `find_related` | Add cross-references to other chapters |
| `get_examples` | Find worked examples from the textbook (dental, TLC, epilepsy, etc.) |

**Workflow for new/updated lectures:**
1. Call `get_chapter_outline(chapter=N)` to see full section structure
2. Compare outline to existing slides - identify gaps or extra content
3. Use `search_textbook` to retrieve accurate wording for key concepts
4. Use `find_related` to add "recall from Ch. X" or "we'll revisit in Ch. Y" callouts
5. Use `get_examples` to find appropriate worked examples from the book

### Course-Corpus RAG (Using the `bios667-corpus` System)

In addition to the textbook-only `bios667-textbook` server, the `bios667-corpus`
MCP server queries a **unified index of the entire course corpus** (lectures,
homework, handouts, slides, SAS/R code, datasets, and the FLW textbook) across
this repo and the level-up `BIOS667/` directory. Use it to keep materials in
sync with the textbook and to mine old materials when authoring new ones.

| Tool | When to Use |
|------|-------------|
| `search_all` | General semantic search across the whole corpus; filter by `source_type`, `chapter`, or `year` |
| `find_examples` | Mine old HW, SAS/R code, and handouts for worked examples on a topic (to adapt into new HW/slides) |
| `find_datasets` | Discover datasets by topic/variables, with the list of materials that have used each |
| `check_lecture_sync` | Compare a lecture (by chapter number, topic, or `.qmd` path) against the FLW textbook; surfaces coverage `gaps` and `possible_mismatches` |

**`source_type` values:** `textbook, lecture, hw, hw_solution, handout, quiz,
slides, author_slides, sas, rcode, data_card, syllabus`. (`author_slides` = the FLW
authors' BIO 226 slides, distinct from our `lecture` decks and the `slides` student decks.)

**Rebuilding the index** (the DB lives in `rag/data/`, gitignored, rebuildable):

```bash
cd rag
.venv/bin/bios667-index-corpus --plan      # dry-run preview (counts, no embedding)
.venv/bin/bios667-index-corpus             # incremental build (only changed files)
.venv/bin/bios667-index-corpus --rebuild   # full re-embed of the whole corpus
```

**Caveats:**
- `check_lecture_sync` is reliable for **Ch. 1–16**; the course resequences late
  topics (L18 Transition, L19 Advanced Missing), so the course's Ch. 17–19 labels
  (as used in the Content Coverage Matrix below) do **not** correspond to FLW's
  actual Ch. 17–19 (FLW Ch. 18 = Missing-Data/MI, Ch. 19 = Smoothing). Sync results
  for those chapters compare mismatched content. It surfaces candidates for review;
  it does not auto-judge.
- Sync `gaps` may include dense textbook formula/table PDF fragments (a
  chunk-granularity artifact), not true missing coverage.
- Scanned-PDF OCR is wired but inactive unless the `tesseract` binary is installed
  (it degrades gracefully: sparse text is kept, the file is still indexed).
- The legacy `textbook_chunks` collection is preserved as a backup; `bios667-corpus`
  is the unified collection (`rag/data/chroma`).

### YAML Header Standard

All lectures must use this YAML structure:

```yaml
---
title: "BIOS 667 — Lecture N: Topic (Ch. N)"
subtitle: "Fitzmaurice, Laird & Ware (2011) — Applied Longitudinal Data Analysis"
author: "Naim Rashid"
format:
  revealjs:
    theme: [default]
    footer: BIOS 667 · UNC Gillings — Lecture N (Ch.N)
    slide-number: true
    hash: true
    toc: false
    code-overflow: wrap
    code-line-numbers: false
    math: mathjax
    incremental: true
    embed-resources: true
    chalkboard: false
    css: "unc-gillings.css"
    scrollable: true
execute:
  warning: false
  message: false
---
```

### Slide Structure Conventions

**Opening slides (pick appropriate combination):**
- "Lecture Objectives" or "Today's Goals" — 3-5 bullet points
- "Roadmap" — numbered list of major sections (optional)
- "Motivation" — why this topic matters

**Slide density:**
- Slides should NOT be overwhelmed with text
- Capture key points only — easy to read at a glance
- One concept per slide when possible
- Use `---` for slide breaks
- Section headers with `##`, subsections with `###`
- Keep bullet points concise (one line each)
- Use `::: {style="font-size: 0.7em;"}` sparingly for dense technical content

**Illustrations are preferred over text:**
- Use R plots to visualize concepts (trajectories, residuals, covariance patterns)
- Include relevant figures/graphs from the textbook when appropriate
- Create diagrams and visual comparisons
- Code demos > verbal explanations for statistical methods

**Code blocks — separate code from output:**
- Key concepts should be illustrated with executed R code
- **Code on one slide, output on the next** using `#| output-location: slide`
- Use `#| echo: true` for teaching code, `#| echo: false` for setup
- Include brief comments explaining each step
- Show model specification clearly: `lmer(y ~ time + (1 | id), data=df)`

Example pattern:
```r
#| label: model-fit
#| echo: true
#| output-location: slide
library(lme4)
fit <- lmer(distance ~ age + (1 | Subject), data = Orthodont)
summary(fit)
```

**Math notation:**
- Display equations: `$$...$$` on own lines
- Inline math: `$...$`
- Use `\operatorname{}` for named functions (Var, Cov, Corr)
- Matrices: `\begin{pmatrix}...\end{pmatrix}`
- Subscripts for subject/time: $Y_{ij}$ (subject $i$, time $j$)

**Callouts:**
- `::: {.callout-note}` — definitions, key points, reading references
- `::: {.callout-warning}` — common mistakes, AI verification reminders
- `::: {.callout-tip}` — practical advice, shortcuts

**Cross-references:**
- "Recall from Chapter N..." when using prior material
- "We'll see in Chapter N..." for forward references
- Use `find_related` tool to identify these connections

### Notation Consistency

Maintain these conventions across all lectures:

| Symbol | Meaning |
|--------|---------|
| $Y_{ij}$ | Response for subject $i$ at occasion $j$ |
| $X_{ij}$ | Fixed-effect covariates |
| $Z_{ij}$ | Random-effect design |
| $\beta$ | Fixed-effect coefficients |
| $b_i$ | Random effects for subject $i$ ($b_i \sim N(0, G)$) |
| $G$ | Random-effects covariance matrix (FLW's letter; not $D$) |
| $R_i$ | Within-subject residual covariance |
| $\Sigma_i$ | Marginal (total) covariance of $Y_i$: $\Sigma_i = Z_i G Z_i^\top + R_i$ (FLW eq 4.2/Ch. 8) |
| $V_i$ | GEE working covariance (Ch. 12-13 only); NOT the Gaussian $\Sigma_i$ |
| $\varepsilon_{ij}$ | Residual error |

### Dataset References

Use consistent naming for textbook datasets:

| Dataset | Context | Chapters |
|---------|---------|----------|
| `dental` | Dental growth study | 5, 7, 8 |
| `tlc` | TLC lead exposure trial | 5, 6 |
| `epilepsy` | Seizure counts | 11, 13, 14 |
| `fev1` | Lung function | 6 |
| `rat` | Rat growth curves | 6, 8 |
| `muscatine` | Obesity study | 14 |

### Quality Checklist

Before finalizing any lecture, verify:

**Textbook fidelity:**
- [ ] Used `get_chapter_outline` to confirm all key sections addressed
- [ ] Used `search_textbook` for accurate technical definitions
- [ ] Checked `find_prerequisites` for assumed knowledge
- [ ] Added cross-references using `find_related`
- [ ] Ran `check_lecture_sync` (bios667-corpus) on new/updated lectures; reviewed `gaps`/`possible_mismatches` (reliable for Ch. 1–16; see caveats)

**Slide quality:**
- [ ] Slides are not text-heavy — key points only
- [ ] Key concepts illustrated with R code (code slide → output slide)
- [ ] Includes visualizations (R plots, book figures, diagrams)
- [ ] Notation consistent with table above and prior lectures

**Technical verification:**
- [ ] YAML header matches standard template
- [ ] All R chunks execute without error
- [ ] Math renders correctly in browser preview
- [ ] Callouts used appropriately (note/warning/tip)

### Common Patterns

**Lecture opening patterns:**
- "Today's goals" or "Lecture Objectives" — 3-5 bullet points
- "Roadmap" — numbered list of major sections for longer lectures
- "Retrieval — from Lecture N" — brief recap of prior material
- "Notation Reference" — table of symbols used in lecture
- "Key terminology" — definitions for lecture-specific terms

**Multi-part lectures:**
- Use `## Part I: Topic`, `## Part II: Topic` for long lectures
- Include a Roadmap slide showing all parts upfront
- Each part can have its own section header

**Introducing a new model:**
1. Motivation slide (why do we need this?)
2. Model specification (equations)
3. Interpretation slide (what do parameters mean?)
4. Estimation slide (ML/REML/GEE)
5. R code example
6. Worked example with real data

**Comparing approaches (common pattern):**
1. Translation table (e.g., "GEE vs GLMM: Translation Guide")
2. "When to choose X vs Y" decision slide
3. Same dataset analyzed both ways
4. Interpretation differences highlighted

**Decision frameworks:**
- Use ASCII diagrams for decision trees:
```
                Research Question
                       ↓
             What is the target?
                ↙          ↘
        Population?    Individual?
```
- Or use simple bullet-point decision trees

**Discussion prompts:**
- Use blockquote format: `> **Question:** ...`
- Place after concept introduction to encourage engagement
- Include in-class discussion cues

**Simulation-based teaching:**
- Simulate data to illustrate concepts (very common)
- Show how violations affect inference
- Compare correct vs incorrect model specifications
- Use `set.seed(667)` for reproducibility

**Worked examples:**
1. Data description (source, variables, research question)
2. Model specification (show formula)
3. R code with output
4. Interpretation of results
5. Model diagnostics (if applicable)

**Lecture closing patterns:**
- "Summary" or "Takeaways" slide
- "For Next Time" — reading assignment
- "Canonical resources" — links to book datasets, author slides

### Setup Patterns

**Package loading (two approaches):**

1. Simple library calls at start:
```r
#| label: setup
#| include: false
library(nlme)
library(ggplot2)
library(dplyr)
```

2. With missing package check (for robustness):
```r
required_pkgs <- c("dplyr", "ggplot2", "nlme")
missing_pkgs <- required_pkgs[!vapply(required_pkgs, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing_pkgs) > 0) {
  stop("Please install: ", paste(missing_pkgs, collapse = ", "))
}
```

**Data loading:**
- Check for local copy first, download if missing
- Use `data/` directory for datasets
- Reference textbook data source: `content.sph.harvard.edu/fitzmaur/ala2e/`

**Helper functions:**
- Define in setup chunk if used across multiple slides
- Use `safe_*` wrappers for error handling in demonstrations

### Summary Tables

Use tables to compare methods, assumptions, or interpretations:

```markdown
| Method | Pros | Cons |
|--------|------|------|
| **Unstructured** | Most flexible | Parameter-heavy |
| **CS** | Parsimonious | Often unrealistic |
| **AR(1)** | Captures decay | Stationary assumption |
```

Common comparison topics:
- Covariance structures (UN/CS/AR1)
- Test types (LRT/Wald/Score)
- Model families (Marginal/Mixed/Transition)
- Missing data mechanisms (MCAR/MAR/MNAR)

---

## Homework Guidelines

Homework assignments are created every 3 lectures to assess key concepts from both lectures and the textbook.

### Assignment Structure

**Coverage:** Each HW covers 3 consecutive lectures (e.g., HW1: L01-L03, HW2: L04-L06)

**Format:** 5 questions total, each with multiple sub-parts (a, b, c, ...)

**Difficulty progression:** Questions should increase in difficulty to enable score stratification:
1. **Q1 (Foundational):** Basic concepts, definitions, straightforward calculations
2. **Q2 (Application):** Apply methods to provided data or scenarios
3. **Q3 (Analysis):** Interpret output, compare models, justify choices
4. **Q4 (Synthesis):** Combine multiple concepts, handle edge cases
5. **Q5 (Challenge):** Complex scenarios, derive results, critique approaches

### Question Design

**Draw from multiple sources:**
- Lecture slides and examples
- Textbook sections and worked examples
- Real datasets from `data/` directory

**Sub-part structure:**
```
1. [Concept from L01] (15 points)
   a) Define X and explain its importance in longitudinal analysis. (3 pts)
   b) Given the following output, interpret the parameter estimate. (4 pts)
   c) What assumption is being made? How would you check it? (4 pts)
   d) Modify the R code to relax this assumption. (4 pts)
```

**Balance question types:**
- Conceptual understanding (definitions, assumptions, interpretations)
- Computational (hand calculations, formula application)
- Applied (R code, output interpretation)
- Critical thinking (model selection, diagnostics, limitations)

### Textbook Fidelity

When creating homework, use RAG tools to ensure alignment:
- `search_textbook` — find relevant problems and examples
- `get_examples` — identify worked examples to adapt
- `find_related` — connect concepts across chapters covered

### File Naming

`HW{N}.qmd` where N corresponds to the assignment number (HW1, HW2, ...)

### YAML Header for Homework

```yaml
---
title: "BIOS 667 — Homework N"
subtitle: "Fitzmaurice, Laird & Ware (2011) — Applied Longitudinal Data Analysis"
author: "Your Name (PID: XXXXXXXXX)"
date: today
format:
  html:
    embed-resources: true
    toc: true
execute:
  warning: false
  message: false
---
```

### Required Sections

**Instructions section (at top):**
- Collaboration/honor code policy
- AI use policy with disclosure requirements
- Submission format requirements
- Due date and late policy

**Setup chunk:**
```r
#| label: setup
#| include: false
library(nlme)
library(ggplot2)
library(dplyr)
# Seed based on student PID for reproducibility
set.seed(as.numeric(substr(Sys.getenv("PID", "667"), 1, 5)))
```

**Grading rubric:** Include point breakdown by category:
- Interpretation & Reasoning (conceptual understanding)
- Analysis & Setup (code correctness, model specification)
- Clarity & Presentation (writing quality, formatting)

**Task markers:** Use `CODE:` and `WRITE:` prefixes to clarify expected response type:
```
a) **CODE:** Fit a linear mixed model with random intercepts.
b) **WRITE:** Interpret the fixed effect for treatment in context.
```

**Peer review section:** For assignments with peer assessment:
- Clear rubric for peer evaluation
- Guidelines on constructive feedback
- Anonymization requirements

**Reminders section (at end):** Common pitfalls and formatting requirements:
- Knit document before submission
- Check that all code executes without errors
- Ensure figures are visible and properly labeled
- Format tables appropriately

### Creation Workflow

**Create solution key first, then derive student version:**

1. **Create `HW{N}_solution.qmd`** (the grader's solution key):
   - Complete R code for all problems
   - Full written answers and interpretations
   - Point breakdowns per sub-part
   - Common mistakes to watch for
   - Partial credit guidelines
   - Grading rubric notes

2. **Derive `HW{N}.qmd`** (student-facing version):
   - Copy from solution file
   - Remove all R code from answer chunks (keep setup chunks)
   - Remove all written answers
   - Replace with placeholder prompts (e.g., "Your code here", "Your interpretation here")
   - Keep question text, point values, and CODE:/WRITE: markers

This workflow ensures:
- Solution key is always complete and tested
- Student version matches solution structure exactly
- Graders have authoritative reference
- No divergence between question and expected answer

### Path Handling for Homework

**NEVER use absolute paths in student-facing files:**

```r
# WRONG - will fail for students
data <- read.table("/home/instructor/data/dental.txt")

# CORRECT - relative path with download fallback
data_url <- "https://content.sph.harvard.edu/fitzmaur/ala2e/dental.txt"
data_file <- "data/dental.txt"
if (!file.exists(data_file)) {
  dir.create("data", showWarnings = FALSE)
  download.file(data_url, data_file)
}
data <- read.table(data_file, header = TRUE)
```

### Homework Quality Checklist

Before creating student versions, verify the solution key:
- [ ] All code chunks execute without error
- [ ] Numerical answers are correct and match code output
- [ ] Formulas use consistent notation with lectures
- [ ] Grading notes specify expected answer format
- [ ] Partial credit guidelines are specific, not vague
- [ ] Due dates are filled in (not "[DATE]" placeholder)
- [ ] Point allocations sum correctly

---

## Quiz Guidelines

Quizzes serve two purposes:
1. Concept consolidation and retrieval practice
2. Attendance verification (in-class administration)

### Quiz Structure

- **Questions**: 5 per quiz
- **Format**: Multiple choice (4 options) or single numeric answer
- **Time**: 5-7 minutes in-class
- **Difficulty**: Quick retrieval, not deep analysis
- **Coverage**: Each quiz covers 3 lectures

### Question Writing Standards

**Multiple Choice Questions:**
- One clearly correct answer
- Three plausible distractors representing common misconceptions
- No "all of the above" or "none of the above"
- Avoid negative stems ("Which is NOT...")

**Numeric Questions:**
- Provide all necessary formulas in the question
- Specify precision/rounding requirements
- Include units if applicable
- Avoid memorization-dependent calculations

### Answer Key Requirements

Include collapsible answer key with:
- Correct answer for each question
- Brief explanation (1-2 sentences)
- Reference to relevant lecture/section

### Common Quiz Issues to Avoid

1. Questions that reference non-existent lectures
2. Calculation questions without provided formulas
3. Ambiguous questions with multiple correct answers
4. Questions that test trivia rather than understanding
5. Trick questions or deliberately misleading distractors

---

## Statistical Precision Standards

When creating or updating course materials, maintain rigorous statistical accuracy.

### Terminology Precision

- Use **"invalid inference"** or **"incorrect standard errors"** when referring to standard errors under correlation misspecification — point estimates remain unbiased if mean model is correct (FLW pp. 43-44)
- Distinguish **"correlation matrix"** from **"covariance matrix"** — do not use interchangeably
- Use **"empirical Bayes predictors"** or **"conditional modes"** for GLMMs (FLW uses "empirical BLUP" as convention)
- Clarify **"random effects"** context: biostatistics (variance components) vs. econometrics (group-specific intercepts)

### Formula Verification Checklist

Before including any formula, verify:
- [ ] Constants are correct (e.g., Zeger attenuation: constant c₂ = 16√3/(15π) ≈ 0.588; the multiplier on σ_b² under the root is c₂² ≈ 0.346 — these are the same constant, not alternatives)
- [ ] Matrix dimensions are stated
- [ ] Subscript indices are consistent (i for subject, j for time, k for state)
- [ ] Distribution assumptions are explicit
- [ ] Boundary conditions are noted for variance component tests

### Common Errors to Avoid

1. **Marginal predictions in GLMMs**: `re.form = NA` gives predictions at $b_i = 0$, NOT true marginal means. True marginal predictions require Monte Carlo integration:
   ```r
   # re.form = NA gives E[Y | b_i = 0], NOT E[Y]
   # For true marginal means, integrate over random effects distribution
   ```

2. **Satterthwaite df**: Do not present a simplified formula — reference `lmerTest` implementation

3. **Hausman test**: Failing to reject does not prove RE consistency — only insufficient evidence

4. **GEE validity**: Standard GEE requires MCAR for valid inference; IPW-GEE extends to MAR with correctly specified dropout model (FLW p. 528)

5. **AR(1) in nlme**: Uses range parameter, not decay rate directly

6. **Mundlak approach**: Include means of X covariates, NOT Y (including Y means creates endogeneity)

7. **Relative efficiency (ANCOVA vs. change scores)**: $2/(1+\rho)$ is specifically the **single-follow-up** case (one baseline + one post-baseline occasion, $n = 2$). The general FLW result (eq. 5.3) is **$n$-dependent**: under compound symmetry the efficiency of the change-score summary *relative to* ANCOVA is $\tfrac{1}{n}\{1+(n-1)\rho\}$ (FLW's convention; $<1$ means ANCOVA is more efficient), so **ANCOVA is $n/\{1+(n-1)\rho\}$ times as efficient**, which at $n=2$ is $2/(1+\rho)$. ANCOVA's advantage is therefore **decreasing in $\rho$** (greatest when $\rho$ is low: $\to n\times$ as $\rho\to0$, e.g. $\to 2\times$ at $n=2$; vanishes as $\rho\to1$) **and grows with the number of occasions $n$**. Cite FLW eq. (5.3) and state the single-follow-up special case explicitly rather than presenting $2/(1+\rho)$ as the general result. Do not confuse this with ANCOVA vs. *post-only* analysis ($1/(1-\rho^2)$), whose advantage *does* increase with $\rho$. **Mechanism:** change scores are less efficient because they force the baseline coefficient to be exactly 1, whereas ANCOVA estimates the optimal coefficient (regression to the mean); the inefficiency is NOT due to "measurement error" or "using baseline twice", and lecture explanations must give the optimal-coefficient/regression-to-the-mean argument, not a measurement-error story

### Textbook Alignment Verification

Before finalizing any statistical content, cross-reference with FLW (2011):

1. **Attenuation formula**: The logistic random-intercept attenuation is β_marg ≈ β_cond / √(1 + c₂²·σ_b²) with the single constant c₂ = 16√3/(15π) ≈ 0.588 (FLW p. 477). **0.346 is NOT an alternative constant**: it is c₂² ≈ 0.346 (= (1/1.7)², the probit-matching teaching form), the multiplier ON σ_b² under the root. Write c₂ for the constant and c₂² ≈ 0.346 for the multiplier; never present 0.346 and 0.588 as competing constants. L14 (Ch.14 deck) states this canonically; match it. **This closed-form factor is a LOGISTIC-link result** (FLW p. 477): always label it "logistic" when a Poisson/log-link deck (L13/L15) previews or recalls it. The Poisson/log-link Jensen fan-out is real (E[exp(b₀+b₁t)] = exp(σ₀²/2 + σ₀₁t + σ₁²t²/2) adds THREE terms to the marginal log-mean: an intercept shift σ₀²/2, a linear slope modification σ₀₁t via the intercept-slope covariance, and a time-quadratic term σ₁²t²/2) but there is NO single slope-attenuation constant, and Poisson random SLOPES are not attenuated this way.
2. **Standard error language**: Use "invalid inference" not "biased standard errors" (FLW pp. 43-44)
3. **Marginal predictions**: Never claim `re.form = NA` gives marginal means; requires integration (FLW p. 477)
4. **GEE/MAR**: Distinguish standard GEE (MCAR) from IPW-GEE (MAR) (FLW p. 528)
5. **Random effect predictions**: Use "empirical BLUP" or "predicted random effects" (FLW convention)

---

## Notation Consistency (Expanded)

| Symbol | Meaning | Notes |
|--------|---------|-------|
| $Y_{ij}$ | Response for subject $i$ at occasion $j$ | Always use subscript $i$ for subject, $j$ for time |
| $\mathbf{Y}_i$ | Response vector for subject $i$ | Bold for vectors |
| $X_{ij}$ | Fixed-effect covariates | Row vector, dimension $1 \times p$ |
| $\mathbf{X}_i$ | Fixed-effect design matrix | Dimension $n_i \times p$ |
| $Z_{ij}$ | Random-effect design | Row vector |
| $\mathbf{Z}_i$ | Random-effect design matrix | Dimension $n_i \times q$ |
| $\beta$ or $\boldsymbol{\beta}$ | Fixed-effect coefficients | Bold when emphasizing vector nature |
| $b_i$ or $\mathbf{b}_i$ | Random effects for subject $i$ | $b_i \sim N(0, G)$ |
| $G$ | Random-effects covariance matrix | FLW's letter (Ch. 8, elements $g_{jk}$); the course no longer uses $D$ |
| $R_i$ | Within-subject residual covariance for subject $i$ | $\varepsilon_i \sim N(0, R_i)$ |
| $\Sigma_i$ | Marginal (total) covariance of $\mathbf{Y}_i$ | $\Sigma_i = Z_i G Z_i^\top + R_i$ (FLW eq 4.2, Ch. 7-8) |
| $V_i$ | GEE working covariance (Ch. 12-13 ONLY) | $V_i = A_i^{1/2}\operatorname{Corr}(Y_i)A_i^{1/2}$; a working assumption, NOT the Gaussian $\Sigma_i$ |
| $\varepsilon_{ij}$ | Residual error | $\varepsilon_i \sim N(0, R_i)$ |
| $\phi$ | Dispersion parameter (GLMs) | Not to be confused with AR correlation |
| $\rho$ | Correlation parameter | AR(1) or exchangeable |
| $\alpha$ | Working correlation parameters (GEE) | Vector for non-exchangeable |
| $\pi_{ij}$ | Probability (binary outcomes) | Subject $i$, time $j$ |

### Subscript Conventions

- $i$: Subject index ($i = 1, \ldots, N$; $N$ = number of subjects, per FLW Section 3.2)
- $j$: Time/occasion index ($j = 1, \ldots, n_i$; $n$ = common number of occasions when balanced)
- $k$: State index for transition models
- $g$: Group index for multi-group comparisons ($g = 1, \ldots, G$)

Keep notation matching FLW across all lectures; use $N$ for the subject count and $n$/$n_i$ for occasions (do not use $n$ for the subject count).

---

## Lecture Quality Assurance

### Pre-Deployment Review Checklist

**Statistical Content:**
- [ ] All formulas verified against textbook
- [ ] Terminology matches standard usage (see Statistical Precision Standards)
- [ ] No conflicting definitions across lectures
- [ ] Boundary cases and assumptions clearly stated

**Code Quality:**
- [ ] All chunks execute without error
- [ ] Object names consistent throughout
- [ ] Output interpretation matches actual output
- [ ] Required packages listed in setup chunk

**Pedagogical Flow:**
- [ ] Learning objectives are measurable
- [ ] Roadmap reflects actual slide content
- [ ] Difficulty progresses appropriately
- [ ] Key points reinforced with examples

**Cross-References:**
- [ ] Prior lecture references are accurate
- [ ] Forward references use correct lecture numbers
- [ ] Dataset references match available data files

**Common Lecture Errors to Check:**
1. Prediction code: Verify `re.form = NA` is not misrepresented as "marginal"
2. Test statistics: Verify LRT/Wald/Score test contexts
3. Boundary tests: Include caveat about mixture distributions
4. Covariance structures: Verify formula matches verbal description
5. GEE validity: Clearly state MCAR requirement vs. IPW-GEE for MAR

---

## Content Coverage Matrix

Maintain a tracking matrix to ensure all textbook content is covered:

| Chapter | Lecture(s) | Key Topics | HW Coverage | Quiz Coverage |
|---------|------------|------------|-------------|---------------|
| Ch. 1 | L01 | Intro, study designs, motivation | HW1 | Quiz1 |
| Ch. 2 | L02 | Data structures, notation, sources of correlation | HW1 | Quiz1 |
| Ch. 3 | L03 | Linear models overview | HW1 | Quiz1 |
| Ch. 4 | L04 | Estimation, inference, missing data | HW2 | Quiz2 |
| Ch. 5 | L05 | Response profiles, hypotheses | HW2 | Quiz2 |
| Ch. 6 | L06 | Parametric curves, splines | HW2 | Quiz2 |
| Ch. 7 | L07 | Covariance pattern models | HW3 | Quiz3 |
| Ch. 8 | L08 | Linear mixed effects | HW3 | Quiz3 |
| Ch. 9 | L09 | FE vs RE, Hausman test | HW3 | Quiz3 |
| Ch. 10 | L10 | Residual analyses and diagnostics (residuals, transformed/aggregating residuals, semi-variogram, case study) | HW4 | Quiz4 |
| Ch. 11 | L11 | GLM review | HW4 | Quiz4 |
| Ch. 12 | L12 | Marginal models intro | HW4 | Quiz4 |
| Ch. 13 | L13 | GEE extensions | HW4 | Quiz4 |
| Ch. 14 | L14 | GLMMs | HW5 | Quiz5 |
| Ch. 14 | L15 | GLMM random slopes (random slopes are FLW Ch.14; deck relabeled Ch.15→Ch.14) | HW5 | Quiz5 |
| Ch. 15 (PQL/MQL) | (L15 enrichment) | FLW Ch.15 = Approximate Methods (PQL/MQL); NOT a standalone lecture — touched in L15 as flagged enrichment, AGQ (Ch.14) is the taught benchmark | — | — |
| Ch. 16 | L16 | Contrasting models | HW5 | Quiz5 |
| Ch. 17 | L17 | Missing data and dropout: overview, MCAR/MAR/MNAR, dropout patterns | HW6 | Quiz6 |
| Ch. 18 | L18 | Missing data and dropout: multiple imputation, weighting/IPW, pattern-mixture/selection (B6 reorder 2026-06-19: was L19) | HW6 | Quiz6 |
| (instructor topic; FLW 1st-ed Ch.10) | L19 | Transition (Markov) models - NOT a FLW 2nd-ed chapter (2nd-ed Ch.19 = Smoothing); flagged instructor extension (B6 reorder: was L18) | HW6 | Quiz6 |
| Ch. 19 (Smoothing) | (not taught) | FLW Ch.19 = Smoothing Longitudinal Data / Semiparametric Regression; not in the course | - | - |

### Gap Identification

After creating materials, verify:
- [ ] No chapter has zero coverage in homework
- [ ] No lecture's key concepts are missing from corresponding quiz
- [ ] Major concepts have both conceptual AND applied assessment

---

## Student-Centered Pedagogy Guidelines

Based on student feedback, these principles improve learning outcomes across all materials.

### Visual Learning First

**Build intuition before introducing formulas:**
- Show a visualization demonstrating the concept BEFORE the mathematical notation
- Use spaghetti plots, correlation heatmaps, and side-by-side comparisons
- Include "So what?" callouts after visualizations explaining implications
- Color-code groups consistently (e.g., treatment = blue, control = gray)

**Annotate diagnostic plots:**
- Students need to know what "good" vs "problematic" patterns look like
- Add interpretation guidelines: "Flat ACF = good; decaying = need AR(1)"
- Show annotated examples of each pattern type
- Include reference lines and explain what they mean

### Complete and Runnable Code

**Never leave code incomplete:**
- All code examples must execute without errors
- Avoid `eval: false` without providing a working alternative
- If computation is expensive, show simplified version that runs
- Complete all "advanced" implementations (Monte Carlo integration, selection models)

**Code organization:**
- Separate code from output using `#| output-location: slide`
- Add inline comments explaining each step
- Keep chunks short; break long analyses into multiple chunks
- Use consistent object naming within each lecture

### Interpretation Walkthroughs

**Students understand methods but struggle with conclusions:**
- After every model output, provide interpretation in plain language
- Show how to report results in a clinical/scientific context
- Include "What would you conclude?" prompts
- Demonstrate both statistical and substantive significance

**Annotate model output:**
- Walk through key output tables line by line
- Explain what each number means and whether it's "good"
- Show how to extract specific quantities for reporting
- Connect output to the research question

### Check Your Understanding Sections

**Embed quick checks throughout lectures:**
- Add 2-3 "Quick Check" questions after major sections (not just at end)
- Include answers in collapsible sections
- Mix conceptual and calculation questions
- Examples: "What would happen if we ignored correlation here?"

**Format:**
```markdown
::: {.callout-note collapse="true"}
## Quick Check

1. If ρ = 0.8, what is the relative efficiency of ANCOVA vs. change scores?
2. Why does ignoring correlation typically underestimate standard errors?

**Answers:** [provide brief answers]
:::
```

### Common Mistakes and Gotchas

**Explicitly warn students about common errors:**
- Add a "Common Mistakes" or "Gotchas" slide to each lecture
- Include debugging tips for common error messages
- Show what happens when assumptions are violated
- Reference these warnings in homework assignments

**Common mistakes to highlight:**
- Using ML instead of REML for LRT of variance components
- Forgetting to recreate spline basis in newdata for predictions
- Misinterpreting `re.form = NA` as marginal predictions
- Confusing Hausman test "fail to reject" with "RE is correct"
- Using wrong correlation structure without checking fit

### Recipe Cards and Cheat Sheets

**Provide actionable summaries:**
- End complex lectures with a "Recipe Card" summarizing the workflow
- Include exact R code patterns students can adapt
- Create "When to Use Which" decision tables
- Provide SAS-to-R translation tables where relevant

**Recipe card format:**
```markdown
## Recipe: Fitting a Random Slopes Model

1. Center time at meaningful value (e.g., baseline)
2. Fit: `lme(y ~ time_c * group, random = ~ time_c | id, data = df)`
3. Check: RE correlation, residual plots, RE QQ plots
4. Compare to RI model using AIC or LRT (boundary-aware)
5. Report: Fixed effects with 95% CI, variance components
```

### Terminology Consistency

**Use consistent vocabulary across all materials:**
- Define terms at first use and use consistently thereafter
- When different fields use different terms (econometrics vs biostatistics), provide explicit translation
- Create a terminology reconciliation table when introducing conflicting conventions

**Example reconciliation:**
```markdown
| Biostatistics Term | Econometrics Term | Meaning |
|-------------------|-------------------|---------|
| Random effects model | — | Model with subject-specific random intercepts/slopes |
| — | Random effects (RE) | Swamy-Arora estimator assuming no endogeneity |
| — | Fixed effects (FE) | Within-subject demeaned estimator |
```

### Scaffolding for Complex Problems

**Break multi-step problems into manageable parts:**
- For simulations: provide pseudocode or step-by-step outline
- For diagnostics: provide starter code for loops
- For novel procedures: break into numbered sub-parts with hints
- Increase scaffolding for later, harder homework

**Scaffolding hierarchy:**
1. Q1-Q2: Minimal scaffolding (foundational)
2. Q3-Q4: Moderate scaffolding (hints, partial code)
3. Q5: Structured scaffolding (pseudocode, sub-parts)

### Connection to Prior Material

**Build explicit bridges between lectures:**
- Start lectures with "Recall from Lecture N..." connecting to prior content
- Use "We'll see in Lecture N..." for forward references
- Maintain running examples across multiple lectures (e.g., dental, epilepsy)
- Show how new methods relate to simpler approaches already learned

**Bridge patterns:**
```markdown
::: {.callout-note}
## Connection to Chapter N
In Lecture N, we learned [concept]. Today we extend this by [new concept].
The key difference is [distinction].
:::
```

### Decision Guides and Flowcharts

**Students value "when to choose X vs Y" guidance:**
- Provide decision tables for method selection
- Include ASCII or visual flowcharts for complex decisions
- State recommendations clearly ("Prefer X when...")
- Acknowledge that judgment is required, but give starting points

**Decision guide format:**
| Scenario | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| Few time points, balanced | Response profiles | Simple, interpretable |
| Many time points, continuous | Parametric curves | Efficiency, smoothness |
| Interest in individual trajectories | Mixed effects | Subject-specific predictions |

### Worked Examples with Full Interpretation

**Provide complete analysis walkthroughs:**
- From data description to final conclusion
- Include model selection rationale
- Show both statistical output AND written interpretation
- Demonstrate how to handle unexpected results

**Worked example structure:**
1. Research question and data description
2. Exploratory visualization
3. Model specification with justification
4. Model fitting and output
5. Diagnostic checks
6. Interpretation in context
7. Limitations and next steps

### Quiz Question Design

**Test understanding, not memorization:**
- Focus on application and interpretation
- Provide formulas when calculation is required
- Make distractors represent common misconceptions
- Avoid trick questions or gotchas
- State calculator/formula sheet policy clearly

**Question improvement checklist:**
- [ ] Tests conceptual understanding, not recall
- [ ] Has one clearly correct answer
- [ ] Distractors are plausible but distinguishably wrong
- [ ] Question stem is unambiguous
- [ ] Required information is provided (formulas, data)

---

## Lecture Timing Assessment

The 2026 lectures vary significantly in length. This assessment helps with class scheduling.

### Timing Methodology

- Technical biostatistics content with code: ~2-3 minutes per slide
- 75-minute class period: optimal for ~25-40 slides
- Lectures are NOT split; longer lectures fill 2 classes

### Lecture Classification by Duration

| Lecture | Slides | Est. Time | Classes | Notes |
|---------|--------|-----------|---------|-------|
| **L01** | 17 | 34-51 min | **1** | Ch.1 intro (split from old L01+2) |
| **L02** | 24 | 48-72 min | **1** | Ch.2 basic concepts (split from old L01+2) |
| **L03** | 52 | 104-156 min | 1.5-2 | Could fill 2 leisurely |
| **L04** | 68 | 136-204 min | **2** | Estimation/inference |
| **L05** | 75 | 150-225 min | **2** | Response profiles |
| **L06** | 52 | 104-156 min | 1.5-2 | Parametric curves |
| **L07** | 73 | 146-219 min | **2** | Covariance structures |
| **L08** | 72 | 144-216 min | **2** | LME |
| **L09** | 31 | 62-93 min | **1** | FE vs RE (rebalanced FLW-primary; econometrics as supplement) |
| **L10** | ~50 (rendered) | 100-150 min | **2** | Diagnostics (B4 rebuild: transformed residuals + Mahalanobis + dental Case Study) |
| **L11** | ~110 (rendered) | 200-300 min | **3** | GLMs (dense; B4: 2 real case studies + beyond-FLW flags + SAS + scaffolding) |
| **L12** | ~48 (rendered) | 96-144 min | **1.5** | Marginal intro (B4: epilepsy GEE Case Study added) |
| **L13** | 76 | 152-228 min | **2** | GEE extensions |
| **L14** | 82 | 164-246 min | **2** | GLMMs (dense) |
| **L15** | 77 | 154-231 min | **2** | GLMM random slopes (FLW Ch.14; course slot "Lecture 15") |
| **L16** | 83 | 166-249 min | **2** | Contrasting models (dense) |
| **L17** | 128 | 256-384 min | **3** | Missing data overview (FLW Ch.17; comprehensive) |
| **L18** | 83 | 166-249 min | **2** | Missing data: MI/weighting/pattern-mixture (FLW Ch.18; B6 reorder, was L19) |
| **L19** | 68 | 136-204 min | **2** | Transition (Markov) models (instructor topic, FLW 1st-ed Ch.10; B6 reorder, was L18) |

### Summary by Class Count

**Single class (1):** L01 (17), L02 (24)

**Flexible (1-2):** L03, L09 (after B4: L12 ~1.5 periods, L10 a firm 2)

**Two classes (2):** L04-L08, L13-L16, L18-L19 (67-83 slides)

**Three classes (3):** L11 (~110 rendered slides after the B4 rebuild), L17 (128 slides, comprehensive missing data)

### Scheduling Recommendations

- **Dense 2-class lectures** (L14, L16, L19): Build in discussion time or exercises (L11 is now ~3 classes after the B4 rebuild)
- **L17 (3 classes)**: Comprehensive missing data coverage; could also introduce a class break for questions
- **Flexible lectures** (L03, L09): Can be compressed to 1 class if time-pressed, or expanded with discussion (L10 is now a firm 2 after the B4 rebuild)
- **Total estimate**: ~34-37 class periods for all 19 lectures (B4 added ~2: L11 2->3, L10 1.5->2, L12 1->1.5)

### When Editing Lectures

If modifying lecture content:
- Adding >10 slides to a 1-class lecture may require 2 classes
- Removing slides from 2-class lecture doesn't automatically make it 1-class (content density matters)
- Consider `incremental: false` for rushed sections to speed delivery
