# rag/src/bios667_rag/mcp_server.py
"""MCP server for BIOS 667 textbook RAG."""

import json
from pathlib import Path
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from bios667_rag.storage import KnowledgeStore
from bios667_rag.embed import Embedder
from bios667_rag.query import QueryEngine


RAG_DIR = Path(__file__).parent.parent.parent
DATA_DIR = RAG_DIR / "data"
DB_PATH = DATA_DIR / "knowledge_graph.db"
CHROMADB_PATH = DATA_DIR / "vectors.chromadb"


def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("bios667-textbook")

    _store: Optional[KnowledgeStore] = None
    _embedder: Optional[Embedder] = None
    _engine: Optional[QueryEngine] = None

    def get_engine() -> QueryEngine:
        nonlocal _store, _embedder, _engine
        if _engine is None:
            _store = KnowledgeStore(db_path=DB_PATH, chromadb_path=CHROMADB_PATH)
            _embedder = Embedder()
            _engine = QueryEngine(_store, _embedder)
        return _engine

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="search_textbook",
                description="Semantic search across the Fitzmaurice textbook content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "top_k": {"type": "integer", "description": "Number of results (default: 5)", "default": 5},
                        "chapter": {"type": "integer", "description": "Optional chapter filter"},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="get_chapter_outline",
                description="Get hierarchical structure of a textbook chapter",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "chapter": {"type": "integer", "description": "Chapter number (1-19)"},
                        "depth": {"type": "integer", "description": "Depth of outline (default: 3)", "default": 3},
                    },
                    "required": ["chapter"],
                },
            ),
            Tool(
                name="get_concept",
                description="Get a specific concept with definition and related concepts",
                inputSchema={
                    "type": "object",
                    "properties": {"concept": {"type": "string", "description": "Concept name"}},
                    "required": ["concept"],
                },
            ),
            Tool(
                name="find_prerequisites",
                description="Find prerequisite concepts needed to understand a topic",
                inputSchema={
                    "type": "object",
                    "properties": {"topic": {"type": "string", "description": "Topic to find prerequisites for"}},
                    "required": ["topic"],
                },
            ),
            Tool(
                name="find_related",
                description="Find cross-references and related concepts",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Topic to find relations for"},
                        "relationship": {
                            "type": "string",
                            "description": "Filter by relationship type",
                            "enum": ["all", "requires", "relates_to", "uses", "implements"],
                            "default": "all",
                        },
                    },
                    "required": ["topic"],
                },
            ),
            Tool(
                name="get_examples",
                description="Find worked examples involving a concept or dataset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "concept": {"type": "string", "description": "Concept filter"},
                        "dataset": {"type": "string", "description": "Dataset filter (e.g., 'dental', 'epilepsy')"},
                    },
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        engine = get_engine()

        if name == "search_textbook":
            results = engine.search(
                query=arguments["query"],
                top_k=arguments.get("top_k", 5),
                chapter=arguments.get("chapter"),
            )
            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == "get_chapter_outline":
            outline = engine.get_chapter_outline(
                chapter=arguments["chapter"],
                depth=arguments.get("depth", 3),
            )
            return [TextContent(type="text", text=json.dumps(outline, indent=2))]

        elif name == "get_concept":
            concept = engine.get_concept(arguments["concept"])
            return [TextContent(type="text", text=json.dumps(concept, indent=2))]

        elif name == "find_prerequisites":
            prereqs = engine.find_prerequisites(arguments["topic"])
            return [TextContent(type="text", text=json.dumps(prereqs, indent=2))]

        elif name == "find_related":
            rel = arguments.get("relationship", "all")
            related = engine.find_related(
                arguments["topic"],
                relationship=None if rel == "all" else rel,
            )
            return [TextContent(type="text", text=json.dumps(related, indent=2))]

        elif name == "get_examples":
            examples = engine.get_examples(
                concept=arguments.get("concept"),
                dataset=arguments.get("dataset"),
            )
            return [TextContent(type="text", text=json.dumps(examples, indent=2))]

        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    return server


async def _main():
    """Run the MCP server (async)."""
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


def main():
    """Synchronous entry point for the bios667-mcp console script."""
    import asyncio
    asyncio.run(_main())


if __name__ == "__main__":
    main()
