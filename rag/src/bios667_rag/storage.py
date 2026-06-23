"""Storage layer for knowledge graph and vectors."""

import sqlite3
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings


class KnowledgeStore:
    """Combined SQLite (graph) + ChromaDB (vectors) storage."""

    def __init__(
        self,
        db_path: Path,
        chromadb_path: Path,
    ):
        self.db_path = db_path
        self.chromadb_path = chromadb_path

        # Initialize SQLite
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self._init_schema()

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(chromadb_path),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="textbook_chunks",
            metadata={"hnsw:space": "cosine"},
        )

    def _init_schema(self):
        """Create tables if they don't exist."""
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                content TEXT,
                chapter_num INTEGER,
                page_start INTEGER,
                page_end INTEGER,
                chromadb_id TEXT
            );

            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                FOREIGN KEY (source_id) REFERENCES nodes(id),
                FOREIGN KEY (target_id) REFERENCES nodes(id)
            );

            CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
            CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
            CREATE INDEX IF NOT EXISTS idx_edges_rel ON edges(relationship);
            CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
            CREATE INDEX IF NOT EXISTS idx_nodes_chapter ON nodes(chapter_num);
        """)
        self.db.commit()

    def add_node(
        self,
        node_id: str,
        node_type: str,
        name: str,
        content: Optional[str] = None,
        chapter_num: Optional[int] = None,
        page_start: Optional[int] = None,
        page_end: Optional[int] = None,
        embedding: Optional[list[float]] = None,
    ) -> str:
        """Add a node to the knowledge graph."""
        chromadb_id = None

        # Store embedding in ChromaDB if provided
        if embedding is not None and content is not None:
            chromadb_id = f"vec_{node_id}"
            self.collection.add(
                ids=[chromadb_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[{
                    "node_id": node_id,
                    "type": node_type,
                    "chapter_num": chapter_num if chapter_num is not None else -1,
                }],
            )

        # Store node in SQLite
        self.db.execute(
            """
            INSERT OR REPLACE INTO nodes
            (id, type, name, content, chapter_num, page_start, page_end, chromadb_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (node_id, node_type, name, content, chapter_num, page_start, page_end, chromadb_id),
        )
        self.db.commit()
        return node_id

    def get_node(self, node_id: str) -> Optional[dict]:
        """Get a node by ID."""
        cursor = self.db.execute(
            "SELECT * FROM nodes WHERE id = ?", (node_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        confidence: float = 1.0,
    ):
        """Add an edge between two nodes."""
        self.db.execute(
            """
            INSERT INTO edges (source_id, target_id, relationship, confidence)
            VALUES (?, ?, ?, ?)
            """,
            (source_id, target_id, relationship, confidence),
        )
        self.db.commit()

    def get_children(self, node_id: str, relationship: str = "contains") -> list[dict]:
        """Get child nodes (outgoing edges)."""
        cursor = self.db.execute(
            """
            SELECT n.* FROM nodes n
            JOIN edges e ON n.id = e.target_id
            WHERE e.source_id = ? AND e.relationship = ?
            """,
            (node_id, relationship),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_related(
        self,
        node_id: str,
        relationship: Optional[str] = None,
    ) -> list[dict]:
        """Get related nodes (both directions)."""
        if relationship:
            cursor = self.db.execute(
                """
                SELECT n.*, e.relationship, e.confidence FROM edges e
                LEFT JOIN nodes n ON (n.id = e.target_id AND e.source_id = ?)
                                  OR (n.id = e.source_id AND e.target_id = ?)
                WHERE (e.source_id = ? OR e.target_id = ?) AND e.relationship = ?
                """,
                (node_id, node_id, node_id, node_id, relationship),
            )
        else:
            cursor = self.db.execute(
                """
                SELECT n.*, e.relationship, e.confidence FROM edges e
                LEFT JOIN nodes n ON (n.id = e.target_id AND e.source_id = ?)
                                  OR (n.id = e.source_id AND e.target_id = ?)
                WHERE e.source_id = ? OR e.target_id = ?
                """,
                (node_id, node_id, node_id, node_id),
            )
        return [dict(row) for row in cursor.fetchall()]

    def search_vectors(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        chapter_filter: Optional[int] = None,
    ) -> list[dict]:
        """Search for similar vectors, return node info."""
        where_filter = None
        if chapter_filter is not None:
            where_filter = {"chapter_num": chapter_filter}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        if results["ids"] and results["ids"][0]:
            for i, chromadb_id in enumerate(results["ids"][0]):
                node_id = results["metadatas"][0][i]["node_id"]
                node = self.get_node(node_id)
                if node:
                    output.append({
                        **node,
                        "distance": results["distances"][0][i],
                        "score": 1 - results["distances"][0][i],  # cosine similarity
                    })
        return output

    def close(self):
        """Close database connections."""
        self.db.close()
