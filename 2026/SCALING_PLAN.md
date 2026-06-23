# Scaling the Reference-Deck Review to All Lectures

How to bring all 19 BIOS 667 reference decks (2026 traditional track; lecture numbers L01-L19; the old
combined L01 covering Ch. 1-2 was split into L01 (Ch. 1) and L02 (Ch. 2), so there are now 19 deck files) to the spec, keep them
consistent with one another, and catch cross-lecture problems. Decisions made by the PI: run the full
multi-perspective **panel on every lecture**, and **auto-run the cross-lecture sweep at every batch
boundary** (not only at the end).

## Three nested guards

Each guard catches a class of problem the others structurally cannot.

1. **Mechanical lint (free, all decks at once).** Deterministic invariants, enforced by grep before any
   agent runs: every deck renders notation via the appropriate shared include for what it has introduced
   (none for a Ch.1 intro deck, the lite `_notation_box_intro.qmd`, or the full `_notation_box.qmd`),
   never a hand-pasted table; YAML matches the standard; title style `BIOS 667 - Lecture N: Topic (Ch. N)`;
   no em-dashes or en-dashes; R is runnable and (for methods decks) a static SAS-equivalent slide is
   present; period dividers where the timing plan says multi-period; and the slide-density check
   (`slide_density_check.py`) has no unaddressed flags. Fix lint failures first; they cost nothing to find.
   **B2 additions to the mechanical lint (all grep-able, run on every deck):**
   - No 2027-track machinery in a reference deck: `grep -nEi 'AI-Augmented|AI-Aided|Exit Ticket|No Laptops|Tutor/Critic|first encounter'` returns nothing (those belong to the 2027 condensed track; L06 shipped with them and the single-deck panel did not flag it).
   - Every methods deck loads a REAL FLW dataset (not simulated-only): grep for a `read.table`/`read.csv` of a canonical file (`fev1`/`tlc`/`dental`/`epilepsy`/`rat`) with the download fallback; a deck whose only data is `rnorm`/`simulate`/`*-like` fails.
   - No stray "GLM" meaning the general linear model in a Ch. 3-6 deck (`grep -n 'GLM'`; should appear only where contrasted with the generalized linear model).
   - Subject count is $N$, not $n$ (FLW): `grep -nE 'i = 1, ?\\l?dots, ?n\b|\$n\$ subjects'` returns nothing.
   - YAML matches the standard header (theme `[default]`, author "Naim Rashid", standard footer/subtitle, `incremental: true`); diff each deck's YAML, do not assume.
   - AR(1) illustration uses $\rho = 0.8$ (ledger): grep the sim chunks for off-ledger `rho <- 0.5/0.6/0.75` without an in-deck justification.
   - No `{.panelset}`/`{.small}` notation/plot panels (anti-pattern: code in tiny tabs, plots land on
     separate untitled slides): `grep -nE '\.panelset|\{\.small\}'` returns nothing.
   - Every `ggplot` plot is self-identifying: it sets a `labs(title=...)` (note `labs()` often spans
     lines, so check for `title =` within the call, not just the first line) or a `facet_wrap` label; a
     model COMPARISON uses one faceted/labeled plot, not several untitled ones.
   - Diagnostic plots carry an interpretation on the SAME slide (plot `echo: false` inline + a
     `::: {.callout-note}` "reading rule"), not split across slides.
   - **Dataset-provenance + high-risk-phrase lint [2026-06-19 fidelity audit]:** `grep -nE` each deck for
     `illustrative|similar to Figure|the genuine|the real FLW|our running example|the chapter example`
     and method tokens `ddfm=kr|corCompSymm|bootstrap|poly\(|orthogonal poly|score test|MNAR|turning point`
     (the `-E` is required: bare `grep` treats `|` literally and matches nothing).
     A hit is not an auto-fail but forces a recorded decision: is the dataset FLW's actual example for this
     chapter (cite it) or a labeled substitution (per the ledger chapter->dataset map)? is the method the
     one FLW uses for this example, or flagged as a deviation? The dominant departure class was a dataset
     presented as canonical when it was an instructor substitution (L02 dental, L06 fev1.txt), sometimes
     cascading into a stated conclusion that contradicts FLW (L06: "quadratic needed" vs FLW "linear
     adequate"). For every LR/hypothesis test run on a real FLW dataset, confirm the verdict matches FLW's
     reported result; a dataset-mismatch that flips the headline conclusion is HIGH severity.
   - **Notation lint (FLW symbols, run on every deck) [2026-06-19 notation pass; source of truth
     `NOTATION_REFERENCE.md`, verified against the FLW PDFs].** FLW is the tie-breaker. grep each deck
     (prose AND code/figures/tables/captions) for canon violations, fix or record:
     - **Marginal covariance is $\Sigma_i$, NOT $V_i$.** `grep -nE '\\mathbf\{V\}_i|\$V_i'` returns nothing
       OUTSIDE the GEE decks (L12-L13). $\Sigma_i$ is canonical (FLW eq 4.2 / Ch. 7-8); bare $\Sigma$
       (subscript dropped) is fine, so `grep -nP '\\Sigma(?!_)'` is informational, not a failure.
     - **Random-effects covariance is $G$, NOT $D$;** residual is $R_i$. Do NOT rely on anchored greps for
       this (they miss `N\!\left(\mathbf{0}, D\right)`, `\hat D`/`\hat{D}`, `\phi(b; D)`, headings, ASCII
       diagrams, table cells, and `D_hat` code vars: those forms slipped the entire first pass and were only
       caught on review). Use a **permissive standalone-$D$ triage** and eyeball every hit:
       `grep -nP '(?<![A-Za-z_])D(?![A-Za-z_0-9])' <deck> | grep -vP 'deviance|D-optimal|\bD_i\b|D\^\\top'`.
       Every remaining hit must be either the random-effects covariance (-> `G`) or a declared non-covariance
       use (deviance `D` in a GLM deck, GEE derivative `D_i`); there is no third option. Scan prose, math,
       headings (`## ... D ...`), `labs()/ggtitle`, `fig-cap`/`tbl-cap`, markdown `| ... D ... |` cells, AND
       echoed R (`D <- ...`, `D_hat <-`, `Sigma = D`).
     - **$V_i$ is the GEE working covariance (L12-L13 ONLY):** $V_i = \mathbf{A}_i^{1/2}\operatorname{Corr}(\mathbf{Y}_i)\mathbf{A}_i^{1/2}$;
       there $\mathbf{D}_i = \partial\boldsymbol\mu_i/\partial\boldsymbol\beta$ is a derivative, not a covariance. Leave those.
     - **In code/figures/captions too:** `grep -nE 'Sigma *= *D|(^|[^_a-zA-Z])D *<- *(matrix|diag|MASS)|Sigma *<- *[0-9(]'`
       catches a random-effects covariance built as `D <- matrix(...)` and a residual variance named
       `Sigma <- ...` (both collide; use `G` and `sigma2`). L08's EBLUP sim shipped with both. Also scan
       plot `labs(title=)/ggtitle/main=/name=`, `fig-cap`/`tbl-cap`, and markdown `| $D$ |` table cells.
     - **No $\mathbf{D}\,\mathbf{R}\,\mathbf{D}$ split** (collides with $G$/$R_i$): write
       $\Sigma_i = \mathbf{S}\,\mathbf{C}\,\mathbf{S}$ ($\mathbf{S}$ = SD diagonal, $\mathbf{C}$ = correlation).
       grep `\\mathbf\{D\}.*\\mathbf\{R\}` / `D\s*R\s*D`.
     - **Row-form mean model.** `grep -nE 'beta\^(\\top|T|\{\\top\})\s*x'` returns nothing (write $X_{ij}\beta$);
       error term is $\varepsilon$ not $e_{ij}$ (`grep -nE 'e_\{?i?j'`); subject count is $N$.
     - **B1-B3 (L01-L09) migrated to FLW symbols 2026-06-19.** L14/L15 (B5) also migrated for corpus
       consistency; L10-L13/L16-L19 conform when their batches run. (L15 has a separate pre-existing
       `MASS::select` masking render bug at its prediction chunk, independent of notation, for the B5 pass.)
2. **Per-lecture review (panel for all).** Each deck gets the full four-role panel
   (`2026/workflows/lecture_review_panel.mjs`): UNC masters student (learnability) + Harvard FLW
   faculty (rigor/fidelity) in parallel, adjudicator (local + global change plan), consistency
   guardrail. Output is the deck's `<DECK>_reference_audit.md`. Propose-only; the PI approves changes.
   Gate 0 (clean `quarto render`) must pass before the panel runs.
   - **Gate 0b: narrative-vs-output verification (REQUIRED; B4 L10/codex lesson).** Independently RE-RUN
     the executed chunks and confirm every analysis-derived number and data-derived verdict on each slide
     matches the chunk's actual result on the actual dataset (this is what caught L10's "drifts off 1"
     variogram and "within bands" ACF claims, which the data did not support). Prefer inline R over
     hardcoded analysis numbers; grep each deck for hardcoded ORs/RRs/variance components and for pattern/
     verdict words ("rises", "flat", "drifts", "within bands", "adequate", "needed", "no `corAR1`") and
     check each against the output. This is a reviewer step you must do; the on-commit codex hook
     (`lecture-stat-review.sh` lens 4) only ATTEMPTS it best-effort (needs codex's flaky sandbox to run R;
     the claude fallback cannot), so a clean hook pass is not evidence the gate was checked. See
     `POST_LECTURE_REVIEW.md` Gate 0b.
3. **Cross-lecture sweep (per batch + final).** A separate workflow
   (`2026/workflows/cross_lecture_consistency.mjs`) that reads ACROSS the decks in a batch and checks
   what no single-deck review can see (see "Cross-lecture sweep" below). Auto-runs at each batch
   boundary and once globally over all 19 at the end.

## Batches (by concept cluster, dense-first within each)

Review in concept clusters so shared concepts and cross-references surface together. Order roughly
follows the course sequence; do the dense decks first within a batch (they need the most work and set
the conventions later decks inherit).

| Batch | Lectures | Cluster | Dense (panel-priority within batch) |
|---|---|---|---|
| B1 | L01, L02, L03 | Intro, basic concepts, linear models | L03 |
| B2 | L04, L05, L06 | Estimation, response profiles, curves | L05 |
| B3 | L07, L08, L09 | Covariance, LME, FE vs RE | L07, L08 |
| B4 | L10, L11, L12 | Diagnostics, GLM, marginal intro | L11 |
| B5 | L13, L14, L15, L16 | GEE, GLMM family, contrasting | L14, L16 |
| B6 | L17, L18, L19 | Missing data overview (Ch.17), missing data advanced/MI/weighting (Ch.18), transition models (instructor topic) | L17 |

Every deck in every batch still gets the full panel (per the PI decision); "dense" only sets the order
within a batch.

## Per-batch procedure

For each batch:

1. **Lint sweep** over the batch's decks (mechanical invariants); fix failures.
2. **Per-lecture panel** on each deck (Gate 0 render first). Apply approved LOCAL changes; collect
   proposed GLOBAL changes. Write each deck's audit.
   - **Corpus mining (B3 onward, PI directive 2026-06-18):** when authoring or repairing a deck, query
     the course corpus via the venv -- `find_examples` (mine the 2025 lectures / HW / SAS / R code for
     worked examples on the topic, to ADAPT rather than reinvent) and `find_datasets` (confirm the
     canonical dataset and which prior materials used it). Anchor new examples in the actual prior course,
     not just the textbook. Same venv pattern as `check_lecture_sync` (`CorpusQuery(store_dir="data")`).
   - **Book-departure scan (REQUIRED, PI directive 2026-06-19):** run the `POST_LECTURE_REVIEW.md`
     Dimension-A "book-departure scan" on every deck: classify each method/formula/diagnostic/claim as
     in-chapter vs beyond-chapter, require every beyond-FLW item to be flagged + cited or removed, and fix
     anything that contradicts the book or invents an alternative to the book's own method. Ground every
     check in THREE sources, not memory: (1) the RAG textbook (`search_all(source_type='textbook',
     chapter=N)`), (2) the chapter **PDF** in `book/` (read the actual table/figure for every numeric
     value and stated conclusion -- the RAG alone missed the L05 Table 5.6 and L06 conclusion errors), and
     (3) the **authors' BIO 226 slides** (`search_all(source_type='author_slides')`) for departures AND
     omissions vs the authors' own presentation. Also re-verify any constant/formula the deck takes from
     project `CLAUDE.md` against the PDF (CLAUDE.md is a fidelity source, not ground truth: `RE=2/(1+rho)`
     is only the n=2 case of the ANCOVA-vs-change efficiency `n/{1+(n-1)rho}`, the reciprocal of FLW eq 5.3
     `(1/n){1+(n-1)rho}`, not the general result). The reusable `book-fidelity-audit`
     workflow runs the textbook+PDF pass at scale; record confirmed departures in each deck's audit and
     recurring patterns in the ledger. (Motivating B2 catches: L02 dental and L06 fev1.txt as wrong-chapter
     datasets; L06's incorrect partial-residual diagnostic; the n-dependent RE.)
3. **Apply global changes once** (they affect the template/spec/notation/timing or all decks), following
   the consistency agent's companion-edit obligations, then record the decision in the ledger.
4. **Cross-lecture sweep** over the batch (auto): notation/terminology, cross-references, definitions,
   coverage, progression. Resolve findings; update the ledger.
5. **Re-render** every touched deck (Gate 0); run `slide_density_check.py` on each (it flags dense slides,
   prose-without-a-visual, AND empty slides from a `---` before a `# ` divider); re-grep for em/en-dashes.
6. **Visual step-through (every batch).** Open every deck in the batch in Chrome and step through the
   slides looking for visual problems: blank slides, content overflowing the frame, clipped tables,
   dense code, or broken math/layout. Fix what you find. This catches what a clean render does not (a
   deck can render exit 0 and still have a blank slide or an overflowing table).

Each batch conforms to the **consistency ledger** (`2026/CONSISTENCY_LEDGER.md`) established by prior
batches, so later batches inherit earlier decisions instead of relitigating them.

## Cross-lecture sweep (what the per-lecture panel cannot see)

`cross_lecture_consistency.mjs` fans out one agent per cross-cutting dimension, reading across the
batch's decks (grep-driven so it scales to all 19 at the end), then a synthesizer + the propose-only
consistency guardrail:

- **Notation and terminology:** the same symbol is used the same way everywhere (all via the shared
  include); preferred terms are consistent ("empirical BLUP", "invalid inference", covariance vs
  correlation).
- **Cross-reference integrity:** every "recall from Ch. X", "see Lecture Y", "we revisit in Ch. Z"
  resolves to content that actually exists in the named deck. Builds the reference graph; flags
  dangling or contradictory pointers.
- **Definitions:** no symbol or term is defined two different (or contradictory) ways across decks.
- **Coverage:** cumulative FLW coverage across the batch has no gap and no accidental double-coverage;
  maps each deck to its chapter(s).
- **Progression:** difficulty, length, and pacing progress sensibly and match `LECTURE_TIMING_PLAN.md`.

Output is a cross-lecture findings report plus proposed ledger updates (propose-only). Run it per batch
to catch drift early and cheaply, and once globally over all 19 decks at the very end as the final gate.

## Consistency mechanisms (how consistency is actually maintained)

- **Mechanical, not memory:** notation lives in one shared partial; the lint sweep enforces structure.
  This removes the largest source of drift without judgment calls.
- **Persistent ledger:** `2026/CONSISTENCY_LEDGER.md` records every cross-lecture decision (notation,
  terminology, dataset naming, the cross-reference map, global-change history) so decisions persist
  across batches and sessions. The per-lecture consistency agent's "global obligations" are written
  here, not left to evaporate.
- **Global changes are batch-atomic:** when a panel proposes a global change, apply it across all the
  files in its companion-edit set together (spec + review protocol; or notation master + partial +
  template), then log it in the ledger so every later deck conforms.

## Cost and cadence

The full panel is roughly 290K tokens / ~6 minutes per deck, so 19 panels plus the six per-batch sweeps
and one final sweep is a substantial but bounded spend, run batch by batch with PI approval between
batches. Because each batch commits before the next starts, the work is resumable and the exemplar
(L08) stays the reference other decks are aligned against.

## Gotchas (tooling and commits, learned in B1)

- **Workflow `args` arrives as a JSON STRING, not an object.** Parse it at the top of every workflow:
  `const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})`, then read `A.deckPath` etc.
  Forgetting this silently falls back to the script default (B1 wasted two full panel runs re-reviewing
  L08 before this was caught). Add a `log()` of the resolved target so a wrong-deck run is visible at once.
- **The RAG MCP is unreachable from headless workflow agents** (the panel faculty reports `rag_used=false`).
  Run the RAG fidelity check (`check_lecture_sync`) in the ORCHESTRATOR via the venv, not in the panel.
  Re-index (`rag/.venv/bin/bios667-index-corpus`) after editing a deck; a `covered=0` for a chapter is
  usually a chapter-tagging/stale-index artifact, not a true gap. Chapter-tag deck filenames (`_chN`).
  **Exact invocation (B2, works without re-indexing the edited deck):** from `rag/`,
  `CorpusQuery(store_dir="data")` (pass the STORE dir `data`, which contains `chroma/` -- passing the
  chroma dir or no dir raises `ValueError: CorpusQuery requires either store_dir or client`), then
  `q.check_lecture_sync("<path-to-deck.qmd>")` -- passing the deck PATH (not the chapter int) loads the
  CURRENT edited file, so you do not need to re-index after edits. Run it for every deck in the batch
  before commit. Gaps are usually artifacts: a near-threshold paraphrase the deck does cover, or a PDF
  download-watermark / formula-table fragment (eyeball the gap text to confirm; do not treat as missing
  coverage). B2: Ch.4 covered=6/gaps=0; Ch.5 covered=25/gaps=1 (empty-chunk artifact); Ch.6
  covered=13/gaps=2 (a "covariance postponed to Ch.7" transitional sentence + a Wiley watermark) -- all
  artifacts, batch is faithful.
- **Author slides are now indexed (2026-06-19)** as a distinct `source_type='author_slides'` (66 chunks
  from the FLW authors' BIO 226 slides, `bio226-slides-2007.pdf`, gitignored under `new/author_slides/`,
  outside the `rag/`-excluded tree). Query with `search_all(query, source_type='author_slides')` to check
  decks against the authors' own presentation for departures/omissions (the `metadata.py` classifier
  gained an `author_slides` rule). The B2 author-slides check corroborated the textbook audit and
  confirmed the L02 (TLC) and L06 (smoking-exposure groups) dataset fixes; the authors use unstructured
  covariance + REML for the Ch. 6 case study.
- **Commit hygiene after a split/rename.** Do NOT pass an already-`git rm`'d path to `git add`: a
  non-matching pathspec aborts the WHOLE `git add`, so the commit captured only the deletion and left the
  new files uncommitted (a broken HEAD). Stage the files that exist, and verify `git diff --cached --name-only`
  before committing.
- **The commit hooks fire on every commit and surface nits.** Batch related fixes into one cohesive commit
  rather than one-nit-per-commit, to avoid a long review/fix churn.
- **B4 process lessons (apply in B5):**
  - **Run on-demand codex reviews ONE AT A TIME.** Two concurrent `codex exec --sandbox read-only` runs
    trip the bwrap network-namespace setup (`bwrap: loopback: Failed RTM_NEWADDR`), so one silently dies;
    a single run (as for L10) initializes fine. The narrative-vs-output re-run (Gate 0b) is the reviewer's
    job regardless: if codex's sandbox cannot run R for a deck (it failed for L11 twice), do the chunk
    re-run yourself and verify the Case Study numbers against the slides (L11 verified by hand:
    epilepsy RR 0.82 / phi-hat 12.05, TLC OR 0.18/1.33, all inline-R).
  - **Inline-R the Case Study numbers from the start.** Decks that did this (L11, L12) passed
    narrative-vs-output trivially; the one that hardcoded an aspirational pattern (L10's variogram/ACF)
    needed a multi-round fix. Pull every OR/RR/variance-component/phi-hat from the fitted object via
    `` `r round(...)` ``.
  - **Keep `~ ... | id` formulas out of pipe-table cells** (CLAUDE.md pitfall 25): `\|` in a code span
    renders a literal backslash. Put exact `nlme`/`lme4` calls in speaker notes/callouts. B5's GEE/GLMM
    decision-tree tables are the high-risk spot.
  - **When a deck's period count changes, update EVERY timing location in ONE commit.** The L11 2->3
    reclassification cascaded into ~6 follow-up commits because the row, section subtotal, summary table,
    semester scenarios, week-by-week schedule, assessment due dates, dense-lectures list, AND CLAUDE.md's
    own timing table were updated piecemeal. Change them together and re-check the category subtotals sum
    to the TOTAL.
  - **Pre-register new cross-deck symbols before authoring.** A shared extension symbol (e.g. ordinal
    cutpoint $\kappa_k$ across L11/L12) must be decided and written into `NOTATION_REFERENCE.md` first, or
    the decks diverge (L11 $\alpha_k$ vs L12 $\theta_k$ until reconciled). Choose collision-free (avoid the
    GEE $\alpha$, natural-parameter $\theta$, $V_i$, etc.).
- **B5 process lessons (apply in B6):**
  - **Verify the STAGED diffstat before every commit; never trust that edits were staged.** The L15 rename
    bit us hard: `git mv old new` stages the rename, then we EDITED the renamed files, then ran a single
    `git add <new-paths> <stale-old-path>`. Because the stale `..._ch15.qmd` path no longer existed, the
    whole `git add` ABORTED ("did not match any files") and staged **nothing**, but the commit still
    succeeded, recording only the rename already staged by `git mv`, silently dropping all four content
    edits. The commit-review caught it ("similarity index 100%, 0 insertions"). Rule: after `git add`, run
    `git diff --cached --stat` and confirm it shows the CONTENT hunks you expect (not rename-only, not
    empty) BEFORE `git commit`. A failed/partial `git add` is a real failure even when a later `git commit`
    exits 0. B6 (L17 Ch.17 missing overview, L18 Ch.18 missing advanced/MI/weighting, L19 transition
    instructor topic) involves large multi-file edits plus a deck reorder where this is easy to repeat.
  - **The deck filename `_chNN` suffix tracks the FLW CHAPTER, not the course slot** (L13->`_ch13`,
    L14->`_ch14`; L15 random slopes are FLW Ch.14 so the deck is `BIOS667_L15_..._ch14.qmd`). When a course
    slot maps to a different FLW chapter than its lecture number, name/rename the deck AND all siblings
    together (`.qmd`, `_note.md`, `_reference_audit.md`, `.html`, `_files/`) and fix the chapter label
    INSIDE the audit header/Deck line and the note header/body (the L15 note had a factually wrong "Chapter
    15 ... random-slope covariance" claim; FLW Ch.15 is PQL/MQL). **B6 is the high-risk batch:** the course
    L17/L18/L19 labels do NOT track FLW's physical chapters (FLW Ch.18 = Missing-Data/MI, Ch.19 =
    Smoothing per the CLAUDE.md caveat), so decide each deck's FLW-chapter suffix up front.
  - **The closed-form attenuation constant is a LOGISTIC-link result.** When a Poisson/log-link deck
    previews or recalls $\beta^{\text{marg}}\approx\beta^{\text{cond}}/\sqrt{1+c_2^2\sigma_b^2}$, label it
    "logistic": the Poisson/log-link Jensen fan-out is real but adds THREE terms to the marginal log-mean
    ($E[\exp(b_0+b_1 t)] = \exp(\sigma_0^2/2 + \sigma_{01}t + \sigma_1^2 t^2/2)$: intercept shift, linear
    slope modification via the intercept-slope covariance $\sigma_{01}$, and a time-quadratic term), not a
    single slope-attenuation factor (Poisson random slopes are not attenuated this way). See CLAUDE.md Statistical Precision Standards (attenuation entry).
  - **codex rate-limit reality:** codex was unavailable for L14/L15/L16, so those got gate-battery +
    same-model (claude-fallback) commit reviews only. The fallback is a mechanical safety net (it DID catch
    the staging bug and stale labels), not an independent perspective. Re-run a real codex pass on the B5
    deck commits when the usage limit resets, and budget for codex being rate-limited during B6.

## Status

- Framework, per-lecture panel, and L08 exemplar: done.
- This plan, the cross-lecture sweep workflow, and the ledger: established here.
- **B1, B2, B3 complete.** **B4 (L10, L11, L12) complete** (2026-06-19): full-spec rebuilds, audits,
  cross-lecture sweep, framework guards, on-demand codex review of the deck commits (L10 had 2 real
  defects, fixed; L11/L12 verified). The whole corpus was migrated to FLW symbols ($\Sigma_i$/$G$/$R_i$;
  $V_i$ = GEE working cov) earlier in the same session.
- **B5 (L13, L14, L15, L16) complete** (2026-06-19): full-spec rebuilds committed one deck per commit
  with commit-hook reviews; FLW table values verified present in rendered HTML (narrative-vs-output).
  Cross-deck doc reconciliations: Zeger attenuation labeling unified ($c_2$=0.588 / $c_2^2$≈0.346),
  `exactRLRT`-Gaussian-only rule (GLMM -> parametric bootstrap), L15 relabeled Ch.15->Ch.14,
  L13 working-correlation aligned to L12 as $\operatorname{Corr}_i(\alpha)$. See ledger Batch log B5 +
  Global-change B5-G01..03. **codex caveat:** L14/L15/L16 got gate-battery + same-model (claude-fallback)
  commit reviews only because codex was rate-limited; re-run a real codex pass on the B5 commits when the
  limit resets.
- **B6 (L17, L18, L19) decks complete** (2026-06-19): PI-directed chapter-mapping REORDER first
  (FLW 2nd-ed Ch.17 = missing overview, Ch.18 = missing MI/weighting, Ch.19 = smoothing; no 2nd-ed
  transition chapter), so L17 = Ch.17, L18 = Ch.18 (was L19 advanced-missing), L19 = transition models
  (instructor topic, FLW 1st-ed Ch.10; renamed, no `_chNN`). Then full-spec rebuilds one deck per commit:
  L17 (LVCF formula, R_i indicator notation, real fev1 Case Study), L18 (render-fixed; IPW/weighted-GEE
  added as co-primary, real TLC MI Case Study, plus an INDEPENDENT subagent review that caught a [high]
  dplyr bug NA-ing the sensitivity analysis), L19 (beta_1=0 fix, instructor-extension provenance, row-form
  notation). Cross-refs repointed (HW6/Quiz6/student-review). All render exit 0; gate batteries clean.
  See ledger Batch log B6. **codex caveat:** codex was rate-limited for most B6 commits (resets
  ~2026-06-24); re-run a real codex pass on the B6 commits when the limit resets.
- **Final global cross-lecture sweep COMPLETE** (2026-06-19): the worry was that early decks (B1-B3)
  missed standards codified in later batches. (1) MECHANICAL LINT across all 19 decks: em/en-dashes, the
  section symbol, forbidden 2027-track machinery, pipe-in-table backslash, retired notation
  ($V_i$-for-Gaussian, $D$-for-RE, $R(\alpha)$), YAML conformance, and `incremental` were ALL clean
  corpus-wide (the migration and style rules did propagate); the one real hit was L13 with 7 blank slides
  (pitfall #1, missed in its B5 rebuild) - fixed. (2) SEMANTIC BACKPORT AUDIT of L01-L12 via 4 parallel
  subagents that RE-RAN the chunks: notation migration, book-fidelity, and beyond-FLW flagging were fully
  back-ported (L05/L06/L09/L10/L12 clean on every dimension). Real gaps found and fixed: L01 naive-vs-
  cluster SE demo drew the OPPOSITE of its claim (DGP redesigned, naive<cluster verified); L08 (exemplar)
  carried the BLUP-QQ-normality caution-reversal (FLW p.273; the L10-rebuild lesson never backported);
  L03 had no real Case Study (added TLC placebo); L04/L11 stale missing-data pointers (post-reorder);
  L02 adjacency wording; L07 `form=` naming; assorted inline-R / #24d note fixes. All re-run numbers now
  match the slides. **codex caveat:** codex was rate-limited throughout (resets ~2026-06-24); sweep fixes
  got gate-battery + same-model commit reviews; re-run a real codex pass on the B5/B6 + sweep commits when
  the limit resets.
- Remaining: only the deferred real-codex re-run on the B5 + B6 + global-sweep deck commits (codex
  resets ~2026-06-24). All 19 reference decks are now lint-clean, render exit 0, and standards-aligned.
