# BIOS 667 (2026) Delivery Notes

Operational checklist for actually USING the materials: presenting lectures, distributing homework,
and running quizzes. (Content was reviewed separately; this is about delivery.) Target: R 4.5.1,
Quarto >= 1.5.

## One-time setup (before rendering anything)

- **Install all R packages:** `Rscript 2026/setup.R` (installs only what is missing). The full list is
  in `2026/DESCRIPTION` (33 CRAN packages: lme4, nlme, geepack, glmmTMB, mice, emmeans, pbkrtest,
  clubSandwich, plm, multgee, RLRsim, ...). A missing package is the most common render failure on a
  fresh machine.
- **Datasets are committed** in `data/` (dental, epilepsy, fev1, tlc, cholesterol, cd4, toenail,
  birthwt, ...), so renders do NOT depend on the FLW website being up. Each loader still has a
  download-fallback to `content.sph.harvard.edu/fitzmaur/ala2e/` as a secondary path.

## Equations need internet to render (the one real gotcha)

The rendered HTML loads its math library (MathJax/KaTeX) **from a CDN** even with
`embed-resources: true`. Quarto does not cleanly self-contain math for RevealJS (and only partially
for plain HTML), so the materials are NOT shipped with bundled math. Practical consequence and the
reliable workaround:

- **With internet in the room (the normal case): nothing to do** - equations render fine.
- **For a no-internet classroom:** open the rendered HTML **once while online** before going offline.
  The browser caches the math library for that session/device, and equations then render with no
  network. Do this on the actual presentation laptop before class.
- Do not re-render a deck live in a room with no internet expecting math to appear in a fresh browser.

## Lectures

- **Present from the PRE-RENDERED `.html`**, not by re-rendering live. Some decks take minutes
  (L11 ~110 slides, L17 128 slides) and a few run R that is slow on first render.
- **Multi-period decks:** L11 (~3 classes), L17 (3 classes), and the dense 2-class decks - see
  `2026/LECTURE_TIMING_PLAN.md` for per-deck period counts before you schedule.
- Each `.html` is otherwise self-contained (`embed-resources`), so a single file is portable (subject
  to the math-CDN note above).
- **Reproducibility:** all reported numbers are inline-R (recomputed at render), so prose never drifts.
  But `set.seed(667)` output can shift slightly across R / lme4 / mice versions - do not quote a number
  from memory; read it off the current render.

## Homework

- **`HW{N}.qmd` = student version; `HW{N}_solution.qmd` = instructor key.** They live in the same
  folder - **keep the `_solution.*` files (and any rendered solution HTML) out of anything you share
  with students.** Distribute only `HW{N}.qmd` (or its rendered student HTML).
- **Due dates:** the files say "See Canvas" - set the actual dates in Canvas.
- **Student environment:** students need the same packages (`2026/setup.R`) and, ideally, the repo's
  `data/` folder. HW5's parametric bootstrap and HW3's CD4 fit (5035 rows) can take a minute or two on
  a weak laptop - this is expected, not a hang.

## Quizzes

- **`Quiz{N}.qmd` = student version (NO answer key)** - safe to distribute or print/project.
  **`Quiz{N}_solution.qmd` = instructor version (with the answer key).** Previously the key was in the
  student file behind a one-click collapse; it is now split, so students cannot reveal it.
- Format: 5 questions, ~5-7 minutes, in-class (doubles as attendance). Calculator policy is now
  consistent across all six ("basic calculator permitted; formulas provided where needed").
- If printing, print from a browser that has already loaded the math (see the equations note) so the
  formulas (attenuation, Rubin's T, transition logit) render before printing.

## Still outstanding

- **Independent codex review pass** on the recent commits (codex was rate-limited all session; resets
  ~2026-06-24). See `2026/SCALING_PLAN.md` / `CONSISTENCY_LEDGER.md`.
