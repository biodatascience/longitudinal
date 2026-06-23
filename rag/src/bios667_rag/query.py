"""Query engine for RAG system."""

from typing import Optional
from bios667_rag.storage import KnowledgeStore
from bios667_rag.embed import Embedder


class QueryEngine:
    """Query interface for the knowledge graph and vectors."""

    def __init__(self, store: KnowledgeStore, embedder: Embedder):
        self.store = store
        self.embedder = embedder

    def search(self, query: str, top_k: int = 5, chapter: Optional[int] = None) -> list[dict]:
        """Semantic search across all content."""
        query_embedding = self.embedder.embed_single(query)
        return self.store.search_vectors(
            query_embedding=query_embedding, top_k=top_k, chapter_filter=chapter,
        )

    def get_chapter_outline(self, chapter: int, depth: int = 3) -> dict:
        """Get hierarchical structure of a chapter."""
        chapter_node = self.store.get_node(f"chapter_{chapter}")
        if not chapter_node:
            return {"error": f"Chapter {chapter} not found"}

        def build_tree(node_id: str, current_depth: int) -> dict:
            node = self.store.get_node(node_id)
            if not node:
                return {}

            result = {"id": node["id"], "name": node["name"], "type": node["type"]}

            if current_depth < depth:
                children = self.store.get_children(node_id)
                if children:
                    result["children"] = [
                        build_tree(c["id"], current_depth + 1)
                        for c in children if c["type"] in ("section", "concept")
                    ]

            return result

        return build_tree(f"chapter_{chapter}", 0)

    def get_concept(self, concept_name: str) -> Optional[dict]:
        """Get a concept with its context."""
        concept_id = f"concept_{concept_name.lower().replace(' ', '_')}"
        node = self.store.get_node(concept_id)

        if not node:
            results = self.search(concept_name, top_k=1)
            if results:
                return results[0]
            return None

        related = self.store.get_related(concept_id)
        return {**node, "related": related}

    def find_prerequisites(self, topic: str) -> list[dict]:
        """Find prerequisite concepts for a topic."""
        concept_id = f"concept_{topic.lower().replace(' ', '_')}"
        prerequisites = []
        visited = set()

        def collect_prereqs(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            related = self.store.get_related(node_id, relationship="requires")
            for r in related:
                prerequisites.append(r)
                collect_prereqs(r["id"])

        collect_prereqs(concept_id)
        return prerequisites

    def find_related(self, topic: str, relationship: Optional[str] = None) -> list[dict]:
        """Find related concepts."""
        concept_id = f"concept_{topic.lower().replace(' ', '_')}"
        return self.store.get_related(concept_id, relationship=relationship)

    def get_examples(self, concept: Optional[str] = None, dataset: Optional[str] = None) -> list[dict]:
        """Find examples involving a concept or dataset."""
        results = []

        if concept:
            search_results = self.search(f"example {concept}", top_k=10)
            results.extend([r for r in search_results if "example" in r.get("content", "").lower()])

        if dataset:
            search_results = self.search(f"{dataset} data example", top_k=10)
            results.extend([r for r in search_results if dataset.lower() in r.get("content", "").lower()])

        seen = set()
        unique_results = []
        for r in results:
            if r["id"] not in seen:
                seen.add(r["id"])
                unique_results.append(r)

        return unique_results[:10]
