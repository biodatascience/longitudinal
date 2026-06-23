# BIOS 667 Textbook RAG

Local RAG system with knowledge graph for the Fitzmaurice longitudinal analysis textbook.

## Setup

```bash
cd rag
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Index the textbook (one-time)

```bash
bios667-index
```

## Index the course corpus

```bash
# Preview what would be indexed without writing anything
bios667-index-corpus --plan

# Default incremental build (only embeds new/changed files)
bios667-index-corpus

# Force a full re-embed of the entire corpus
bios667-index-corpus --rebuild
```

## Use with Claude Code

Add to `.claude/settings.local.json`, then restart Claude Code.
