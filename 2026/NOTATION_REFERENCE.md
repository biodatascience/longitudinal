# BIOS 667 Notation Reference (canonical)

**Purpose.** One source of truth for notation across all BIOS 667 lectures, homework, and quizzes,
aligned to Fitzmaurice, Laird & Ware (2011), *Applied Longitudinal Analysis* (FLW). Lectures render
the per-slide notation box from the shared partial `2026/lectures/_notation_box.qmd`
(`{{< include _notation_box.qmd >}}`); this document is the human-readable master that the partial
mirrors. If a symbol is added or changed, edit it **here and in the partial together**.

**Convention.** Bold = vector or matrix; plain = scalar or index. No em-dashes anywhere.

**Reserved symbols (no collision).** $\mathbf{X}_i$ / $\boldsymbol\beta$ are the fixed-effect design
and coefficients; $\mathbf{Z}_i$ / $\mathbf{b}_i$ are reserved for the random-effect design and random
effects and must NEVER denote a fixed covariate. A deck must not introduce an inline equation symbol
that collides with a reserved canonical symbol (for example, do not write a fixed covariate as
$z_{ij}$). Lecture-specific symbols go on a small slide AFTER the `{{< include _notation_box.qmd >}}`,
never by editing the shared partial.

**Book first.** Keep notation as consistent with FLW as possible across all lectures; FLW is the
tie-breaker whenever a course habit and the book differ (confirmed by PI 2026-06-18). The $N$ = subjects,
$n_i$/$n$ = occasions convention above IS the FLW convention.

**Reused-symbol override (non-reserved symbols only).** Some chapters follow FLW in giving a
non-reserved symbol a chapter-local meaning (e.g. FLW Ch. 5 response profiles uses $G$ for the number of
groups, which would collide with $G$ = random-effects covariance if random effects were in play). A deck
MAY do this PROVIDED it states the local meaning explicitly at first appearance, on the lecture-specific
notation slide right after the include, and re-shows the affected definitions where they first matter.
This applies ONLY to non-reserved symbols; the reserved set ($\mathbf{X}_i/\boldsymbol\beta$,
$\mathbf{Z}_i/\mathbf{b}_i$) may never be reassigned. Do not edit the shared partial to encode a
chapter-local meaning. (Ch. 5: $G$ = number of groups is collision-free there because the random-effects
covariance $G$ does not appear in that chapter; this mirrors FLW, which itself reuses $G$ for groups in
Ch. 5 and for the random-effects covariance in Ch. 8. The $N$/$n$ counts are the standard FLW convention,
not an override.)

**General vs generalized linear model.** "GLM" denotes the **generalized** linear model (Ch. 11+).
The **general** linear model (normal errors, e.g. Ch. 3-5 response profiles) is written out or
abbreviated "LM", never "GLM", so the two do not collide across the course.

## Core symbols

These are FLW's symbols (verified against FLW Ch. 4 eq (4.2), Ch. 7, Ch. 8, Ch. 13). Where the course
historically used a different letter, the FLW letter is canonical and the old letter is retired (see the
**FLW-symbol rulings** below).

| Symbol | Meaning | Notes |
|:--|:--|:--|
| $Y_{ij}$ | response for subject $i$ at occasion $j$ | scalar; $i$ = subject, $j$ = time |
| $\mathbf{Y}_i$ | response vector for subject $i$ | $n_i \times 1$ |
| $X_{ij}$ | fixed-effect covariates for $(i,j)$ | row vector, $1 \times p$ |
| $\mathbf{X}_i$ | fixed-effect design matrix for subject $i$ | $n_i \times p$ |
| $Z_{ij}$ | random-effect design row for $(i,j)$ | row vector, $1 \times q$ |
| $\mathbf{Z}_i$ | random-effect design matrix for subject $i$ | $n_i \times q$ |
| $\boldsymbol\beta$ | fixed-effect coefficients | population-average |
| $\mathbf{b}_i$ | random effects for subject $i$ | $\mathbf{b}_i \sim N(0, G)$ |
| $G$ | random-effects (between-subject) covariance | FLW's letter (Ch. 8, elements $g_{jk}$); the course no longer uses $D$ for this |
| $R_i$ | within-subject residual covariance | $\boldsymbol\varepsilon_i \sim N(0, R_i)$ |
| $\Sigma_i$ | marginal (total) covariance of $\mathbf{Y}_i$ | FLW's letter: $\operatorname{Cov}(\mathbf{Y}_i\mid\mathbf{X}_i) = \Sigma_i(\theta)$; in an LME $\Sigma_i = \mathbf{Z}_i G \mathbf{Z}_i^\top + R_i$ |
| $\theta$ | covariance parameters | the vector indexing $\Sigma_i = \Sigma_i(\theta)$ (FLW eq (4.2)) |
| $\varepsilon_{ij}$ | within-subject residual error | scalar |
| $\rho$ | correlation parameter | AR(1) or exchangeable |
| $V_i$ | GEE **working** covariance (Ch. 12-13 ONLY) | $V_i = \mathbf{A}_i^{1/2}\operatorname{Corr}(\mathbf{Y}_i)\,\mathbf{A}_i^{1/2}$; a working assumption, NOT the Gaussian $\Sigma_i$ |
| $\alpha$ | GEE working-correlation parameter(s) | vector when non-exchangeable |
| $\pi_{ij}$ | probability for a binary outcome at $(i,j)$ | |
| $\phi$ | dispersion parameter (GLMs) | distinct from AR correlation |
| $v(\mu)$ | GLM mean-variance function (scalar) | lowercase, $\operatorname{Var}(Y)=\phi\,v(\mu)$; distinct from the matrix $V_i$ (introduced L11) |
| $\kappa_k$ | ordinal cumulative-logit cutpoints, $k=1,\dots,K-1$ | FLW eq (11.1) writes these $\alpha_k$; the course uses $\kappa_k$ to avoid the GEE working-correlation $\alpha$ and the GLM natural parameter $\theta$. Use the polr minus-sign form $\operatorname{logit}P(Y\le k)=\kappa_k - X_{ij}\beta$ (L11/L12) |

## Subscript conventions

Following FLW (Section 3.2): $N$ = number of subjects, $n_i$ = number of occasions for subject $i$
(and $n$ = the common number of occasions when the design is balanced, $n_i = n$).

- $i$: subject ($i = 1, \ldots, N$)
- $j$: occasion / time ($j = 1, \ldots, n_i$; or $j = 1, \ldots, n$ when balanced)
- $k$: state index (transition models)
- $g$: group index (multi-group comparisons, $g = 1, \ldots, G$)

## FLW alignment notes

- **Random-effects predictions:** use "empirical BLUP" / "predicted random effects" (FLW convention),
  not "estimated random effects."
- **Two-stage formulation (FLW 8.4):** Stage 1 (within-subject) $\mathbf{Y}_i = \mathbf{Z}_i \boldsymbol\beta_i + \boldsymbol\varepsilon_i$;
  Stage 2 (between-subject) $\boldsymbol\beta_i = \mathbf{A}_i \boldsymbol\beta + \mathbf{b}_i$. Substituting gives the
  single-equation LME with $\Sigma_i = \mathbf{Z}_i G \mathbf{Z}_i^\top + R_i$.
- **Attenuation (GLMM marginalization):** for the logistic random-intercept model the marginal
  coefficient is $\beta^{\text{marg}} \approx \beta^{\text{cond}}/\sqrt{1 + c_2^{2}\,\sigma_b^2}$ with the
  single constant $c_2 = 16\sqrt{3}/(15\pi) \approx 0.588$ (FLW p. 477). The number $0.346$ is **not** an
  alternative constant: it is the *multiplier on* $\sigma_b^2$ under the root, i.e. $c_2^{2} \approx 0.346$
  ($= (1/1.7)^2$, the probit-matching teaching form). Write $c_2$ for the constant and $c_2^2 \approx 0.346$
  for the multiplier; never present $0.346$ and $0.588$ as competing constants. See the project precision
  standards.
- **Covariance vs correlation:** never use the words interchangeably.

## FLW-symbol rulings (course aligned to the book, 2026-06-19)

Verified against the FLW (2011) PDFs; FLW is the tie-breaker (PI confirmed). These supersede earlier
"pick one per deck" latitude:

- **Marginal (total) covariance of $\mathbf{Y}_i$ is $\Sigma_i$, not $V_i$.** FLW writes
  $\operatorname{Cov}(\mathbf{Y}_i\mid\mathbf{X}_i) = \Sigma_i(\theta)$ (eq (4.2)), the unstructured/pattern
  covariance $\operatorname{Cov}(\mathbf{Y}_i)=\Sigma_i$ (Ch. 7), and the LME decomposition
  $\Sigma_i = \mathbf{Z}_i G \mathbf{Z}_i^\top + R_i$ (Ch. 8). The course's old $V_i$ for this object is retired.
- **Random-effects covariance is $G$, not $D$.** FLW Ch. 8 names "the covariance matrix, $G$, for the
  vector of random effects" with elements $g_{jk}$; Ch. 14/22 use $G$ for GLMM/multilevel random effects.
  The course's old $D$ (Laird-Ware 1982 notation) is retired. Within-subject residual covariance stays $R_i$.
- **$V_i$ is reserved for the GEE *working* covariance (Ch. 12-13 ONLY):**
  $V_i = \mathbf{A}_i^{1/2}\operatorname{Corr}(\mathbf{Y}_i)\,\mathbf{A}_i^{1/2}$ (FLW eq for the working
  covariance). It is a working assumption, a *different object* from the Gaussian $\Sigma_i$; never use
  $V_i$ for the LME/marginal-Gaussian covariance, and never use $\Sigma_i$ for the GEE working covariance.
- **In GEE, $\mathbf{D}_i = \partial\boldsymbol\mu_i/\partial\boldsymbol\beta$** (a derivative matrix in the
  estimating equation), which is why $D$ is not reused for a covariance anywhere in the course.
- **SD-correlation split of a covariance** (e.g. reading off an unstructured fit) is written
  $\Sigma_i = \mathbf{S}\,\mathbf{C}\,\mathbf{S}$ ($\mathbf{S}$ = diagonal of SDs, $\mathbf{C}$ = correlation
  matrix), never $\mathbf{D}\,\mathbf{R}\,\mathbf{D}$ (which would collide with $G$ and $R_i$).

## How to use in a lecture

Put the shared box where the notation slide belongs (typically after Objectives/Prerequisites):

```markdown
{{< include _notation_box.qmd >}}
```

For a lecture that introduces extra symbols (e.g. a transition-state notation in Ch. 18), add a
small lecture-specific slide *after* the shared box rather than editing the shared box, and add the
new symbol to this master if it is reused across lectures.
