"""Tests for the bios667-corpus MCP server (Task 5.4).

These tests stay at the level the existing textbook mcp_server is structured: confirm
the module imports, ``create_server`` returns a configured ``Server``, the four corpus
tools are exposed with non-empty inputSchemas, and -- crucially -- ``main`` is a SYNC
shim (NOT a coroutine function) over an async ``_main`` (guarding against re-introducing
the async-console-entry bug fixed earlier).

Tool DISPATCH is exercised lightly with an injected fake ``CorpusQuery`` so we never
touch the real ``rag/data`` store. Behavior of the query methods themselves is covered
by test_corpus_query.py.
"""

import asyncio
import inspect
import json

from mcp.server import Server
from mcp.types import TextContent

import bios667_rag.corpus_mcp_server as mcp_mod
from bios667_rag.corpus_mcp_server import create_server, main, _main


EXPECTED_TOOLS = {"search_all", "find_examples", "find_datasets", "check_lecture_sync"}


class _FakeCorpusQuery:
    """Records calls and returns canned results for each query method."""

    def __init__(self):
        self.calls = []

    def search_all(self, query, source_type=None, chapter=None, year=None, top_k=8):
        self.calls.append(("search_all", query, source_type, chapter, year, top_k))
        return [{"text": "hit", "source_path": "p", "score": 0.9}]

    def find_examples(self, topic, material_types=None, top_k=8):
        self.calls.append(("find_examples", topic, material_types, top_k))
        return [{"text": "ex", "source_path": "hw.qmd"}]

    def find_datasets(self, query, top_k=8):
        self.calls.append(("find_datasets", query, top_k))
        return [{"dataset_card": {"text": "dc"}, "used_by": []}]

    def check_lecture_sync(self, lecture, distance_threshold=0.6):
        self.calls.append(("check_lecture_sync", lecture, distance_threshold))
        return {"lecture": str(lecture), "covered": [], "gaps": []}


def test_module_imports_and_create_server():
    server = create_server()
    assert isinstance(server, Server)
    assert server.name == "bios667-corpus"


def test_list_tools_exact_four_with_schemas():
    server = create_server()
    # Find the registered list_tools handler.
    from mcp.types import ListToolsRequest

    handler = server.request_handlers[ListToolsRequest]
    result = asyncio.run(handler(ListToolsRequest(method="tools/list")))
    tools = result.root.tools
    names = {t.name for t in tools}
    assert names == EXPECTED_TOOLS
    assert len(tools) == 4
    for t in tools:
        assert t.inputSchema
        assert t.inputSchema.get("type") == "object"
        assert t.inputSchema.get("properties")


def test_main_is_sync_shim_not_coroutine():
    assert inspect.iscoroutinefunction(main) is False
    assert inspect.iscoroutinefunction(_main) is True


def test_call_tool_dispatch_with_injected_query():
    fake = _FakeCorpusQuery()
    server = create_server(query=fake)
    from mcp.types import CallToolRequest, CallToolRequestParams

    handler = server.request_handlers[CallToolRequest]

    def call(name, arguments):
        req = CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(name=name, arguments=arguments),
        )
        result = asyncio.run(handler(req))
        return result.root.content

    content = call("search_all", {"query": "lme", "top_k": 3})
    assert isinstance(content[0], TextContent)
    assert json.loads(content[0].text) == [
        {"text": "hit", "source_path": "p", "score": 0.9}
    ]

    call("find_examples", {"topic": "gee"})
    call("find_datasets", {"query": "dental"})
    content = call("check_lecture_sync", {"lecture": 8})
    parsed = json.loads(content[0].text)
    assert parsed["lecture"] == "8"

    called = {c[0] for c in fake.calls}
    assert called == EXPECTED_TOOLS
