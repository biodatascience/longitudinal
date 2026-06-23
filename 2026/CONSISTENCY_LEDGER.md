# Cross-Lecture Consistency Ledger

The persistent record of cross-lecture decisions for the 2026 reference decks. Every batch must conform
to the entries here; the cross-lecture sweep (`2026/workflows/cross_lecture_consistency.mjs`) reads this
file and proposes additions. This is where the per-lecture consistency agent's "global obligations" are
written down so decisions persist across batches and sessions. See `2026/SCALING_PLAN.md` for the
process. Append decisions with the batch that made them; do not relitigate prior entries without noting
the change.

## Notation

- Notation is rendered via a shared partial, never a hand-pasted table: the full
  `{{< include _notation_box.qmd >}}` for methods decks, or the lite `{{< include _notation_box_intro.qmd >}}`
  for intro/overview decks (see the [B1] rule below). Master is `2026/NOTATION_REFERENCE.md`.
- **No dashes in ranges:** the no-em-dash house rule also bans the en-dash (U+2013); write chapter/page
  ranges with a hyphen ("Ch. 7-8", "pp. 43-44"). [B1]
- Reserved symbols (no collision): $\mathbf{X}_i$ / $\boldsymbol\beta$ = fixed-effect design and
  coefficients; $\mathbf{Z}_i$ / $\mathbf{b}_i$ = random-effect design and random effects ONLY. A fixed
  covariate is never written as $z_{ij}$. Bold = vector/matrix; plain = scalar/index.
- Lecture-specific symbols go on a small slide AFTER the include, never by editing the shared partial.
- **Intro/overview decks use the LITE include** `{{< include _notation_box_intro.qmd >}}` (basic symbols
  only) until random effects and GEE are introduced; methods decks (L08+) use the full `_notation_box.qmd`. [B1]
- **Covariate orientation:** the per-occasion covariate is the row vector $X_{ij}$ ($1 \times p$); write the
  mean model as $X_{ij}\beta$ (or $\mathbf{X}_i\boldsymbol\beta$), NOT $\boldsymbol\beta^\top\mathbf{x}_{ij}$.
  (L08's equations were written the column way and are being reconciled.) [B1]
- **Error term:** always $\varepsilon$ ($\varepsilon_{ij}$, $\boldsymbol\varepsilon_i$), never $e_i$. [B1]
- **Marginal covariance is $\Sigma_i$ (FLW's letter), NOT $V_i$ [superseded the B1 $V_i$ ruling on
  2026-06-19].** $\Sigma_i = \operatorname{Cov}(\mathbf{Y}_i)$; the decomposition
  $\Sigma_i = \mathbf{Z}_i G \mathbf{Z}_i^\top + R_i$ applies once random effects are introduced (Ch. 8+).
  See the FLW-symbol ruling below.
- **Graduated tiers:** intro/overview decks have a reduced bar (Case Study / SAS slide / period dividers
  optional when conceptual or single-period); see `REFERENCE_DECK_SPEC.md` "Deck tiers". [B1]
- **Book-first (FLW is the tie-breaker):** keep notation as consistent with FLW as possible across all
  lectures; when a course habit and the book differ, follow the book. Confirmed by PI 2026-06-18. [B2]
- **Subject/occasion counts follow FLW (Section 3.2):** $N$ = number of subjects ($i = 1,\dots,N$),
  $n_i$ = occasions for subject $i$, $n$ = the common number of occasions when balanced. The course
  previously used $n$ = subjects; this was flipped course-wide to FLW. Edited: `NOTATION_REFERENCE.md`,
  both partials' index lines, project `CLAUDE.md` subscript conventions, L02 (`i=1..N`), L03 (stacked
  model / block-diagonal $\dots,\mathbf{V}_N$). L12/L14 already used $N$; L05 uses $N$ subjects / $n$
  occasions as the balanced response-profile case (no longer framed as an "override"). NOTE (low,
  for L04 audit): L04's REML/ML variance cells use $n$, $n-p$ generically for the OLS sample size;
  clarify or leave as a standalone estimator template. [B2]
- **FLW-symbol ruling [2026-06-19, supersedes the earlier "$V_i$ / pick $D$ or $G$" latitude; PI directive
  "100% fidelity to the book, single source of truth"].** Verified against the FLW (2011) PDFs
  (Ch. 4 eq (4.2), Ch. 7, Ch. 8, Ch. 13); FLW is the tie-breaker. Source of truth = `NOTATION_REFERENCE.md`.
  - **Marginal (total) covariance of $\mathbf{Y}_i$ is $\Sigma_i$, NOT $V_i$.** FLW:
    $\operatorname{Cov}(\mathbf{Y}_i\mid\mathbf{X}_i)=\Sigma_i(\theta)$ (eq 4.2),
    $\operatorname{Cov}(\mathbf{Y}_i)=\Sigma_i$ (Ch. 7), $\Sigma_i=\mathbf{Z}_i G\mathbf{Z}_i^\top+R_i$ (Ch. 8).
    $\Sigma_i$ is canonical with NO declaration needed; bare $\Sigma$ (subscript dropped) is fine. The old
    course $V_i$ for this object is RETIRED.
  - **Random-effects covariance is $G$, NOT $D$** (FLW Ch. 8 "the covariance matrix, $G$", elements
    $g_{jk}$; Ch. 14/22 use $G$). Residual within-subject covariance is always $R_i$.
  - **$V_i$ is reserved for the GEE *working* covariance (L12-L13 ONLY):**
    $V_i = \mathbf{A}_i^{1/2}\operatorname{Corr}(\mathbf{Y}_i)\mathbf{A}_i^{1/2}$; there
    $\mathbf{D}_i=\partial\boldsymbol\mu_i/\partial\boldsymbol\beta$ is a derivative (not a covariance).
  - **SD-correlation split** is $\Sigma_i=\mathbf{S}\,\mathbf{C}\,\mathbf{S}$, never $\mathbf{D}\,\mathbf{R}\,\mathbf{D}$.
  - **Migration done 2026-06-19:** `NOTATION_REFERENCE.md`, both `_notation_box*.qmd` partials, project
    `CLAUDE.md` (two tables + pitfall 21), `SCALING_PLAN.md` lint. Decks: L03/L04/L05/L07/L08/L09 (B1-B3)
    prose + code/figures/tables/captions; L14/L15 (B5) math/tables; templates. L08's EBLUP sim had `D`/`Sigma`
    R objects renamed to `G`/`sigma2`; L05's $D R D$ slide renamed to $S C S$. L13 kept $V_i$/$D_i$ (GEE,
    correct). All 6 B1-B3 decks + L14 render OK; L15 has a separate pre-existing `MASS::select` render bug.
- **Reused-symbol override (non-reserved only):** a chapter that follows FLW in giving a non-reserved
  symbol a chapter-local meaning (e.g. FLW Ch. 5 uses $G$ = number of groups, which would collide with
  $G$ = random-effects covariance if random effects were present) MAY do so only if it declares the
  meaning up front on a lecture-specific slide after the include and re-shows the affected definitions.
  Reserved symbols ($\mathbf{X}_i/\boldsymbol\beta$, $\mathbf{Z}_i/\mathbf{b}_i$) are NEVER reassigned,
  and the shared partial is never edited for a chapter-local meaning. **L05:** $G$ = number of groups
  is collision-free (no random effects in Ch. 5); the subagent also renamed a group-indicator covariate
  $Z_{ig}\to W_{ig}$ to respect the reserved $Z$. [B2]

## Terminology

- "empirical BLUP" (define EBLUP as this at first use) / "predicted random effects", not "estimated
  random effects".
- "invalid inference" / "incorrect standard errors", not "biased standard errors" (FLW pp. 43-44).
- When within-subject correlation is ignored: point estimates stay **consistent (and unbiased under a
  correctly specified mean model)**; only the standard errors are incorrect. Use this phrasing across decks. [B1]
- "covariance matrix" and "correlation matrix" are not used interchangeably.
- REML for random-effects/covariance structure; ML for LRT of fixed effects (refit both with ML).
- `nlme::lme` reports containment df and provides neither Kenward-Roger nor Satterthwaite; those require
  `lme4` + `lmerTest` or `pbkrtest`. A deck must state this where it recommends KR/Satterthwaite.
- **"GLM" = generalized linear model only (Ch. 11+).** The general (normal) linear model (Ch. 3-5,
  response profiles) is written out or abbreviated "LM", never "GLM". Audit: L03 spells out "general
  linear model" (OK), L04 does not use the term (OK), L05 fixed from GLM -> general linear model/LM. [B2]
- **Change-score inefficiency mechanism:** explain as optimal-coefficient / regression-to-the-mean
  (change scores force the baseline coefficient to 1; ANCOVA estimates the optimal coefficient),
  giving RE $= 2/(1+\rho)$. It is NOT "measurement error" or "baseline used twice". [B2]
- **Beyond-FLW extensions** (instructor enrichment, e.g. Lord's paradox in Ch. 5) must be flagged as
  beyond the chapter and carry an external citation. [B2]
- **Static SAS slide = complete standalone program** (a full PROC MIXED block), not a cheat-sheet
  fragment table; a translation table may accompany it but does not satisfy the requirement. [B2]

## Datasets (canonical names)

`dental` (Orthodont), `tlc` (TLC lead trial), `epilepsy`, `fev1`, `rat`, `muscatine`. Use the same name
and load path (download fallback) across decks; do not rename per deck.

**Chapter -> canonical FLW dataset map (provenance gate) [B2 fidelity audit, 2026-06-19].** A deck must
NOT present an instructor-chosen or wrong-chapter dataset as "the chapter example" / "the genuine Ch.N
case study" / "our running example". For each dataset, either it IS FLW's example for THAT chapter (cite
the table/figure) or it carries a one-line label that it is an instructor substitution (and which FLW
chapter it actually belongs to). FLW's actual examples by chapter:
- **Ch. 1:** TLC lead trial, Muscatine obesity, anti-epileptic (epilepsy/progabide), Connecticut Child Surveys (Section 1.3).
- **Ch. 2:** TLC **placebo** group, N=50 (covariance Table 2.2: var 25.2/29.8/33.1/31.8; correlation Table 2.3: 0.76-0.87). NOT dental.
- **Ch. 5:** TLC trial (group means Table 5.6: Succimer 26.5/13.5/15.5/20.8); dental (Orthodont) also
  serves as a response-profiles example here (course dataset table: dental = Ch. 5/7/8), so dental in an
  L05 deck is NOT a substitution.
- **Ch. 6:** **Vlagtwedde-Vlaardingen** current/former-smoker FEV1 (liters, DECLINING over years 0-19; Tables 6.1-6.2, linear adequate G^2=1.3/2df/p>0.5). NOT the Topeka child-growth fev1.txt.
- **fev1.txt (Topeka girls, Six Cities, log FEV1 growth):** this is FLW's **Ch. 9** example (Table 9.1), not Ch. 1 or Ch. 6.
- **dental (Orthodont):** FLW Ch. 5/7/8 example, not Ch. 2.

## Cross-reference map (forward/backward pointers)

Maintained so the cross-lecture sweep can verify each pointer resolves. Seed entries:

- L08 (Ch. 8) recalls Ch. 7 (covariance structures) and forward-points to L09 / Ch. 9 (Fixed vs Random
  Effects, Hausman test). Verify L09 actually covers the Hausman test before B3 closes.

- **B1 (post-split):** the old combined L01 (Ch. 1-2) was SPLIT into L01 (Ch. 1, intro/designs,
  `BIOS667_L01_Intro_ch1.qmd`) and L02 (Ch. 2, basic concepts/notation/correlation sources,
  `BIOS667_L02_BasicConcepts_ch2.qmd`). So **L02 now exists** (the earlier "intentionally absent" note is
  void). Pointer chain: L01 (Ch.1) -> L02 (Ch.2) -> L03 (Ch.3); L02 recalls L01; L03 recalls L01/L02.
  The new chapter-tagged filenames (`_ch1`, `_ch2`) **close the RAG chapter-tagging TODO** (the indexer
  now associates each with its chapter); re-run the sync after re-indexing to confirm.

- **B2:** pointer chain L03 (Ch.3) -> L04 (Ch.4) -> L05 (Ch.5) -> L06 (Ch.6). L04 forward-points to L05 by
  name ("Looking Ahead"); L05 opens with "Recall from Lecture 4" (GLS/ML, REML vs ML, LRT); L06 opens with
  "Retrieval / Quick Recap from L5" and forward-points to L07 (Ch.7 covariance) and FLW Ch.19 (smoothing,
  a textbook chapter, NOT course Lecture 19). All resolve. L05/L06 forward-ref to Ch.11 (GLM) and Ch.8
  (random effects) resolve.

(Extend as batches are reviewed.)

## Deck conventions (structure and running examples)

- **Slide-count rule** (for `LECTURE_TIMING_PLAN.md`): rendered content slides = count of `## ` headers
  MINUS `## ` headers nested inside `:::` callout blocks (e.g. "Check Your Understanding"). Apply the same
  rule to every timing-plan row. [B1]
- **Intro-tier skeleton:** keep Objectives and Roadmap as `## ` content slides; reserve `# ` strictly for
  "Part N" period dividers. [B1]
- **AR(1) running example:** use $\rho = 0.8$ for the AR(1) illustration across decks unless a deck states
  an explicit reason to differ. [B1]
- **Common Mistakes / gotchas** are surfaced in a `::: {.callout-warning}` block (not a plain `## ` slide).
  [B1] (recorded; L01/L03 currently use plain slides, a low-priority backlog touch-up.)
- **Slide density / visual engagement:** run `2026/workflows/slide_density_check.py <deck>`; every flagged
  CONTENT slide is split or given a visual (R plot, diagram/schematic, annotated figure, or table).
  Illustrations over text; a wall of bullets is the top student complaint ("boring"). [split-L01]
- **Graduated notation (what is introduced):** the notation slide shows ONLY symbols introduced by that
  lecture. An intro/Ch.1 deck (L01) has NO notation slide; `_notation_box_intro.qmd` (lite) from the
  lecture that introduces the basic notation (L02/Ch.2); the full `_notation_box.qmd` from L08. Never
  front-load later-chapter symbols. [split-L01]
- **No empty slides:** never place a `---` immediately before a `# ` section divider (the `#` already
  starts its own slide, so the `---` renders a BLANK slide). `slide_density_check.py` flags this
  (YAML-aware) and a Chrome visual step-through of every batch deck is now a required per-batch step. [B1]
- **Notation-slide formatting [B2]:** wrap every notation table (shared include AND each deck's
  lecture-specific "Notation (this lecture)" table) in `::: {.notation-card}` so the `unc-gillings.css`
  rule narrows the Symbol column (Pandoc emits 50/50 `<col>` widths -> wide gap otherwise). Keep the
  slide a table; move "why" prose to `::: {.notes}`. Inline math ending in `)` then text collides
  ("$(...,N)$ and" -> "N)and"); drop the wrapping parens (`$i=1,\dots,N$`). Done for the lite/full
  includes and L04/L05/L06; **obligation:** apply `.notation-card` to L12/L14/L17 (and any deck with a
  notation table) when their batches run.
- **Full notation box is graduated [B2]:** `_notation_box.qmd` (used from L08) is the
  THROUGH-RANDOM-EFFECTS card and does NOT front-load GEE/GLM symbols. **Obligation:** L11 adds binary
  $\pi_{ij}$ + dispersion $\phi$; L13 adds GEE $\alpha$ as a lecture-specific row after the include.
- **Plots: self-identifying + diagnostic interpretation on-slide [B2]:** no `{.panelset}`/`{.small}`
  plot panels (the panelset puts code in tiny tabs and sends each plot to a separate untitled slide);
  every plot sets a `labs(title=...)`/facet label; a model comparison is ONE faceted+labeled plot;
  diagnostic plots render `echo: false` inline with a `::: {.callout-note}` reading rule on the SAME
  slide. Fixed in L06 (Compare Fits -> one `facet_wrap(~model)` plot; Diagnostics -> three titled slides
  each with a reading callout). **Obligation:** apply the same check to L07-L19 in their batches; a
  title-coverage grep flagged L11-L19 as candidates (the grep undercounts multi-line `labs()`, so it is
  a candidate list, not confirmed).

## Global-change history

Global changes applied across the framework, with the batch/lecture that triggered them:

- From the L08 panel (2026-06-18):
  - G-1 notation no-collision guardrail -> `NOTATION_REFERENCE.md`, template include comment,
    `_notation_box.qmd` header.
  - G-2 nlme cannot produce KR/Satterthwaite -> `REFERENCE_DECK_SPEC.md` + `POST_LECTURE_REVIEW.md`.
  - G-3 per-slide diagnostic reading rule -> `REFERENCE_DECK_SPEC.md` checklist + `POST_LECTURE_REVIEW.md`.
  - G-4 self-documenting reused control objects -> `REFERENCE_DECK_SPEC.md` + `POST_LECTURE_REVIEW.md`.
  - G-5 redundancy-vs-budget note -> `LECTURE_TIMING_PLAN.md`.
- From the L05 panel (B2, 2026-06-18):
  - L05-G01 reused-symbol override rule (non-reserved only) -> `NOTATION_REFERENCE.md`,
    `_notation_box.qmd` header, `REFERENCE_DECK_SPEC.md` QA notation bullet, ledger Notation above.
  - **Book-first notation + N=subjects flip (PI directive 2026-06-18, supersedes the n/N "override"):**
    adopt FLW notation course-wide; $N$ = subjects, $n$/$n_i$ = occasions -> `NOTATION_REFERENCE.md`
    (subscripts + book-first note), both partials' index lines, project `CLAUDE.md` subscript
    conventions, decks L02/L03 reconciled, L05 notation slide reframed as canonical. See ledger
    Notation above and memory `bios667-notation-follows-flw`.
  - L05-G02 "GLM" = generalized linear model only; general LM is "LM" -> `NOTATION_REFERENCE.md`,
    `_notation_box.qmd` header, `REFERENCE_DECK_SPEC.md` QA notation bullet, ledger Terminology above;
    L03/L04 audited clean, L05 fixed locally.
  - L05-G03 change-score inefficiency = optimal-coefficient/regression-to-mean, not measurement error
    -> project `CLAUDE.md` Statistical Precision Standards #7, ledger Terminology above.
  - L05-G04 static SAS = complete standalone PROC MIXED program -> `REFERENCE_DECK_SPEC.md` (Computing
    detail + QA checklist), `POST_LECTURE_REVIEW.md` SAS-reference item, ledger Terminology above.
    **Audit obligation:** the L08 exemplar's SAS slide must be re-checked in B3 (it may be a cheat-sheet).
  - L05-G05 beyond-FLW extensions flagged + external citation -> `REFERENCE_DECK_SPEC.md` (book-accuracy
    item 1 + QA checklist), `POST_LECTURE_REVIEW.md`, ledger Terminology above.
- From the B2 book-fidelity audit (2026-06-19, `book_fidelity_audit.mjs` over L01-L06 + author-slides check):
  - **Required three-source fidelity pass** wired into `POST_LECTURE_REVIEW.md` Dimension A and the
    `SCALING_PLAN.md` per-batch step: RAG textbook + chapter PDF (read tables/figures for every numeric
    value and conclusion) + the **authors' BIO 226 slides** (indexed `source_type='author_slides'`, 66
    chunks) for departures AND omissions. CLAUDE.md pitfall #20 summarizes.
  - **Dataset fixes applied:** L02 -> TLC placebo (Tables 2.2/2.3); L06 -> Vlagtwedde-Vlaardingen smoker
    FEV1 (Tables 6.1/6.2, linear adequate). See chapter->dataset map under Datasets above.
  - **RE correction:** `2/(1+rho)` is the n=2 case of the ANCOVA-vs-change *efficiency* `n/{1+(n-1)rho}`
    (the reciprocal of FLW eq (5.3)'s variance ratio `(1/n){1+(n-1)rho}`), not the general result; fixed
    in project `CLAUDE.md` #7 and L05. Lesson: verify CLAUDE.md constants against the PDF; do not dismiss
    an audit formula flag without reading the book.
  - **Beyond-FLW flags + method attribution applied** across L01-L05 (score test/MNAR/MI/IPW, AR(1)/ACF,
    spaghetti-plot framing, ddfm=kr -> Wald CHISQ, etc.); all kept but flagged, methods matched to FLW.
- **FLW-symbol migration (PI directive 2026-06-19, "100% fidelity to the book; notation reference is the
  single source of truth"):** marginal covariance $V_i\to\Sigma_i$, random-effects covariance $D\to G$,
  $V_i$ retained only for the GEE working covariance (L12-L13). Verified against the FLW PDFs. Touched
  `NOTATION_REFERENCE.md` (core table + FLW-symbol rulings, the master), both `_notation_box*.qmd`
  partials, project `CLAUDE.md` (both notation tables + rewritten pitfall #21), `SCALING_PLAN.md` notation
  lint; decks L03/L04/L05/L07/L08/L09 (B1-B3) in prose AND code/figures/tables/captions, L14/L15 (B5)
  math/tables, both templates. See the FLW-symbol ruling under Notation above. Lesson: the migration must
  reach code/figure/caption layers, not just prose (L08 EBLUP sim built `D`/`Sigma` R objects; renamed to
  `G`/`sigma2`), and anchored greps miss the `$$D = \begin{pmatrix}` form.
- **From the B5 batch (2026-06-19):**
  - B5-G01 **Zeger attenuation labeling unified.** The logistic random-intercept attenuation is
    $\beta^{\text{marg}}\approx\beta^{\text{cond}}/\sqrt{1+c_2^2\sigma_b^2}$ with the single constant
    $c_2=16\sqrt3/(15\pi)\approx0.588$ (FLW p.477); $0.346=c_2^2$ is the multiplier on $\sigma_b^2$
    ($=(1/1.7)^2$, probit form), **not an alternative constant**. Fixed the "0.346 vs 0.588 alternatives"
    wording in `NOTATION_REFERENCE.md`, project `CLAUDE.md` (formula-verification checklist + textbook-
    alignment item 1), and the L15 speaker note; L14 already stated it canonically (the model to match).
  - B5-G02 **`exactRLRT`/`RLRsim` are Gaussian-LMM-only.** GLMM variance-component boundary tests
    (random slope in Poisson/logistic) need a **parametric bootstrap** of the LRT (or the conservative
    Stram-Lee $\tfrac12\chi^2_1+\tfrac12\chi^2_2$ mixture), never `exactRLRT`. Added to CLAUDE.md pitfall
    #8; L14 replaced its `exactRLRT` call accordingly.
  - B5-G03 **L15 relabeled course slot "Lecture 15" -> FLW Ch.14** (random slopes are Ch.14 content; FLW's
    physical Ch.15 = Approximate Methods PQL/MQL is enrichment only, AGQ is the taught Ch.14 benchmark).
    Synced the Content Coverage Matrix (`CLAUDE.md`) and `LECTURE_TIMING_PLAN.md`; deck title/footer/intro
    already carry the Ch.14 label + on-slide rationale.

## FLW explicit cautions (caution-reversal watch list)

Do NOT teach the opposite of these. Check every covariance/diagnostics/GLMM deck against this list
(CLAUDE.md pitfall 23a). Grow it as audits find more.

- **BLUP / empirical-Bayes QQ plots do NOT test random-effects normality (FLW p.273).** The empirical
  BLUPs are shrunk toward the population mean, so their distribution understates the true RE variance; use
  them only to spot individuals with unusual profiles. (L10 originally taught the reverse.)
- **Ignoring within-subject correlation gives "invalid inference / incorrect standard errors," not
  uniformly "biased / too-small SEs"** (FLW pp. 43-44): the direction depends on whether the covariate is
  within- or between-subject.
- **Marginal residuals/means in nlme vs lme4 (two different traps).** nlme: `residuals.lme()` defaults to
  CONDITIONAL (innermost); the CORRECT fix for marginal residuals is to set `level=0` (which for an LMM
  genuinely gives $Y-X\beta$). lme4: `re.form=NA` is NOT a marginal-mean shortcut for a GLMM (it predicts
  at $b_i=0$); true GLMM marginal means require integration over the random effects. Never state
  "`resid()` is marginal by default."

## Notation (GEE-symbol introducing decks)

- **L12 is the introducing deck for the GEE working-covariance notation** $V_i(\alpha) = \mathbf{A}_i^{1/2}\operatorname{Corr}_i(\alpha)\mathbf{A}_i^{1/2}$
  and the working-correlation parameter $\alpha$ (added as a lecture-specific row after the include). L13
  extends it. Do NOT write the working correlation as $R(\alpha)$ (collides with the reserved residual
  covariance $R_i$). **B5 alignment (2026-06-19):** L13 now writes the working correlation as FLW's
  $\operatorname{Corr}_i(\alpha)$ and the working covariance as
  $V_i = \mathbf{A}_i^{1/2}\operatorname{Corr}_i(\alpha)\mathbf{A}_i^{1/2}$ with
  $\mathbf{A}_i=\operatorname{diag}(\phi\,v(\mu_{ij}))$ (dispersion $\phi$ inside $\mathbf{A}_i$), matching
  L12. The B4-era L12 $V_i(\alpha)$/$R(\alpha)$ wording is retired in favor of $\operatorname{Corr}_i(\alpha)$.
- **L11 (Ch.11 GLM review) legitimately carries a large beyond-FLW enrichment block** (ordinal POM,
  multinomial, ROC/AUC, calibration, Hosmer-Lemeshow, zero-inflated/hurdle, sandwich SEs, AIC). These are
  acceptable ONLY because each is flagged "Beyond FLW Ch.11 (instructor extension)" with a citation; the
  reviewer should confirm the flags persist, not re-litigate the content.

## Batch log

- **B1 (L01, L03): complete.** Lint fixed; panels done (no statistical must-fix, both faculty "minor
  gaps"); graduated-tier local fixes applied; lite intro notation box + graduated-tier spec added.
  Cross-lecture sweep (wf_c9a53ad5): notation/terminology fully consistent, all cross-refs resolve;
  minor issues fixed (L01 en-dashes -> hyphens, L03 title "(Ch. 3)", AR(1) rho aligned to 0.8) and the
  conventions above recorded. Backlog (low): wrap "Common Mistakes" in callout-warning on both decks.
  Audits: `BIOS667_L01_reference_audit.md`, `BIOS667_L03_reference_audit.md`.
  RAG fidelity (run in the orchestrator via the venv, since the MCP is unreachable headless and the panel
  faculty had `rag_used=false`): L03/ch3 healthy (covered=12, gaps=2, mismatches=8 post re-index); L01/ch1-2 returned
  covered=0 even after an incremental re-index, so the root cause is **chapter-tagging, not staleness**:
  L01's filename has no chapter tag (unlike L03's `..._ch3`), so the indexer does not associate L01's
  chunks with ch 1-2. **RAG-index TODO (open):** make the corpus indexer infer `chapters` from the deck
  title/YAML (e.g. "Ch. 1+2") or add a filename->chapter map, then re-run the L01 sync. Not a deck
  content gap. (Affects any deck whose filename omits the chapter tag.)
- **B2 (L04, L05, L06): complete.** Lint + panels done; all L05 local fixes (16) and the five L05 global
  changes applied (notation override rule, GLM=generalized only, change-score mechanism =
  optimal-coefficient/regression-to-mean, static SAS = full PROC MIXED, beyond-FLW citation). **Book-first
  notation flip:** adopted FLW $N$=subjects / $n$=occasions course-wide (canonical + partials + project
  CLAUDE.md + L02/L03 reconciled). Cross-lecture sweep (wf_b215d41c): batch "minor issues", concentrated
  in L06, which carried 2027-track AI/Exit-Ticket machinery and simulated-only data; L06 brought to spec
  (AI machinery removed/converted, REAL fev1 Case Study added, GLM->LM slide title, standard YAML, AR(1)
  rho->0.8, Part I divider added, $\mathbf{X}_{ij}$->row form, $a$->$g$ group index, Ch.19->FLW Ch.19,
  AUC overstatement dropped). L04 fixes: $R_i$=missingness-indicator declared on the notation slide +
  false "two lectures ago" speaker note corrected, AR(1)/CS rho->0.8, forward pointer names L05, OLS
  $n$ clarified. L05: "Recall from Lecture 4" slide added. Timing plan refreshed (L05 73->75, L06 67->52;
  L06 reclassified flexible 1.5-2 periods). All B2 decks render exit 0, 0 em/en-dashes, 0 empty slides.
  Audits: pending (this commit). RAG fidelity: check_lecture_sync to be run in the orchestrator (venv).
- **B3 (L07, L08, L09): complete.** Gate-0 fix (installed `plm` so L09 renders); framework alignment
  (L07/L09 dashes, YAML, notation includes, L09 guarded loads). Three-source fidelity audit
  (wf_8655579a) + cross-lecture sweep (wf_5b605237): "minor issues". **L09 REBALANCED to FLW-primary** (FE
  = OLS dummies, RE = the Ch.8 mixed model, the between/within decomposition eq 9.5 + the
  $\beta^{(C)}=\beta^{(L)}$ test as the centerpiece; real Six Cities case study on fev1.txt, FE=RE=0.0298
  congruent, contextual p~0.72; the plm/Hausman/Swamy-Arora/two-way-FE/robust-SE econometrics treatment +
  the simulation demoted to a flagged "Beyond FLW" supplement). L07: BIC flagged (FLW p.179), ACF/
  semivariogram flagged beyond-FLW + the FLW-native UN-vs-pattern REML-LRT added, a **complete PROC MIXED
  SAS slide added** (was a cheat-sheet only -> L05-G04 now satisfied), Part I/II dividers added,
  $\Sigma_i\equiv V_i$ declared, boundary-LRT reframed to $H_0:\sigma_b^2=0$. L08: Table C.1 mixture +
  $\alpha=0.10$ attribution (5.14 = q=1 / random-slope, not single-variance), bootstrap/KR flagged
  beyond-FLW, marginal reworded, $\beta^\top x\to X_{ij}\beta$, bare $\Sigma\to V_i$/$R_i$, $G\to D$, L178
  backward-ref fixed, a pre-existing empty slide fixed. **Statistical corrections** (commit review,
  verified vs PDFs): L07 AR-vs-UN conclusion was reversed (AR IS rejected, $G^2=23.8$/13df/p<0.05; EXP
  preferred); UN-vs-pattern LRTs are ordinary $\chi^2$ not boundary tests. Both standing obligations
  DISCHARGED (L08 SAS = full program; L09 covers the Hausman test). Timing plan refreshed (L07 73, L08 72,
  L09 31 / 1 period). All three render exit 0; 0 em/en-dashes; 0 empty slides; Chrome visual pass clean.
  Audits: `BIOS667_L07_reference_audit.md`, `..._L08_..` (B3 re-audit section), `..._L09_..`.
- **B4 (L10, L11, L12): decks brought to full spec (2026-06-19).** Panels + three-source fidelity audit
  (22 confirmed departures, all "needs work"); audit files written. **L10 corrected to FLW Ch.10** (the
  Content Coverage Matrix wrongly had L10 = "-"; FLW Ch.10 IS "Residual Analyses and Diagnostics," pp.
  265-290; standalone PDF was missing from `book/` so it was extracted from the full-book PDF and the RAG
  re-indexed for chapter=10). Full-spec rebuilds applied and committed:
  - L10: removed a FABRICATED diagnostic (`abs(rnorm())` plotted as cluster influence); added FLW's core
    machinery (transformed/Cholesky residuals eq 10.2, Mahalanobis distance eq 10.3, Lin-Wei-Ying aggregated
    sums, semi-variogram on transformed residuals centered at 1); fixed the caution-reversal (BLUP-QQ for RE
    normality, FLW p.273); real dental Case Study; SAS + notes + scaffolding.
  - L11: flagged 13 beyond-FLW blocks with citations; FLW exponential-family form; 2 real Case Studies (TLC
    logistic, epilepsy Poisson); row-form + lecture-specific notation; SAS + notes + dividers. Deck grew
    (~2.5-3 periods); timing plan updated.
  - L12: dropped the clustering-blind `polr` fit; removed the "FLW p.528" mis-citation; renamed R(alpha) ->
    V_i(alpha); epilepsy GEE Case Study (robust SE ~4x naive); Frechet-bound table fixed (commit-review
    catch); compressions + notation row + SAS + notes.
  All three render exit 0; 0 em/en-dashes; 0 empty slides. Audits: `BIOS667_L1{0,1,2}_*_reference_audit.md`.
  Cross-lecture sweep (wf w9sigxoh0): notation consistent; fixed L11-over-claims-L10 recall, the
  L11/L12 ordinal-cutpoint split (-> $\kappa_k$ course-wide), $v(\mu)$ casing, and a full
  timing-plan reconciliation. **On-demand codex review of the three deck commits:** L10 (ca6653e) had
  TWO real narrative-vs-output defects (variogram "drifts off 1" and ACF "within bands" claims the dental
  data did not support) - codex caught them by RE-RUNNING the chunks; fixed over a multi-round chain
  (labels/title, lag-3 band, note-hardcoding, decision-tree contradiction, Ch.7-not-13, corAR1 form=,
  Pandoc pipe-in-table backslash leak, time->age_c). L11/L12 Case Study numbers verified correct and
  inline-R (epilepsy RR 0.82/phi 12.05, TLC OR 0.18/1.33, L12 GEE RR 0.90 / robust SE 4.29x / alpha 0.41);
  codex's L11 sandbox failed twice (bwrap) so L11 was hand-verified. **B4 lessons wired in:** CLAUDE.md
  pitfalls 24 (narrative-vs-output + inline-R, notes included), 25 (Pandoc pipe-in-table trap), 26
  (repoint cross-deck recall after a rebuild; pre-register shared symbols); POST_LECTURE_REVIEW Gate 0b;
  SCALING_PLAN per-batch step + "B4 process lessons"; commit-hook lens 4. **B4 COMPLETE.**
- **B5 (L13, L14, L15, L16): decks brought to full spec (2026-06-19).** Full-spec rebuilds applied and
  committed one deck per commit (each got a commit-hook review):
  - L13 (GEE Extensions, Ch.13): working correlation written as $\operatorname{Corr}_i(\alpha)$ (FLW's
    symbol; the L12 carry-over $R(\alpha)$/$V_i(\alpha)$ collisions retired course-wide, see below), GEE
    working covariance in FLW form $V_i = A_i^{1/2}\operatorname{Corr}_i(\alpha)A_i^{1/2}$ with
    $A_i = \operatorname{diag}(\phi\,v(\mu_{ij}))$ (dispersion $\phi$ INSIDE $A_i$, no separate $\phi$
    factor); QIC / IPW-GEE / Kauermann-Carroll-Fay-Graubard small-sample SEs flagged as beyond-FLW; epilepsy
    GEE Case Study with provenance; PROC GENMOD SAS; "Day 1 Recap" divider.
  - L14 (GLMMs, Ch.14): boundary mixture corrected to $\tfrac12\chi^2_1+\tfrac12\chi^2_2$; **`exactRLRT`
    replaced by a parametric bootstrap** (exactRLRT is Gaussian-LMM-only, now a CLAUDE.md pitfall #8
    addendum); attenuation stated canonically as $\beta^{\text{marg}}\approx\beta^{\text{cond}}/\sqrt{1+c_2^2\sigma_b^2}$,
    $c_2=16\sqrt3/(15\pi)\approx0.588$, $c_2^2\approx0.346$ (the multiplier, $=(1/1.7)^2$); Jensen mechanism
    for asthma; $f_G(b_i)$ density; epilepsy Table 14.6 reproduced; PROC GLIMMIX; `set.seed(667)`.
  - L15 (GLMM Random Slopes): **relabeled course slot "Lecture 15" → FLW Ch.14** (random slopes are FLW
    Ch.14 content; FLW's physical Ch.15 = Approximate Methods PQL/MQL, which the deck flags as enrichment,
    with AGQ as the taught Ch.14 benchmark). Stram-Lee boundary fix; $\rho_{01}\approx-0.057$; Table 14.6 +
    NB/`glmmTMB`; ~15% conditional-vs-marginal gap computed on the epilepsy fit (no asserted closed-form
    number). Matrix + timing plan synced to Ch.14.
  - L16 (Contrasting Models, Ch.16): the `id=factor(row_number())` reshape bug fixed (→ 67 subjects),
    reproducing FLW Tables 16.2/16.3 (GEE OR 1.77 / GLMM nAGQ=100 OR 6.44 / Var(b) 24.4); attenuation
    constant labeled consistently; single inverse-link name $h$; $1/4$ added to the single sampling-zero
    cell; clogit robustness check (treatment-only). Commit-review follow-ups: removed two blank Part-divider
    slides (pitfall #1) and dual-cited the conditional-ML source (results in Section 16.5, method in 14.6).
  All four render exit 0; 0 em/en-dashes; 0 empty slides; FLW table values verified present in rendered
  HTML (inline-R, narrative-matches-output). Audits: `BIOS667_L1{3,4,5,6}_*_reference_audit.md`.
  **codex caveat:** codex was rate-limited for L14/L15/L16, so those got the gate battery + same-model
  (claude-fallback) commit reviews only; **re-run a real codex pass on the B5 deck commits when the usage
  limit resets.** **Cross-deck doc reconciliations wired in:** Zeger attenuation labeling unified
  ($c_2$=0.588 constant, $c_2^2$≈0.346 multiplier, NOT alternatives) in NOTATION_REFERENCE + CLAUDE.md
  (×2) + L15 note; `exactRLRT`-Gaussian-only / GLMM-needs-parametric-bootstrap rule added to CLAUDE.md
  pitfall #8; L15 Ch.15→Ch.14 relabel recorded in the Content Coverage Matrix + LECTURE_TIMING_PLAN.
  **B5 COMPLETE.**
- **B6 (L17, L18, L19): chapter-mapping reorder (PI directive 2026-06-19); full-spec rebuilds in
  progress.** The course's late-topic labels did not match FLW's 2nd-ed TOC (verified from the Front
  Matter PDF): FLW Ch.17 = Missing Data Overview, Ch.18 = Missing Data MI/Weighting, Ch.19 = Smoothing
  (semiparametric); there is NO 2nd-ed transition-models chapter (it was 1st-ed Ch.10). The decks were
  L17 = Missing overview (correct, Ch.17), L18 = Transition (suffix _ch18 wrong), L19 = Advanced missing
  (content is Ch.18, suffix _ch19 wrong). PI chose "reorder so missing-data is contiguous":
  - L17 = FLW Ch.17 (Missing Data and Dropout: Overview of Concepts and Methods). Unchanged.
  - L18 = FLW Ch.18 (Missing Data and Dropout: Multiple Imputation and Weighting Methods). This is the
    FORMER L19 content (pattern-mixture, MNAR, selection, MI/IPW). Renamed
    `BIOS667_L19_MissingData_Advanced_ch19.*` -> `BIOS667_L18_MissingData_Advanced_ch18.*`.
  - L19 = Transition (Markov) models, a flagged INSTRUCTOR TOPIC (FLW 1st-ed Ch.10; not a 2nd-ed chapter),
    so NO `_chNN` suffix. This is the FORMER L18 content. Renamed
    `BIOS667_L18_TransitionModels_ch18.*` -> `BIOS667_L19_TransitionModels.*`.
  Synced the Content Coverage Matrix + timing-classification table (`CLAUDE.md`) and `LECTURE_TIMING_PLAN.md`
  (slide counts move with content: L18 now 83 slides/Dense, L19 now 68/Standard). Per pitfall #27, the
  `.qmd` + `_note.md` siblings were `git mv`- d together and stale `.html`/`_cache`/`_files` removed.
  **Full-spec rebuilds applied and committed (one deck per commit, each reviewed):**
  - L17 (Ch.17 missing overview): fixed the LVCF bias formula (spurious -alpha_2 removed), declared the
    R_i = missingness-indicator chapter-local override (pitfall #14), removed 6 blank slides, standard
    de-dashed YAML, real fev1 Case Study + SAS slide + speaker notes; follow-ups inline-R'd the fev1 note
    numbers (pitfall 24d) and fixed a REML/ML label and a circular CYU wording.
  - L18 (Ch.18 missing advanced): was render-failing; fixed two render-blockers, rewrote the broken MNAR
    sim (monotone post-baseline, no zero-occasion subjects), added IPW/weighted-GEE (FLW 18.3) as a
    co-primary method alongside MI (Rubin's rules), real TLC MI Case Study (reproduces FLW Table 18.1
    -3.152), declared R_ij notation, fixed stale Ch.14/19 refs, removed blank slides, SAS + notes. An
    INDEPENDENT review (not the rebuild author) re-ran the chunks and caught a [high] dplyr ordering bug
    that NA-d the entire Part V delta sensitivity analysis (estimate collapsed before var(estimate)); fixed
    + verified finite SEs, and corrected an IPW dose overclaim.
  - L19 (transition instructor topic): fixed the beta_1=0 Markov misstatement, added the instructor-
    extension provenance flag, repointed the FLW-Ch.18 mis-citation to 1st-ed Ch.10, row-form X_{ij}
    notation, retired R(alpha) -> Corr_i(alpha), subject index on the transition probability, stale
    forward ref.
  Cross-ref repointing done: HW6/HW6_solution/Quiz6 chapter refs ("Chapters 18-19" -> Lectures 17-19 =
  Ch.17-18 missing + transition instructor topic), STUDENT_REVIEW_L17-L19 stale-bannered. All three decks
  render exit 0 with clean gate batteries; Gate 0b narrative-vs-output verified. **codex caveat:** codex
  was rate-limited for most B6 commits (resets ~2026-06-24); they got gate-battery + same-model
  (claude-fallback) reviews, except L18 which got a dedicated INDEPENDENT subagent review. **Re-run a real
  codex pass on the B6 deck commits when the limit resets.** **B6 decks COMPLETE.**
- **Final global cross-lecture sweep COMPLETE (2026-06-19).** Purpose: catch backport gaps where early
  decks (B1-B3) missed standards codified in later batches. MECHANICAL LINT (all 19 decks): dashes, section
  symbol, 2027-track machinery, pipe-in-table, retired notation ($V_i$-Gaussian / $D$-RE / $R(\alpha)$),
  YAML, `incremental` ALL clean corpus-wide (every $V_i$/$D$ grep hit was correct GEE/teaching usage). Only
  mechanical gap: L13 had 7 blank slides (pitfall #1, missed in its B5 rebuild) - removed. SEMANTIC AUDIT
  (L01-L12, 4 parallel subagents re-running chunks): notation migration + book-fidelity + beyond-FLW
  flagging fully back-ported; L05/L06/L09/L10/L12 clean on every dimension. Gaps found + fixed:
  - **[high] L01** naive-vs-cluster SE demo drew the OPPOSITE of its claim (covariate was within-subject,
    orthogonal to the random intercept, so the slope SE was not inflated; naive 0.086 > cluster 0.064 at
    seed 667). PI chose DGP redesign: between-subject time-invariant exposure; now naive < cluster across
    5 seeds, inline-R.
  - **[high] L08 (exemplar)** taught BLUP/empirical-Bayes QQ plots to assess random-effects normality in 3
    spots - the caution-reversal FLW p.273 warns against (the L10-rebuild lesson never backported). Added
    the callout + relabeled the recipe card/checklist. (New caution-watch confirmation: this is the same
    p.273 caution already on the watch list.)
  - **[medium] L03** had no real Case Study (all simulated) - added a TLC placebo case study (PI-approved).
  - **[medium] L04** four "course L17-L19" pointers -> "L17-L18"; **L11** IPW-GEE mis-attributed to Ch.13 ->
    missing-data chapters, and "Next Lecture GEE (Ch.12)" -> "Marginal Models (Ch.12)".
  - **[low]** L02 adjacency wording; L03 lag-4 0.41->0.36 note (#24d); L07 three corStruct `form=` names;
    L01 "times smaller"->"times larger"; L03 robust column selection.
  All sweep-edited decks render exit 0, dash-clean, numbers inline-R and verified. **codex caveat:** codex
  rate-limited throughout (resets ~2026-06-24); re-run a real codex pass on the B5/B6 + sweep commits when
  it resets. **ALL 19 REFERENCE DECKS NOW STANDARDS-ALIGNED.**
- **Homework review + Tier 1-2 fixes COMPLETE (2026-06-20).** Built `2026/HW_REVIEW.md` (5 dimensions:
  structure, vs FLW end-of-chapter Problems, vs prior-professor materials, solution-code re-run, cross-HW
  consistency). Piloted HW1, then audited HW2-HW6 (one `HW{N}_review.md` each, propose-only, every review
  re-ran the solution). **Dimension-C method finding:** the prior professor's materials are the 838 indexed
  SAS programs + rcode (bare-filename `source_path`, NOT under `new/2026|new/2025`); the corpus has NO
  prior-year `.qmd` homeworks. Tier 1 (correctness) + Tier 2 (mechanical) fixes applied per-HW (each
  committed + commit-reviewed):
  - HW1: Q4c/Q4d GLS-vs-OLS SE direction (was reversed), V_i->Sigma_i / e_i->epsilon_i, filled placeholders.
  - HW2: Q3d change-from-baseline contrasts recoded (were between-group gaps), week-6 p=0.063 verdict,
    Q1c ML/REML attribution, absolute paths -> download-fallback.
  - HW3: solution KEY now renders (Q5d Mundlak singular on balanced dental -> degeneracy handled honestly);
    Q3c boundary test -> Stram-Lee 1/2chi1+1/2chi2 (p=0.417); N(0,D)->N(0,G).
  - HW4: Q5d all-NA publication summary fixed (unnamed robust_se); Q5b 'GLMM>GEE' false (log-link, not
    logistic attenuation); R_i(alpha)->Corr_i(alpha); SE-verdict made data-conditional.
  - HW5: Zeger constant fixed (was self-contradictory 0.346=sqrt(3)/pi -> canon c2=0.588/c2^2=0.346);
    Q4d MAR demo -> 100-rep so the narrative matches. **Q4/Q5 missing-data scope left for Tier 3.**
  - HW6: Q3d/Q4d MNAR narrative-vs-output (CC under / MAR overshoots; oracle-RE imputation replaced with
    fitted MAR predictions). **IPW question + real datasets left for Tier 3.**
  All 12 HW files dash-clean, render exit 0, no answer leaks; render-only `2026/homework/data/` gitignored.
- **Homework TIER 3 (curriculum) decisions made + applied (2026-06-20, PI-approved).** Decisions: (1)
  restructure HW5<->HW6; (2) adopt an IPW-GEE question (HW6), fix HW3 Mundlak properly, and adopt other
  FLW Problems (NCGS 5.1 / ACTG 8.2 / toenail 14.1); (3) NOT the broad canonical-dataset swap (HW6 stays
  simulated). New FLW datasets downloaded + gitignored (cholesterol.dat, cd4.dat, toenail.dat, birthwt.dat;
  the review's "bw5.dat" was the prior prof's name - FLW's Ch.9 maternal-age file is `birthwt.dat`).
  Applied per-HW (each committed + reviewed):
  - HW2: re-anchored the response-profiles Q3 on NCGS cholesterol (FLW Ch.5 Problem 5.1) + the by-hand
    L-contrast (5.1.8) and mean-reconstruction (5.1.9) derivations; parallelism LR~7.05, p~0.104 (fail to
    reject, matches FLW); corSymm indexed by OCCASION (occ_idx), not row order (2 interior-missing subjects).
  - HW3: re-based the Mundlak/FE-vs-RE Q5 on FLW Ch.9 birthwt (maternal age) - contextual term now
    IDENTIFIED (between-mother SD 3.69; beta_L=FE=11.83, beta_C=30.36; beta_C=beta_L test p=2.4e-05); added
    ACTG/CD4 random-slope LME (Problem 8.2) as Q3 part (e).
  - HW5: RESTRUCTURED - dropped the mis-scoped missing-data Q4/Q5, added random-slope GLMM (toenail, FLW
    14.1; parametric-bootstrap boundary test p=0.005, NOT exactRLRT) + AGQ quadrature sensitivity + the
    Ch.16 GEE-vs-GLMM contrast (GEE -0.078 / GLMM -0.142). Common-intercept model per FLW 14.1.1 (justified).
  - HW6: added the IPW-GEE question (FLW Ch.18 pillar) by consolidating the two transition questions into
    one (full -4.07 / naive -4.80 / IPW -4.05). "inverse-probability weight" terminology (NOT "stabilized",
    matching FLW p.529 + L18). HW6 stays simulation-based (per the decision).
  All four render exit 0, 5x20=100, dash-clean, inline-R, no leaks. The HW5<->HW6 overlap is resolved (HW5
  now its own Ch.14-16 content; HW6 owns missing data). codex rate-limited for all HW commits (same-model
  reviews only); **re-run a real codex pass on the HW commits when it resets**.
- **Quizzes (Quiz1-6) reviewed + fixed (2026-06-20).** Audited all 6 (30 MC/numeric questions); every
  answer key verified correct (incl. the 6 numerics: 55, 3 df, 2 params, 1.05, 4.5, 0.0505). Fixes:
  em-dashes removed from all 6 titles; Quiz1 Q2 negative stem ("which is NOT") -> positive stem, Q4
  e_i -> epsilon_i; Quiz2 ### -> ## headers; Quiz5 swapped Q3 (GEE-vs-GLMM, overlapped Q1/Q5) for a
  random-slope GLMM boundary-test question so the quiz spans L14/L15/L16; Quiz6 Q1 "None of the above" ->
  reason-paired options (MAR misconception as distractor D); lecture/section refs added to every answer
  key. Verified the Quiz5 Q3 boundary direction numerically: for dropping a random slope (two params,
  correct null 1/2chi2_1+1/2chi2_2, 95th pctile 5.14), naive chi2_1 (3.84) over-rejects (actual size
  ~9.8% at nominal 5%) = anti-conservative. All 6 render exit 0, dash-clean, 5 questions each, no negative
  stems, no all/none-of-the-above. codex rate-limited (same-model reviews only); re-run a real codex pass
  when it resets.
- **Final cross-material consistency/accuracy/code-result/prose pass COMPLETE (2026-06-20).** Capstone
  integration check across all 37 student-facing materials (19 decks + 12 HW + 6 quizzes). MECHANICAL
  LINT clean corpus-wide: 0 em/en-dashes, 0 section symbols, 0 retired notation (V_i-Gaussian / D-RE /
  R(alpha) / e_i), no stale chapter mappings, all HW/quiz lecture refs resolve to L01-L19. THREE parallel
  audits: (1) CROSS-MATERIAL CONSISTENCY - all 7 themes AGREE across lectures/HW/quizzes (Zeger
  c2=0.588/c2^2=0.346 logistic-only; Stram-Lee 1/2chi1+1/2chi2 + exactRLRT-Gaussian-only/GLMM-bootstrap;
  GEE-MCAR/IPW-GEE-MAR/Rubin T=W+(1+1/m)B/IPW-not-stabilized; Sigma_i/G/R_i/V_i-GEE/Corr_i(alpha) notation;
  |GLMM|>|GEE| attenuation direction; canonical datasets per chapter; post-B6 reorder L17/L18/L19). (2)
  CODE-RESULT - all 12 priority files (4 Tier-3 HW + 6 B5/B6 decks + HW1/HW4) render exit 0 and every
  headline number reproduces (all inline-R, cannot drift); no fabricated diagnostics. (3) ACCURACY+PROSE -
  "exceptionally clean"; all high-stakes formulas/cautions correct (attenuation, boundary mixtures, Rubin,
  RE=2/(1+rho) n=2 case, re.form=NA-not-marginal, BLUP-QQ p.273, Hausman, OR-vs-RR). Residual fixes
  applied: standardized L17 NMAR->MNAR (corpus uses MNAR); HW2 Q1a (N-p)/N qualifier; HW4 Q3c placeholder +
  AI-tell; HW6 Q5c dead code; L11 GLM score-equation dimension fix + value-anchored OR prose. codex
  rate-limited throughout the session (same-model reviews only); **the one outstanding item is a real codex
  re-run on the B5/B6 + global-sweep + HW + quiz + final-pass commits when the limit resets (~2026-06-24).**
  Housekeeping (CORRECTED 2026-06-20): the `BIOS667_L08_LME_Part1.qmd` / `BIOS667_L17_MissingData_Part1.qmd`
  files are NOT orphan drafts - on inspection they are deliberate **v2-template exemplars for the 2027
  AI-era condensed track**, instantiated from `Lecture_Template_v2.qmd` and showing the full learning arc
  (oral retrieval / designed first encounter / concept / board-to-code / worked example / AI-augmented
  practice with Tutor-Critic / oral exit check). `TEMPLATE_VS_SLIDES_ASSESSMENT.md` calls them "the only
  fully conforming files" for that template. They are intentional and DISTINCT from the 2026 reference
  decks (and carry exactly the 2027 machinery that pitfall #11 forbids in 2026 reference decks). Do NOT
  remove or treat as part of the 19-deck 2026 sequence. The `Lecture_Template*.qmd` /
  `Reference_Deck_Template.qmd` files are the intended deck skeletons (CLAUDE.md cites the latter).
