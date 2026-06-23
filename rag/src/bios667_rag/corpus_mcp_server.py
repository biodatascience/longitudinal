# rag/src/bios667_rag/corpus_mcp_server.py
"""MCP server for the BIOS 667 course corpus (Task 5.4).

Exposes the four :class:`CorpusQuery` methods (``search_all``, ``find_examples``,
``find_datasets``, ``check_lecture_sync``) as MCP tools, each returning JSON-serialized
results as ``TextContent``. Mirrors the structure of the existing textbook
``mcp_server`` -- in particular the SYNC ``main()`` shim over an async ``_main()`` (do
NOT register an ``async def main`` as the console entry).

The corpus store lives at ``rag/data`` (a ``chroma`` subdir holding the
``bios667_corpus`` collection, plus ``graph.db``). The store directory may be overridden
via the ``BIOS667_CORPUS_STORE`` environment variable; otherwise it defaults to the
package's ``rag/data`` directory.
"""

import json
import os
from pathlib import Path
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from bios667_rag.corpus_query import CorpusQuery


RAG_DIR = Path(__file__).parent.parent.parent
DATA_DIR = RAG_DIR / "data"


def _default_store_dir() -> Path:
    """Resolve the corpus store directory (env override, else ``rag/data``)."""
    env = os.environ.get("BIOS667_CORPUS_STORE")
    if env:
        return Path(env)
    return DATA_DIR


def create_server(query: Optional[CorpusQuery] = None) -> Server:
    """Create and configure the corpus MCP server.

    ``query`` may be injected (tests/smoke checks) to avoid touching the real store; if
    omitted, a :class:`CorpusQuery` pointed at the default store dir is built lazily on
    first tool call.
    """
    server = Server("bios667-corpus")

    _query: Optional[CorpusQuery] = query

    def get_query() -> CorpusQuery:
        nonlocal _query
        if _query is None:
            _query = CorpusQuery(store_dir=_default_store_dir())
        return _query

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="search_all",
                description=(
                    "Semantic search across the entire BIOS 667 course corpus "
                    "(lectures, textbook, homework, code, handouts, data cards) with "
                    "optional metadata filters."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "source_type": {
                            "type": ["string", "array"],
                            "items": {"type": "string"},
                            "description": (
                                "Optional source_type filter; a single value or a list "
                                "(e.g. 'lecture', 'textbook', 'hw', 'rcode')"
                            ),
                        },
                        "chapter": {
                            "type": "integer",
                            "description": "Optional FLW chapter filter (exact membership)",
                        },
                        "year": {"type": "integer", "description": "Optional year filter"},
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results (default: 8)",
                            "default": 8,
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="find_examples",
                description=(
                    "Find adaptable example materials (homework, solutions, SAS/R code, "
                    "handouts) on a topic -- whole problem/code units to open and adapt, "
                    "not lecture or textbook prose."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Topic to find examples for"},
                        "material_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Optional list of material source types to restrict to "
                                "(default: hw, hw_solution, sas, rcode, handout)"
                            ),
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results (default: 8)",
                            "default": 8,
                        },
                    },
                    "required": ["topic"],
                },
            ),
            Tool(
                name="find_datasets",
                description=(
                    "Find dataset cards matching a query and list the materials that USE "
                    "each dataset (via the knowledge graph's uses edges)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Dataset search query"},
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results (default: 8)",
                            "default": 8,
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="check_lecture_sync",
                description=(
                    "Surface candidate textbook-coverage gaps for a lecture: for each "
                    "textbook chunk, find the nearest lecture chunk and bin as covered / "
                    "possible_mismatch / gap. Surfaces candidates for human review; does "
                    "NOT auto-judge. 'lecture' may be a chapter int, a .qmd/.rmd path, or "
                    "a topic string."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "lecture": {
                            "type": ["integer", "string"],
                            "description": (
                                "Chapter number (int), lecture file path (.qmd/.rmd), or "
                                "topic string"
                            ),
                        },
                        "distance_threshold": {
                            "type": "number",
                            "description": (
                                "Cosine-distance threshold for 'covered' (default: 0.6)"
                            ),
                            "default": 0.6,
                        },
                    },
                    "required": ["lecture"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        query_obj = get_query()

        if name == "search_all":
            results = query_obj.search_all(
                query=arguments["query"],
                source_type=arguments.get("source_type"),
                chapter=arguments.get("chapter"),
                year=arguments.get("year"),
                top_k=arguments.get("top_k", 8),
            )
            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == "find_examples":
            results = query_obj.find_examples(
                topic=arguments["topic"],
                material_types=arguments.get("material_types"),
                top_k=arguments.get("top_k", 8),
            )
            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == "find_datasets":
            results = query_obj.find_datasets(
                query=arguments["query"],
                top_k=arguments.get("top_k", 8),
            )
            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == "check_lecture_sync":
            results = query_obj.check_lecture_sync(
                lecture=arguments["lecture"],
                distance_threshold=arguments.get("distance_threshold", 0.6),
            )
            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    return server


async def _main():
    """Run the corpus MCP server (async)."""
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Synchronous entry point for the bios667-corpus console script."""
    import asyncio

    asyncio.run(_main())


if __name__ == "__main__":
    main()
