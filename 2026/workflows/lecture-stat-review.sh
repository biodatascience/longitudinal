#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# lecture-stat-review.sh  (BIOS 667 project-scoped commit review)
#
# Claude Code PostToolUse / Bash hook, wired from this repo's
# .claude/settings.json. It COMPLEMENTS the global codex-commit-review hook:
# the global hook reviews code + prose/consistency; this one adds a
# STATISTICAL / METHODOLOGICAL / CONSISTENCY review of the committed diff for
# course content (slides, homework, statistical R), which is what the global
# code review does not explicitly cover.
#
# Behavior matches the PI's design:
#   * Subsequent versions (a content file is MODIFIED): review the diff for
#     statistical/methodological correctness and notation/terminology/cross-ref
#     consistency.
#   * First version (a content file is ADDED): a diff review is insufficient, so
#     the hook FLAGS that a full first-version review (the POST_LECTURE_REVIEW.md
#     panel) should be run. It does not auto-launch the panel.
#
# Read-only and advisory: it never edits files and always exits 0. codex runs in
# a read-only sandbox; if codex is rate-limited it falls back to headless claude.
#
# SETUP (the wiring lives in .claude/settings.json, which is gitignored, so each
# machine enables it once). Add to <repo>/.claude/settings.json:
#   { "hooks": { "PostToolUse": [ { "matcher": "Bash", "hooks": [
#       { "type": "command",
#         "command": "bash \"$CLAUDE_PROJECT_DIR/2026/workflows/lecture-stat-review.sh\"",
#         "timeout": 300 } ] } ] } }
# Then approve the hook when Claude Code prompts. It complements (does not replace)
# the global codex-commit-review hook.
# ---------------------------------------------------------------------------
set -uo pipefail

input="$(cat)"
command -v jq >/dev/null 2>&1 || exit 0

cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // ""')"
cwd="$(printf '%s' "$input" | jq -r '.cwd // "."')"

# --- Gate 1: only act on git commit commands -------------------------------
case "$cmd" in
  *"git commit"*) : ;;
  *) exit 0 ;;
esac
case "$cmd" in
  *"--dry-run"*|*"--help"*|*" -h "*|*" -h") exit 0 ;;
esac

# --- Gate 2: confirm a real, just-created commit ---------------------------
git -C "$cwd" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
head_sha="$(git -C "$cwd" rev-parse --short HEAD 2>/dev/null)" || exit 0
[ -n "$head_sha" ] || exit 0
commit_epoch="$(git -C "$cwd" show -s --format=%ct HEAD 2>/dev/null)" || exit 0
age=$(( $(date +%s) - commit_epoch ))
[ "$age" -le 30 ] || exit 0
subject="$(git -C "$cwd" show -s --format=%s HEAD 2>/dev/null)"

# --- Gate 3: the commit must touch course CONTENT (else nothing to review) --
changed="$(git -C "$cwd" diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null)"
content="$(printf '%s\n' "$changed" | grep -iE '\.(qmd|rmd|r|md)$' || true)"
[ -n "${content//[$' \t\n']/}" ] || exit 0

# First-version detection: any ADDED lecture/homework deck (.qmd/.Rmd) ------
added_decks="$(git -C "$cwd" diff-tree --no-commit-id --name-status -r HEAD 2>/dev/null \
  | awk '$1=="A"{print $2}' | grep -iE '\.(qmd|rmd)$' | grep -iE 'lectures/|/HW|hw[0-9]|BIOS667_L' || true)"

first_version_note=""
if [ -n "${added_decks//[$' \t\n']/}" ]; then
  first_version_note="

FIRST-VERSION FLAG: this commit ADDS new course content file(s):
${added_decks}
A diff review is NOT sufficient for brand-new content. Recommend running the FULL
first-version review (the 2026/POST_LECTURE_REVIEW.md panel via
2026/workflows/lecture_review_panel.mjs) on the new file(s), not just this diff."
fi

# --- Locate reviewers ------------------------------------------------------
export PATH="/home/naimrashid/.nvm/versions/node/v22.22.1/bin:$PATH"
CODEX="$(command -v codex || true)"
CLAUDE="$(command -v claude || echo "$HOME/.local/bin/claude")"
CLAUDE_REVIEW_MODEL="${CLAUDE_REVIEW_MODEL:-claude-sonnet-4-6}"
[ -n "$CODEX" ] || [ -x "$CLAUDE" ] || exit 0

# --- Statistical / methodological / consistency review prompt --------------
REVIEW_PROMPT=""
read -r -d '' REVIEW_PROMPT <<EOF || true
You are performing a read-only STATISTICAL and CONSISTENCY review of a single git
commit in the BIOS 667 course repository. Do NOT modify, stage, or commit anything.

SCOPE: Review ONLY the changes in the most recent commit (HEAD) vs its parent. Run
\`git show HEAD\`. Examine only the changed hunks in course content (slides, homework,
statistical R); treat unchanged content as context. This review is the statistical
complement to the general code/prose review, so focus on the three lenses below, not
on generic code style.

1. STATISTICAL / METHODOLOGICAL CORRECTNESS of anything the diff changed: formulas,
   distributions, hypothesis tests, degrees of freedom, and statistical R code.
   Watch specifically for: wrong boundary / variance-component mixtures and df (e.g.
   1/2 chi^2_0 + 1/2 chi^2_1 only for a single variance; dropping a random slope from a
   model with a random intercept removes TWO parameters -> 1/2 chi^2_1 + 1/2 chi^2_2,
   not a simple halving); ML vs REML usage (ML for LRT of fixed effects, REML for
   variance/covariance structure); claiming Kenward-Roger/Satterthwaite df from nlme
   (it has neither); re.form=NA / level=0 misdescribed as a nonlinear marginal mean;
   GEE validity (MCAR vs IPW-GEE for MAR); attenuation constants; "invalid inference"
   vs "biased standard errors" language. Treat a real statistical error as HIGH severity.
2. NOTATION / TERMINOLOGY CONSISTENCY with the repo's canon: 2026/NOTATION_REFERENCE.md
   and 2026/lectures/_notation_box.qmd (reserved symbols: X_i/beta fixed, Z_i/b_i random
   only; no inline symbol collisions such as a fixed covariate written as z_{ij}), and
   the precision standards / conventions in CLAUDE.md and 2026/REFERENCE_DECK_SPEC.md.
3. CROSS-REFERENCE INTEGRITY for any reference the diff touched ("recall Ch. X",
   "see Lecture Y", "we revisit in Z"): does it resolve to real content?
4. NARRATIVE-VS-OUTPUT (if your sandbox can run R): for any changed hunk - CODE OR
   PROSE - that states, edits, or relies on an analysis-derived NUMBER or a data-derived
   VERDICT/pattern word ("rises", "flat", "drifts off 1", "within bands", "adequate",
   "needed", "no corAR1"), RE-RUN the chunk that produces that quantity (whether or not
   the chunk itself changed in this diff - a prose-only edit to a stated number or
   conclusion still must be re-verified) and confirm the stated value/pattern matches the
   computed output. A clean render does not prove this. Flag any slide claim the data does
   not support as HIGH (this lens caught L10's variogram and ACF claims). Also flag
   analysis-derived numbers that are HARDCODED rather than pulled from the fitted object
   via inline R (they drift). If you cannot run R, say so and skip this lens (do not pass
   it silently).

You see only the diff, not the whole repo, but you CAN read any file (read-only).
Before flagging a referenced section, file, or cross-reference as missing or
inconsistent, VERIFY it by reading or grepping the target. Do not flag a "missing"
target you did not actually check.

OUTPUT: your final message IS the review. Be concise; list only issues that genuinely
matter, each as \`- [severity] short title -- path:line\` with a one-line rationale.
If the diff introduces no statistical or consistency problems, say so in one line.${first_version_note}
EOF

# --- Run codex STRICTLY read-only (no sandbox-escape fallback) -------------
# Always read-only: there is no danger-full-access retry. If codex's bwrap
# sandbox cannot initialize in this environment, we discard the output and let
# the headless claude fallback below run instead, so the read-only guarantee
# this hook advertises is never relaxed.
review=""; reviewer="codex (statistical)"
if [ -n "$CODEX" ]; then
  msg_file="$(mktemp)"
  raw="$(cd "$cwd" && "$CODEX" exec --sandbox read-only --color never \
      -c approval_policy=never --skip-git-repo-check -C "$cwd" -o "$msg_file" \
      "$REVIEW_PROMPT" </dev/null 2>&1)"
  review="$(sed -E 's/\x1b\[[0-9;]*[mGKHF]//g' "$msg_file" 2>/dev/null)"
  # bwrap could not initialize -> drop any partial/noise so the claude fallback fires.
  if printf '%s\n%s' "$review" "$raw" | grep -qiE 'bwrap|RTM_NEWADDR|loopback: Failed'; then review=""; fi
  rm -f "$msg_file"
fi

# --- Fallback to headless claude if codex was empty / rate-limited ---------
if [ -z "${review//[$' \t\n']/}" ] \
   || printf '%s' "$review" | grep -qiE 'usage limit|rate limit|quota|try again at|429|^[[:space:]]*ERROR:|stream (error|disconnected)'; then
  if [ -x "$CLAUDE" ]; then
    cl_diff="$(git -C "$cwd" --no-pager show "$head_sha" 2>/dev/null | head -c 200000)"
    cl_review="$(timeout 200 "$CLAUDE" -p "$REVIEW_PROMPT

===== COMMIT ${head_sha} DIFF — review ONLY this; do NOT use any tools, just respond =====
NOTE: in this fallback you CANNOT read other files, so you cannot run the verification the prompt
above asks for. Therefore do NOT flag any referenced section, file, or cross-reference as missing or
inconsistent (you cannot confirm it); review only what is visibly wrong in the diff text below.
${cl_diff}" --model "$CLAUDE_REVIEW_MODEL" --permission-mode plan 2>/dev/null)"
    if [ -n "${cl_review//[$' \t\n']/}" ]; then review="$cl_review"; reviewer="claude (codex fallback, statistical)"; fi
  fi
fi

[ -n "${review//[$' \t\n']/}" ] || exit 0
banner="📊 ${reviewer} review — commit ${head_sha}: ${subject}"
note="A ${reviewer} review (statistical/consistency lens, BIOS 667 project hook) of the commit just created follows. It is read-only; the reviewer cannot edit files. Do NOT auto-fix: assess each finding, discard false positives, present the genuine ones, and propose a fix plan for the user to approve. For any FIRST-VERSION FLAG, recommend running the full POST_LECTURE_REVIEW.md panel rather than relying on this diff review."

jq -n --arg b "$banner" --arg r "$review" --arg n "$note" \
  '{ systemMessage: ($b + "\n" + $r), suppressOutput: true,
     hookSpecificOutput: { hookEventName: "PostToolUse", additionalContext: ($n + "\n\n" + $b + "\n" + $r) } }'
exit 0
