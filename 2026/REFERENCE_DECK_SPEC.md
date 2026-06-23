# BIOS 667 Reference Deck Specification (2026 traditional track)

**Date:** 2026-06-17
**Track:** 2026 reference decks (traditional). Taught by David Zhang in Fall 2026, assessed with
traditional homework and a final project (as in 2025).
**Not this track:** the 2027 condensed AI decks + in-class oral/unplugged H/P/L/F assessment
(those live in `2026/pedagogy/` and the v2 template / exemplars, and are derived FROM these
reference decks later).

## Purpose

A reference deck is the **complete, book-faithful, lecture-only teaching deck** for a chapter:
the depth and length of the prior (2025) lecture-only course, polished and verified. It is what a
substitute instructor teaches from, start to finish, with no in-class evaluation machinery.

## Requirements (every reference deck must meet these)

1. **Book-accurate.** Every definition, formula, and claim verified against Fitzmaurice, Laird &
   Ware (2011). Use the textbook corpus (`rag/data/chroma`, `source_type=textbook`) and the
   physical FLW table of contents. Honor the project's statistical-precision standards (e.g.
   Zeger attenuation c approx 0.346; "invalid inference" not "biased SEs"; `re.form=NA` is not a
   marginal mean; REML for variance components, ML for LRT of fixed effects; boundary/mixture
   caveat for variance-component tests). A deck must not recommend output the shown package cannot
   produce: if it recommends Kenward-Roger or Satterthwaite degrees of freedom, it must state that
   `nlme::lme` provides neither (it reports containment df) and that they require `lme4` + `lmerTest`
   or `pbkrtest`. Any material that goes **beyond the FLW chapter** (an instructor extension, e.g.
   Lord's paradox in Ch. 5) must be flagged as such and carry an external citation, so a substitute
   can tell chapter content from enrichment.
2. **Complete.** Covers the chapter's key sections and concepts (map deck sections to the FLW
   chapter outline; no major section unaddressed).
3. **Multi-period with explicit markers.** Classes are **75 minutes** (roughly 25-40 content
   slides each, at about 2-3 minutes per technical slide). A lecture longer than one period stays
   **one deck delivered across multiple periods** (not a separate file, and not compressed into one
   class): it carries explicit period dividers
   (`# Part I (Day 1): ...`, `# Part II (Day 2): ...`) at natural conceptual seams (FLW section
   boundaries), each Part a self-contained 75-minute teaching block. Per-lecture period counts and
   slide tallies are in `LECTURE_TIMING_PLAN.md` (e.g. L08's 77 slides -> 2 classes). If editing a
   deck pushes it past a 75-minute block, add a divider and reflow rather than cramming.
4. **Good coding examples.** Runnable R on real FLW datasets (dental/Orthodont, TLC, epilepsy,
   fev1, rat, ...), code on one slide and output on the next (`#| output-location: slide`), with
   interpretation in context. Prefer `nlme`/`lme4`/`geepack`/`emmeans` per the course stack. A shared
   control/options object reused across many fits (e.g. an `nlme` `lmeControl` object) must be
   explained once at its first appearance, and any setting that can mask failure (e.g.
   `returnObject=TRUE`, which returns a fit even if it did not converge) must be flagged, so a student
   lifting a single fit is not stranded.
5. **Template conventions.** The CLAUDE.md YAML header standard; opening Objectives + Roadmap;
   concept -> worked example -> diagnostics -> summary/recipe flow; consistent notation
   (`Y_{ij}`, `X_i`, `Z_i`, `D`/`G`, `V_i = Z_i D Z_i' + R_i`, etc.); callouts (note/warning/tip);
   cross-references ("recall Ch. X", "we revisit in Ch. Y"); no em-dashes (use hyphens/colons).
   Title style matching the existing decks: `BIOS 667 - Lecture N: Topic (Ch. N)`.
6. **No in-class evaluation segments.** Reference decks do NOT include the graded oral retrieval
   warm-up, the oral exit check, AI-augmented-practice-as-assessment, the "walk me through"
   defense, or AI-mode (Tutor/Critic) gating. Those belong to the 2027 condensed track.
   - **Allowed and encouraged (traditional, non-graded):** "Check Your Understanding" boxes,
     in-class worked exercises, discussion prompts. These are pedagogy, not the evaluation system.
   - **Decision (flip if desired):** the productive-failure "designed first encounter" is NOT
     used in reference decks (it is an active-learning move reserved for the 2027 condensed decks).
     Reference decks open traditionally (motivation -> objectives -> concept).

## Relationship to the 2027 condensed deck

The reference deck is the **canonical source**. The 2027 condensed AI deck is a derived *subset*:
pick the topics to cover live, then wrap them in the v2 active-learning arc (retrieval, first
encounter, oral exit check, Tutor/Critic AI practice). Keeping the reference deck complete means
the condensed deck can always point back to it for depth, and David's traditional course and your
2027 AI course share one accurate, book-checked content base.

## Deck tiers (graduated scaffolding)

Not every lecture carries the same weight; apply the bar by tier.

- **Methods decks** (most lectures, e.g. L05-L19): the full spec, including a Case Study on a real FLW
  dataset, a static SAS-equivalent slide, per-slide instructor notes, period dividers when multi-period,
  and Further Reading.
- **Intro / overview decks** (e.g. L01, L03): a reduced bar. REQUIRED: objectives, a prerequisites/recall
  slide, the notation include (the LITE `_notation_box_intro.qmd` until random effects and GEE are
  introduced, then the full `_notation_box.qmd`), per-slide instructor notes on the key concept/example
  slides, clean runnable R, and a summary. OPTIONAL (only when they fit): a real-data Case Study and a
  static SAS slide are NOT required when the lecture is conceptual (fits no model), and period dividers are
  NOT required for a single-period deck. Do not bolt an artificial model fit or PROC onto a concepts
  lecture just to satisfy the checklist.

When in doubt, treat a deck as a methods deck. The QA-checklist items for Case Study / SAS slide /
period dividers are waivable for an intro/overview deck with a one-line note in its audit explaining why.

## Detail level: teachable cold

Because David teaches these without having written them, the bar is **"a competent substitute can
teach it with one read-through."** That means more *instructor scaffolding* than slides for your
own use, concentrated in (not more body text):

- **Per-slide instructor notes** via Quarto `::: {.notes}` (visible in presenter view, press S):
  what to say, what to emphasize, the common student error, the transition. This is the single
  highest-leverage handoff element; expected on concept, worked-example, and diagnostic slides.
- **Per-Part timing cues** (minutes per block) so 2-3 periods can be paced.
- **Prerequisites / recall** opening slide, and a **recap** opening each later Part.
- A **notation reference** box, included from the shared canonical partial
  (`{{< include _notation_box.qmd >}}`; master `2026/NOTATION_REFERENCE.md`), so every deck shows
  identical, FLW-aligned notation. Add lecture-specific symbols on a small slide after the include.
- **Anticipated questions / common misconceptions** (a "Common Pitfalls/Gotchas" slide counts).
- An explicit **Case Study** on real FLW data (matches the FLW "Case Studies" section), distinct
  from a small illustrative example.
- **Datasets used + how to load** (download fallback) and a **package list** (reproducible cold).
- **Computing in R and SAS.** R is the runnable language (shown in lectures and used in homework,
  as in 2025); ALSO include one **static, non-runnable SAS-equivalent** slide, which must be a
  **complete standalone program** (e.g. a full `PROC MIXED` block with `CLASS`, `MODEL`, and
  `REPEATED`/`RANDOM` statements), not a fragmentary cheat-sheet table. A SAS-to-R translation table is
  fine as an *additional* aid but does not satisfy this item. Shown for reference only. This mirrors
  FLW's "Computing" section (8.9 for Ch. 8) and 2025 practice.
- **Objectives -> assessment mapping** (which HW / final-project skill the lecture sets up).
- **Further reading / references** (the FLW "Further Reading" section + key citations).

It does NOT need a verbatim script (notes are bullet cues), nor theory beyond the chapter.

### Writing voice (slides must not read as AI-generated)

- NO em-dashes anywhere (use a period, comma, or parentheses); NO semicolons unless they truly join
  two independent clauses (prefer two short sentences).
- Avoid AI-tells: "delve", "leverage" (verb), "it's worth noting", "a powerful tool", "in the world
  of", stacked hedges. Write plainly, the way the topic would be said aloud to the class.
- Short declarative sentences, one idea per bullet, concrete over abstract.

## Per-deck QA checklist

- [ ] YAML matches the standard; title `BIOS 667 - Lecture N: Topic (Ch. N)`; no em-dashes.
- [ ] **Human voice:** no em-dashes, no gratuitous semicolons, no AI-tell phrasing (reads like the
      instructor talking, not generated prose).
- [ ] Objectives + Roadmap open the deck; **objectives mapped to the HW/final-project skills**.
- [ ] **Prerequisites/recall** slide up front; **recap** opening each later Part.
- [ ] Deck sections cover the FLW chapter outline (completeness); no major gap.
- [ ] Every formula/claim book-accurate; statistical-precision standards honored.
- [ ] **Notation reference** slide present via `{{< include _notation_box.qmd >}}` (the shared
      canonical box; master is `2026/NOTATION_REFERENCE.md`), not a hand-pasted per-deck table;
      consistent notation; callouts and cross-references used. If the chapter reuses a non-reserved
      symbol with a chapter-local meaning (e.g. FLW Ch. 5 `n` = occasions, `N` = subjects), it is
      declared up front on a lecture-specific slide after the include (reserved `X/beta`, `Z/b` never
      reassigned). "GLM" is used only for the **generalized** linear model (Ch. 11+); the general
      (normal) linear model is "LM".
- [ ] At least one full **Case Study** worked example on a real FLW dataset; all R chunks run;
      output on its own slide; interpretation present; **datasets-to-load + package list** stated.
- [ ] R code is runnable; a **static SAS-equivalent** slide is included (not executed) and is a
      **complete standalone program** (full `PROC MIXED` block, not a cheat-sheet fragment table).
- [ ] Any **beyond-FLW** extension is flagged as such and carries an external citation.
- [ ] Diagnostics shown with a **per-slide reading rule on EACH diagnostic plot** (the good vs
      problematic pattern, and what each reference line means), per the CLAUDE.md "annotate diagnostic
      plots" guideline (not just one general annotation somewhere in the deck).
- [ ] No deck recommends output the shown package cannot produce (e.g. KR/Satterthwaite df with an
      `nlme`-only workflow) without stating the limitation and the package that would provide it.
- [ ] Reused control/options objects are explained at first use; failure-masking settings flagged.
- [ ] **Common pitfalls / misconceptions** slide present.
- [ ] **Per-slide instructor `::: {.notes}`** on the key concept/example/diagnostic slides.
- [ ] Period dividers + **per-Part timing cues** if the lecture spans 2-3 periods.
- [ ] No graded/oral/AI-evaluation segments (traditional non-graded checks are fine).
- [ ] Summary/takeaways, a recipe-card or reporting checklist, and **Further Reading** near the end.

## Post-creation review

The checklist above is the bar; `2026/POST_LECTURE_REVIEW.md` is the **repeatable pass that exercises
it** after a deck is drafted or substantially edited. It walks four substantive dimensions (reflects
the book; correct expression and notation; examples correct and on-point; R code informative for
common and unique tasks) plus render and pacing gates, and it produces a dated per-deck audit file
`2026/lectures/<DECK>_reference_audit.md`. A deck is not "done" until that audit exists and its verdict
is "meets spec." Run it by hand or hand the deck to Claude with "review against POST_LECTURE_REVIEW.md."

## Exemplar

`2026/lectures/BIOS667_L08_Covariance_ch8_LME.qmd` is the worked exemplar of this spec (see its
period dividers and the L08 audit note). `BIOS667_L08_reference_audit.md` is the worked example of a
post-creation audit. Use both as the model when aligning the other lectures.

## Scaling

Most 2026 lectures are already comprehensive; aligning them is QA + period markers + book-check,
not a rewrite. Order suggestion: do the dense/key chapters first (L05, L07, L08, L11, L13, L14,
L17), since those most need clean period seams and book verification.
