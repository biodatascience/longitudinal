#!/usr/bin/env python3
"""Slide density / visual-engagement check for BIOS 667 Quarto reveal.js decks.

A cheap, deterministic heuristic that flags slides students would find dense or
"boring": too much text, too many bullets, or a wall of prose with no visual
(R plot, image, diagram, or even a table). It does NOT judge content; it surfaces
candidates to SPLIT into more slides or to support with a figure/diagram/schematic.

Usage:  python3 2026/workflows/slide_density_check.py <deck.qmd> [<deck2.qmd> ...]

Thresholds (tune in the spec, not here, if the house style changes):
  DENSE_WORDS  = 70   words of prose on one slide
  DENSE_BULLETS= 7    bullet lines on one slide
  PROSE_NOVIS  = 45   words with NO visual element -> wants a figure/diagram
A "visual element" = an R code chunk, an image, a Mermaid/diagram block, or a
markdown table. Speaker notes (::: {.notes}) and code-chunk bodies are excluded
from the prose word count (they are not shown on the slide).
"""
import re
import sys

DENSE_WORDS = 70
DENSE_BULLETS = 7
PROSE_NOVIS = 45

# Structural / navigational / assessment slides are legitimately text: do NOT flag
# them for "needs a visual" (they still get the dense->split flag at the high threshold).
EXEMPT_NOVIS = re.compile(
    r"objective|roadmap|prerequisite|recall|summary|takeaway|canonical|for next time|"
    r"notation|reporting|recipe|further reading|quick reference|common mistakes|gotcha|"
    r"check your understanding|references|outline|agenda",
    re.I,
)


def slides(text):
    """Yield (heading, body) for each `## ` slide; skip `# ` part dividers/title."""
    lines = text.splitlines()
    cur_head, cur_body = None, []
    for ln in lines:
        if re.match(r"^## ", ln):
            if cur_head is not None:
                yield cur_head, "\n".join(cur_body)
            cur_head, cur_body = ln[3:].strip(), []
        elif re.match(r"^# ", ln):
            if cur_head is not None:
                yield cur_head, "\n".join(cur_body)
            cur_head, cur_body = None, []
        elif cur_head is not None:
            cur_body.append(ln)
    if cur_head is not None:
        yield cur_head, "\n".join(cur_body)


def analyze(body):
    has_chunk = bool(re.search(r"^```\{", body, re.M))
    has_image = bool(re.search(r"!\[.*\]\(", body))
    has_diagram = bool(re.search(r"```\{?mermaid|graph (TD|LR)|digraph", body))
    has_table = bool(re.search(r"^\s*\|.*\|", body, re.M))
    visual = has_chunk or has_image or has_diagram or has_table
    # Strip code chunks and speaker notes from the prose word count.
    prose = re.sub(r"^```.*?^```", "", body, flags=re.S | re.M)
    prose = re.sub(r"::: \{\.notes\}.*?:::", "", prose, flags=re.S)
    prose = re.sub(r"^\s*\|.*\|\s*$", "", prose, flags=re.M)  # drop table rows
    bullets = len(re.findall(r"^\s*[-*] ", prose, re.M))
    words = len(re.findall(r"\b\w+\b", re.sub(r"[#>*_`$|:-]", " ", prose)))
    return dict(words=words, bullets=bullets, visual=visual,
                has_chunk=has_chunk, has_image=has_image, has_table=has_table,
                has_diagram=has_diagram)


def main(paths):
    total_flagged = 0
    for path in paths:
        try:
            text = open(path).read()
        except OSError as e:
            print(f"!! cannot read {path}: {e}")
            continue
        name = path.split("/")[-1]
        # Empty-slide check: a `---` immediately before a `# ` section divider renders a BLANK slide
        # (the `#` already starts its own slide). Also flag two consecutive `---` separators.
        # Strip the YAML front matter first so its closing `---` is not mistaken for a slide separator.
        body_text = re.sub(r"^---\n.*?\n---\n", "\n", text, count=1, flags=re.S)
        empties = len(re.findall(r"\n---\n\s*# [^#]", body_text)) + len(re.findall(r"\n---\n\s*---\n", body_text))
        if empties:
            print(f"\n!! {name}: {empties} EMPTY slide(s) -- a '---' sits before a '# ' divider (or doubled). "
                  f"Remove the stray '---'.")
        flags = []
        for head, body in slides(text):
            a = analyze(body)
            reasons = []
            if a["words"] > DENSE_WORDS:
                reasons.append(f"dense prose ({a['words']} words) -> split")
            if a["bullets"] > DENSE_BULLETS:
                reasons.append(f"{a['bullets']} bullets -> split")
            if a["words"] > PROSE_NOVIS and not a["visual"] and not EXEMPT_NOVIS.search(head):
                reasons.append(f"{a['words']} words, NO visual -> add figure/diagram")
            if reasons:
                flags.append((head, a, reasons))
        print(f"\n=== {name}: {len(flags)} slide(s) flagged ===")
        for head, a, reasons in flags:
            vis = "+".join(k for k in ("chunk", "image", "table", "diagram") if a[f"has_{k}"]) or "none"
            print(f"  [{a['words']}w {a['bullets']}b vis:{vis}] {head}")
            for r in reasons:
                print(f"       - {r}")
        total_flagged += len(flags)
    print(f"\nTOTAL flagged across {len(paths)} deck(s): {total_flagged}")
    print("Flags are candidates to SPLIT or to support with a figure/diagram/schematic; "
          "they are not auto-judgments.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1:])
