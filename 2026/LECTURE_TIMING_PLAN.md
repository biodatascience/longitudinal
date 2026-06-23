# BIOS 667 Lecture Timing Plan (2026)

## Overview

- **Class period:** 75 minutes
- **Pacing assumption:** 2-3 minutes per slide (technical biostatistics with code)
- **Optimal single class:** 25-40 slides
- **Lectures are not split** - longer lectures simply fill multiple class periods

---

## Lecture Schedule by Class Count

### Single Class (1 period each)

| Lecture | Topic | Slides | Est. Time |
|---------|-------|--------|-----------|
| L01 | Introduction to Longitudinal Data (Ch. 1) | 17 | 34-51 min |
| L02 | Longitudinal Data: Basic Concepts (Ch. 2) | 24 | 48-72 min |

**Subtotal: 2 class periods** (the old combined L01 was split into L01 Ch.1 + L02 Ch.2)

> **B4 reclassification (2026-06-19).** After the B4 full-spec rebuild the category placements below
> changed for three decks (see the row notes): **L10** -> a firm 2 periods (was flexible 1.5);
> **L11** -> ~3 periods (was 2; +2 real case studies + beyond-FLW flags + SAS + scaffolding, ~110
> rendered slides); **L12** -> ~1.5 periods (was single-class; epilepsy GEE Case Study added). Net total
> shifts to ~36 periods (B4 added ~2: L10 +0.5, L11 +1, L12 +0.5). The L11/L12 rows still appear under their old headings below with notes.

---

### Flexible (1-2 periods each)

| Lecture | Topic | Slides | Est. Time | Recommendation |
|---------|-------|--------|-----------|----------------|
| L03 | Linear Models Overview (Ch. 3) | 52 | 104-156 min | 2 if discussion desired |
| L09 | FE vs RE (Ch. 9) | 31 | 62-93 min | 1 period (rebalanced to FLW-primary; econometrics as a flagged supplement) |
| L10 | Residual Diagnostics (Ch. 10) | ~58 (rendered: 52 `##` + 6 output-location slides) | 116-174 min | 2 periods (B4 rebuild: transformed residuals + Mahalanobis + dental Case Study) |
| L12 | Marginal Models Introduction (Ch. 12) | ~48 (rendered) | 96-144 min | ~1.5 periods after B4 (epilepsy GEE Case Study added; moved here from single-class) |

**Subtotal: ~6 class periods (L03 1-2, L09 1, L10 2, L12 1.5)**

---

### Two Classes (2 periods each)

| Lecture | Topic | Slides | Est. Time | Density |
|---------|-------|--------|-----------|---------|
| L04 | Estimation & Inference (Ch. 4) | 68 | 136-204 min | Standard |
| L05 | Response Profiles (Ch. 5) | 75 | 150-225 min | Standard |
| L06 | Parametric Curves (Ch. 6) | 52 | 104-156 min | Flexible (1.5-2) |
| L07 | Covariance Structures (Ch. 7) | 73 | 146-219 min | Standard |
| L08 | Linear Mixed Effects (Ch. 8) | 72 | 144-216 min | Standard (still 2 periods) |
| L11 | GLMs Review (Ch. 11) | ~99-110 (rendered: 66 `##` + 8 Part dividers + ~25 output-location slides) | 200-300 min | Dense (now ~3 periods after B4: 2 real case studies + beyond-FLW flags + SAS + scaffolding) |
| L13 | GEE Extensions (Ch. 13) | 76 | 152-228 min | Standard |
| L14 | GLMMs (Ch. 14) | 82 | 164-246 min | Dense |
| L15 | GLMM Random Slopes (Ch. 14; course slot "Lecture 15") | 77 | 154-231 min | Standard |
| L16 | Contrasting Models (Ch. 16) | 83 | 166-249 min | Dense |
| L18 | Missing Data: MI/Weighting/Pattern-Mixture (Ch. 18; B6 reorder, was L19) | 83 | 166-249 min | Dense |
| L19 | Transition (Markov) Models (instructor topic, FLW 1st-ed Ch.10; B6 reorder, was L18) | 68 | 136-204 min | Standard |

**Subtotal: 22 class periods** (L11 moved to the three-class group after the B4 rebuild; its row above is annotated)

> **Redundancy-vs-budget note (from the L08 panel review).** L08's Part II is back-loaded with
> list-only slides that repeat the ML-vs-REML rule and the "add AR(1) only if random slopes do not
> absorb the correlation" point several times. Consolidating those to one canonical statement plus
> cross-references frees slide budget to add the two short implied-covariance derivations (the CS
> off-diagonal and the random-slope fan-out variance) without exceeding the 2-period allocation: the
> swap is net-neutral, so L08 stays at 2 periods. Run the same redundancy-vs-budget check on the other
> dense decks (L11, L14, L16) before adding content to them.

---

### Three Classes (3 periods)

| Lecture | Topic | Slides | Est. Time | Notes |
|---------|-------|--------|-----------|-------|
| L11 | GLMs Review (Ch. 11) | ~99-110 (rendered) | 200-300 min | Promoted from 2 periods after the B4 rebuild; row also appears under Two Classes with a note |
| L17 | Missing Data (Ch. 17) | 128 | 256-384 min | Comprehensive coverage |

**Subtotal: 6 class periods**

---

## Total Class Periods Summary

| Category | Lectures | Class Periods |
|----------|----------|---------------|
| Single class | L01, L02 | 2 |
| Flexible | L03, L09, L10 (firm 2), L12 (~1.5) | ~6 (estimated) |
| Two classes | 11 lectures (L11 moved to three) | 22 |
| Three classes | L11, L17 | 6 |
| **TOTAL** | **19 lectures** | **~36 class periods** |

*(B4 reclassification 2026-06-19: L10 1.5->2, L11 2->3, L12 single->1.5; see the row notes and the B4 banner above.)*

---

## Semester Planning

### Assuming 2 classes per week (30 weeks = 60 classes)

- Lecture delivery: ~36 classes (B4 rebuild added ~2: L10 +0.5, L11 +1, L12 +0.5)
- Remaining for exams, review, holidays: ~24 classes

### Assuming 3 classes per week (15 weeks = 45 classes)

- Lecture delivery: ~36 classes
- Remaining for exams, review, holidays: ~9 classes

---

## Week-by-Week Draft Schedule

| Week | Classes | Lectures Covered | Notes |
|------|---------|------------------|-------|
| 1 | 2 | L01 (1) + L03 start | Intro + Linear models |
| 2 | 2 | L03 end + L04 (1) | |
| 3 | 2 | L04 (2) + L05 (1) | Estimation, Response profiles |
| 4 | 2 | L05 (2) + L06 (1) | |
| 5 | 2 | L06 (2) + L07 (1) | Parametric curves, Covariance |
| 6 | 2 | L07 (2) + L08 (1) | |
| 7 | 2 | L08 (2) + L09 | LME, FE vs RE |
| 8 | 2 | L10 (1-2) | Diagnostics (now a firm 2 periods after B4) |
| 9 | 2 | L11 (1-2) | GLMs (now ~3 periods after B4) |
| 10 | 2 | L11 (3) + L12 (1) | GLMs finish, Marginal intro |
| 11 | 2 | L12 (2, ~half) + L13 (1) | Marginal intro finish, GEE extensions |
| 12 | 2 | L13 (2) + L14 (1) | GEE, GLMMs |
| 13 | 2 | L14 (2) + L15 (1) | GLMMs, random slopes |
| 14 | 2 | L15 (2) + L16 (1) | Random slopes, Contrasting models |
| 15 | 2 | L16 (2) + L17 (1) | Contrasting models, Missing data |
| 16 | 3 | L17 (2-3) + L18 (1) | Missing data overview, Missing data advanced (MI/IPW) |
| 17 | 2 | L18 (2) + L19 (1) | Missing data advanced, Transition models |
| 18 | 2 | L19 (2) + Review | Transition models, review |
| 19 | - | Review/Exam | |

> **B4 reflow note.** The B4 rebuild added ~2 class periods (L10 1.5->2, L11 2->3, L12 1->1.5), so the
> back half shifts ~1.5-2 weeks later than the pre-B4 draft; the semester now needs ~18 teaching weeks
> (mostly 2 classes/week, with one 3-class week for L17) rather than ~16. Treat the week numbers above as a draft to re-fit to the actual
> academic calendar.

---

## Dense Lectures (May Need Extra Time)

These lectures have 80+ slides and high content density:

1. **L11 (GLMs)** - ~99-110 rendered slides (66 `##` + 8 Part dividers + ~25 output-location slides) - GLM foundations review; now ~3 periods after the B4 rebuild
2. **L14 (GLMMs)** - 82 slides - Core GLMM material
3. **L16 (Contrasting Models)** - 83 slides - Comprehensive comparison
4. **L17 (Missing Data overview)** - 128 slides - Most comprehensive lecture
5. **L18 (Missing Data advanced: MI/weighting/pattern-mixture)** - 83 slides - B6 reorder, was L19

**Recommendation:** Build in 5-10 min buffer or plan Q&A sessions after these lectures.

---

## Homework & Quiz Timing

| Assessment | Covers | Suggested Due |
|------------|--------|---------------|
| HW1 | L01-L03 | End of Week 2 |
| Quiz 1 | L01-L03 | Week 2 |
| HW2 | L04-L06 | End of Week 5 |
| Quiz 2 | L04-L06 | Week 5 |
| HW3 | L07-L09 | End of Week 7 |
| Quiz 3 | L07-L09 | Week 7 |
| HW4 | L10-L13 | End of Week 12 |
| Quiz 4 | L10-L13 | Week 12 |
| HW5 | L14-L16 | End of Week 15 |
| Quiz 5 | L14-L16 | Week 15 |
| HW6 | L17-L19 | End of Week 18 |
| Quiz 6 | L17-L19 | Week 18 |

---

*Generated: January 2026*
