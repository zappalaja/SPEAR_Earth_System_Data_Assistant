#!/usr/bin/env python3
"""Ingest merged Markdown into Chroma (no queries, no sanity checks)."""

import argparse
import json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md_dir", required=True)
    ap.add_argument("--chroma_dir", required=True)
    ap.add_argument("--collection", required=True)
    ap.add_argument("--embedding_model", required=True)
    ap.add_argument("--chunk_size", type=int, default=1200)
    ap.add_argument("--chunk_overlap", type=int, default=150)
    args = ap.parse_args()

    md_dir = Path(args.md_dir).expanduser().resolve()
    chroma_dir = Path(args.chroma_dir).expanduser().resolve()
    chroma_dir.mkdir(parents=True, exist_ok=True)

    from langchain_community.document_loaders import DirectoryLoader, TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma

    # Load manifest to get PDF titles
    manifest_path = md_dir / "manifest.json"
    source_to_title = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest:
            if entry.get("merged_md") and entry.get("pdf"):
                # Map merged_md path to PDF filename (which contains the title)
                merged_path = Path(entry["merged_md"]).resolve()
                pdf_title = entry["pdf"].replace(".pdf", "")
                source_to_title[str(merged_path)] = pdf_title
        print(f"Loaded {len(source_to_title)} title mappings from manifest.json")
    else:
        print("Warning: manifest.json not found, titles will not be added to metadata")

    loader = DirectoryLoader(
        str(md_dir),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    docs = loader.load()
    print(f"Loaded {len(docs)} markdown docs from {md_dir}")

    # Add title metadata to each document
    for doc in docs:
        source = str(Path(doc.metadata.get("source", "")).resolve())
        if source in source_to_title:
            doc.metadata["title"] = source_to_title[source]
        else:
            # Fallback: use filename stem as title
            doc.metadata["title"] = Path(source).stem

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    chunks = splitter.split_documents(docs)
    print(f"Chunked into {len(chunks)} total chunks.")

    emb = HuggingFaceEmbeddings(model_name=args.embedding_model)

    ids = []
    for i, d in enumerate(chunks):
        src = (d.metadata.get("source") or "unknown").replace("\\", "/")
        ids.append(f"{src}::chunk{i}")

    vs = Chroma(
        collection_name=args.collection,
        embedding_function=emb,
        persist_directory=str(chroma_dir),
    )

    vs.add_documents(chunks, ids=ids)
    vs.persist()

    print(f"Added/updated {len(chunks)} chunks into collection='{args.collection}'")
    print(f"Persist dir: {chroma_dir}")

if __name__ == "__main__":
    main()
