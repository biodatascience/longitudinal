# rag/tests/test_graph.py
import tempfile
from pathlib import Path
import pytest
from bios667_rag.graph import KnowledgeGraphBuilder
from bios667_rag.storage import KnowledgeStore


def test_build_chapter_hierarchy():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = KnowledgeStore(
            db_path=Path(tmpdir) / "test.db",
            chromadb_path=Path(tmpdir) / "chroma",
        )

        builder = KnowledgeGraphBuilder(store)

        structure = [
            {"type": "chapter", "number": 8, "title": "Linear Mixed Effects Models", "page": 201},
            {"type": "section", "number": "8.1", "title": "Introduction", "page": 201},
            {"type": "section", "number": "8.2", "title": "Model Specification", "page": 210},
            {"type": "section", "number": "8.2.1", "title": "Random Intercept Model", "page": 212},
        ]

        builder.build_hierarchy(structure)

        chapter = store.get_node("chapter_8")
        assert chapter is not None
        assert chapter["type"] == "chapter"

        children = store.get_children("chapter_8")
        assert len(children) == 2  # 8.1 and 8.2

        subsections = store.get_children("section_8.2")
        assert len(subsections) == 1
        assert subsections[0]["name"] == "Random Intercept Model"

        store.close()
