#!/usr/bin/env python3
"""
Query an existing Chroma collection from the terminal.
"""

import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chroma_dir", required=True, help="Chroma persist directory")
    ap.add_argument("--collection", required=True, help="Collection name")
    ap.add_argument("--query", required=True, help="Query text")
    ap.add_argument("--top_k", type=int, default=5)
    ap.add_argument(
        "--embedding_model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Embedding model used for the collection",
    )
    args = ap.parse_args()

    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma

    emb = HuggingFaceEmbeddings(model_name=args.embedding_model)

    vs = Chroma(
        collection_name=args.collection,
        embedding_function=emb,
        persist_directory=args.chroma_dir,
    )

    results = vs.similarity_search(args.query, k=args.top_k)

    print(f"\nQuery: {args.query}\n")
    for i, r in enumerate(results, 1):
        title = r.metadata.get("title", "Unknown Title")
        src = r.metadata.get("source", "unknown")
        snippet = r.page_content[:500].replace("\n", " ")
        print(f"[{i}] Title: {title}")
        print(f"    Source: {src}")
        print(f"    {snippet}...\n")

if __name__ == "__main__":
    main()

