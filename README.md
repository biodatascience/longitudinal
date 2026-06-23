# BIOS 667 - Applied Longitudinal Data Analysis

Course website and source for **BIOS 667** (UNC Gillings School of Global Public Health),
based on Fitzmaurice, Laird & Ware (2011), *Applied Longitudinal Analysis* (2nd ed.).

- **Live site:** https://biodatascience.github.io/longitudinal
- **Source (this repo, `main` branch):** Quarto `.qmd` for 19 lecture decks, 6 homeworks, 6 quizzes
- **Rendered site (`gh-pages` branch):** built by `quarto publish gh-pages`

This repo is **student-facing**: it contains lectures, homework, and quiz prompts, but **no answer
keys**. Solution keys (homework and quiz) live in the separate private repo
**`biodatascience/longitudinal_key`**.

---

## 1. Layout

```
_quarto.yml                     website config (renders index + lectures + homework + quizzes)
index.qmd                       the schedule / landing page
2026/lectures/   BIOS667_L01..L19_*.qmd   19 reference decks (RevealJS) + _notation_box includes
2026/homework/   HW{1..6}.qmd              student homework (no solutions)
2026/quizzes/    Quiz{1..6}.qmd            student quizzes (no answer keys)
2026/handouts/                            supplementary handouts
data/                                     all datasets the materials load (committed; no download needed)
figs/ , unc-gillings.css                  render dependencies
2026/setup.R , 2026/DESCRIPTION           R package install + dependency list
2026/NOTATION_REFERENCE.md                the notation canon all decks follow
2026/LECTURE_TIMING_PLAN.md               per-deck class-period counts
2026/DELIVERY_NOTES.md                    read before teaching (presenting, distributing, offline math)
CLAUDE.md                                 full authoring + statistical conventions
```

The decks load data with `../../data/<file>` (the committed copies), so a clone renders with **no
internet dependency**. Each loader still keeps a download-fallback to the FLW site as a secondary path.

## 2. Prerequisites (once)

- **R** >= 4.5 (tested on 4.5.1 / 4.6.0): https://cloud.r-project.org
- **Quarto** >= 1.5 (tested on 1.8): https://quarto.org/docs/get-started/ (bundles Pandoc; pulls
  LaTeX and a headless Chrome on first use)

```bash
quarto check          # Quarto, Pandoc, LaTeX, Chrome, R/knitr engine should all report OK
Rscript 2026/setup.R  # installs only the missing R packages (full list in 2026/DESCRIPTION)
```

A missing R package is the most common render failure, so run `setup.R` before anything else.

## 3. Build the site locally

```bash
quarto preview        # live preview with auto-reload (opens the schedule page)
quarto render         # build the whole site into _site/
```

To render a single file while authoring:

```bash
quarto render 2026/lectures/BIOS667_L08_Covariance_ch8_LME.qmd
quarto render 2026/homework/HW1.qmd
```

First renders are slower (package load + a few slow models, e.g. HW5's bootstrap, L17's 128 slides).

## 4. Publish to GitHub Pages

The site is served from the `gh-pages` branch. After changes to `main`:

```bash
quarto publish gh-pages
```

This renders the site and pushes the result to `gh-pages` (Quarto manages that branch for you). Source
stays on `main`; you never edit `gh-pages` by hand. In the repo's **Settings -> Pages**, set the source
to the `gh-pages` branch (root) once.

## 5. Solution keys (separate private repo)

Homework and quiz answer keys are **not** in this repo. They live in
**`biodatascience/longitudinal_key`** (private), one file per assignment
(`HW{N}_solution.qmd`, `Quiz{N}_solution.qmd`). Keep that repo private and out of anything shared with
students. The student prompts here and the keys there share the same structure, so a key renders against
the same `data/` copies.

## 6. Before you teach

Read `2026/DELIVERY_NOTES.md`. Key points:

- **Equations load their math library from a CDN.** With room WiFi this is invisible. For a no-internet
  room, open the rendered `.html` once while online (the browser caches the math), then it renders offline.
- **Present from the published / pre-rendered `.html`**, do not re-render live.
- **Due dates** in the homework say "See Canvas" - set the real dates in Canvas.
- All reported numbers are inline-R (recomputed at render), so prose never drifts; but `set.seed(667)`
  output can shift slightly across package versions - read numbers off the current render, not memory.
