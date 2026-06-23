"""Knowledge graph construction from parsed content."""

import re
from typing import Optional
from bios667_rag.storage import KnowledgeStore
from bios667_rag.chunk import Chunk


class KnowledgeGraphBuilder:
    """Build knowledge graph from extracted content."""

    def __init__(self, store: KnowledgeStore):
        self.store = store

    def build_hierarchy(self, structure: list[dict]):
        """Build hierarchical structure from parsed sections."""
        chapter_id = None

        for item in structure:
            if item["type"] == "chapter":
                node_id = f"chapter_{item['number']}"
                self.store.add_node(
                    node_id=node_id, node_type="chapter",
                    name=item["title"], chapter_num=item["number"],
                    page_start=item.get("page"),
                )
                chapter_id = node_id

            elif item["type"] == "section":
                section_num = item["number"]
                node_id = f"section_{section_num}"
                level = section_num.count(".")
                chapter_num = int(section_num.split(".")[0])

                self.store.add_node(
                    node_id=node_id, node_type="section",
                    name=item["title"], chapter_num=chapter_num,
                    page_start=item.get("page"),
                )

                parent_id = None
                if level == 1:
                    parent_id = f"chapter_{chapter_num}"
                else:
                    parent_num = ".".join(section_num.split(".")[:-1])
                    parent_id = f"section_{parent_num}"

                if parent_id:
                    self.store.add_edge(parent_id, node_id, "contains")

    def add_chunk_with_embedding(self, chunk: Chunk, embedding: list[float]) -> str:
        """Add a content chunk with its embedding."""
        chunk_id = f"chunk_{chunk.chapter_num}_{chunk.section_path}_{hash(chunk.text[:50]) % 10000}"

        self.store.add_node(
            node_id=chunk_id, node_type="content",
            name=f"Content from {chunk.section_path}",
            content=chunk.text, chapter_num=chunk.chapter_num,
            page_start=chunk.page_start, page_end=chunk.page_end,
            embedding=embedding,
        )

        section_id = f"section_{chunk.section_path}"
        if self.store.get_node(section_id):
            self.store.add_edge(section_id, chunk_id, "contains")

        return chunk_id

    def add_concept(
        self, name: str, definition: str, chapter_num: int,
        section_path: str, embedding: Optional[list[float]] = None,
    ) -> str:
        """Add a concept node."""
        concept_id = f"concept_{name.lower().replace(' ', '_')}"

        self.store.add_node(
            node_id=concept_id, node_type="concept",
            name=name, content=definition, chapter_num=chapter_num,
            embedding=embedding,
        )

        section_id = f"section_{section_path}"
        if self.store.get_node(section_id):
            self.store.add_edge(section_id, concept_id, "contains")

        return concept_id

    def add_relationship(
        self, source_concept: str, target_concept: str,
        relationship: str, confidence: float = 1.0,
    ):
        """Add a relationship between concepts."""
        source_id = f"concept_{source_concept.lower().replace(' ', '_')}"
        target_id = f"concept_{target_concept.lower().replace(' ', '_')}"
        self.store.add_edge(source_id, target_id, relationship, confidence)
