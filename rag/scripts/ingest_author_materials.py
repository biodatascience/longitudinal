"""One-off ingest of the FLW companion materials (author BIO226 slides + book TOC)
into the bios667_corpus collection with dedicated source_types so they are queryable
via CorpusQuery.search_all(..., source_type='author_slides' | 'book_toc').

Reuses the prose chunker (via source_type='slides' for chunking) and overrides the
stored source_type. Idempotent (upsert by deterministic chunk_id)."""
import fitz  # pymupdf
import chromadb
from chromadb.config import Settings

from bios667_rag.loaders.base import RawDoc
from bios667_rag.chunk import chunk_document
from bios667_rag.metadata import ChunkMeta, make_chunk_id
from bios667_rag.embed import Embedder

STORE = "/home/naimrashid/Dropbox/UNC_bios_line/BIOS667/new/rag/data/chroma"
COMP = "/home/naimrashid/Dropbox/UNC_bios_line/BIOS667/new/book/ala2e_companion"

MATERIALS = [
    {"path": f"{COMP}/author_slides_BIO226_color.pdf",
     "source_type": "author_slides",
     "title": "FLW BIO 226 author lecture slides (Fitzmaurice/Coull/Ware)",
     "year": 2007},
    {"path": f"{COMP}/book_table_of_contents.pdf",
     "source_type": "book_toc",
     "title": "FLW (2011) Applied Longitudinal Analysis: book table of contents",
     "year": 2011},
]


def extract_text(path):
    doc = fitz.open(path)
    pages = [doc[i].get_text() for i in range(doc.page_count)]
    doc.close()
    return "\n\n".join(pages)


def main():
    client = chromadb.PersistentClient(path=STORE, settings=Settings(anonymized_telemetry=False))
    col = client.get_or_create_collection("bios667_corpus", metadata={"hnsw:space": "cosine"})
    before = col.count()
    embedder = Embedder()

    total = 0
    for m in MATERIALS:
        text = extract_text(m["path"])
        # Chunk with the prose path (source_type='slides'), then override the stored type.
        rd = RawDoc(text=text, source_path=m["path"], source_type="slides", native_metadata={})
        chunks = chunk_document(rd)
        ids, docs, metas = [], [], []
        for i, (ctext, _ctype) in enumerate(chunks):
            if not ctext.strip():
                continue
            cid = make_chunk_id(m["path"], i)
            meta = ChunkMeta(
                chunk_id=cid, source_type=m["source_type"], source_path=m["path"],
                title=m["title"], chapters=[], topic_tags=[], year=m["year"],
                dataset_refs=[], is_solution=False, chunk_type="content",
            )
            ids.append(cid); docs.append(ctext); metas.append(meta.to_chroma())
        embs = embedder.embed(docs)
        # upsert in batches to stay well under any single-call limits
        B = 256
        for j in range(0, len(ids), B):
            col.upsert(ids=ids[j:j+B], embeddings=embs[j:j+B],
                       documents=docs[j:j+B], metadatas=metas[j:j+B])
        print(f"  {m['source_type']:14} {len(ids):4} chunks from {m['path'].split('/')[-1]}")
        total += len(ids)

    after = col.count()
    print(f"collection: {before} -> {after} (+{after-before}); ingested {total} chunks")


if __name__ == "__main__":
    main()
