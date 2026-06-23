# rag/src/bios667_rag/scripts/index_textbook.py
"""Index the textbook PDFs into the knowledge graph."""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from bios667_rag.extract import extract_pdf_text, extract_pdf_blocks, detect_structure
from bios667_rag.chunk import semantic_chunk
from bios667_rag.embed import Embedder
from bios667_rag.storage import KnowledgeStore
from bios667_rag.graph import KnowledgeGraphBuilder


RAG_DIR = Path(__file__).parent.parent.parent.parent
BOOK_DIR = RAG_DIR.parent / "book"
DATA_DIR = RAG_DIR / "data"


def parse_chapter_num(filename: str) -> int | None:
    """Extract chapter number from filename."""
    chapter_map = {
        "Front Matter": 0,
        "Longitudinal and Clustered Data": 1,
        "Longitudinal Data  Basic Concepts": 2,
        "Overview of Linear Models": 3,
        "Estimation and Statistical Inference": 4,
        "Analyzing Response Profiles": 5,
        "Parametric Curves": 6,
        "Modeling the Covariance": 7,
        "Linear Mixed Effects Models": 8,
        "Fixed Effects versus Random Effects": 9,
        "Residual Analyses": 10,
        "Review of Generalized Linear Models": 11,
        "Marginal Models  Introduction": 12,
        "Generalized Estimating Equations": 13,
        "Generalized Linear Mixed Effects Models": 14,
        "Approximate Methods": 15,
        "Contrasting Marginal and Mixed Effects": 16,
        "Missing Data and Dropout  Overview": 17,
        "Missing Data and Dropout  Multiple Imputation": 18,
        "Sample Size and Power": 19,
        "Multilevel Models": 20,
    }

    for title, num in chapter_map.items():
        if title.lower() in filename.lower():
            return num
    return None


def main():
    """Main indexing function."""
    print("BIOS 667 Textbook Indexer")
    print("=" * 50)

    DATA_DIR.mkdir(exist_ok=True)

    print("\nInitializing components...")
    store = KnowledgeStore(
        db_path=DATA_DIR / "knowledge_graph.db",
        chromadb_path=DATA_DIR / "vectors.chromadb",
    )
    embedder = Embedder()
    builder = KnowledgeGraphBuilder(store)

    print(f"  Embedding model: {embedder.model_name}")
    print(f"  Device: {embedder.device}")
    print(f"  Embedding dimension: {embedder.dimension}")

    pdf_files = sorted(BOOK_DIR.glob("*.pdf"))
    pdf_files = [f for f in pdf_files if "Fitzmaurice.pdf" not in f.name or "-" in f.name]

    print(f"\nFound {len(pdf_files)} chapter PDFs")

    stats = {
        "chapters": 0,
        "sections": 0,
        "chunks": 0,
        "start_time": datetime.now().isoformat(),
    }

    for pdf_path in pdf_files:
        chapter_num = parse_chapter_num(pdf_path.stem)
        if chapter_num is None:
            print(f"  Skipping {pdf_path.name} (unknown chapter)")
            continue

        print(f"\nProcessing Chapter {chapter_num}: {pdf_path.name}")

        pages = extract_pdf_text(pdf_path)
        full_text = "\n\n".join(p["text"] for p in pages)

        blocks = extract_pdf_blocks(pdf_path)
        structure = detect_structure(blocks)

        if structure:
            builder.build_hierarchy(structure)
            stats["sections"] += len([s for s in structure if s["type"] == "section"])

        chapter_id = f"chapter_{chapter_num}"
        if not store.get_node(chapter_id):
            title = pdf_path.stem.split(" - ")[-1].replace("Fitzmaurice - ", "")
            store.add_node(
                node_id=chapter_id, node_type="chapter",
                name=title, chapter_num=chapter_num, page_start=1,
            )
        stats["chapters"] += 1

        chunks = semantic_chunk(full_text, chapter_num=chapter_num)
        print(f"  Created {len(chunks)} chunks")

        chunk_texts = [c.text for c in chunks]
        if chunk_texts:
            embeddings = embedder.embed(chunk_texts)

            for chunk, embedding in zip(chunks, embeddings):
                builder.add_chunk_with_embedding(chunk, embedding)

            stats["chunks"] += len(chunks)

    stats["end_time"] = datetime.now().isoformat()
    with open(DATA_DIR / "index_log.json", "w") as f:
        json.dump(stats, f, indent=2)

    print("\n" + "=" * 50)
    print("Indexing complete!")
    print(f"  Chapters: {stats['chapters']}")
    print(f"  Sections: {stats['sections']}")
    print(f"  Chunks: {stats['chunks']}")
    print(f"  Data saved to: {DATA_DIR}")

    store.close()


if __name__ == "__main__":
    main()
