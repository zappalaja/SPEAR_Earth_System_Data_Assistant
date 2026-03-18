"""
rag_overview_helpers.py — API client functions for the RAG Overview page.

All calls go to the RAG FastAPI service (default http://localhost:8002).
"""

import os
import requests
from typing import Any, Dict, List, Optional


def _rag_url() -> str:
    return os.getenv("RAG_API_URL", "http://localhost:8002").rstrip("/")


def check_health() -> bool:
    """Return True if the RAG service is reachable."""
    try:
        r = requests.get(f"{_rag_url()}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def list_documents(timeout: int = 15) -> Optional[Dict[str, Any]]:
    """GET /documents — list all documents in ChromaDB."""
    try:
        r = requests.get(f"{_rag_url()}/documents", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def get_manifest(timeout: int = 15) -> Optional[List[Dict[str, Any]]]:
    """GET /manifest — return the ingestion manifest."""
    try:
        r = requests.get(f"{_rag_url()}/manifest", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def get_document_content(title: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
    """GET /documents/{title}/content — return cleaned markdown for a document."""
    try:
        from urllib.parse import quote
        encoded_title = quote(title, safe="")
        r = requests.get(f"{_rag_url()}/documents/{encoded_title}/content", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def delete_document(title: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
    """DELETE /documents/{title} — remove a document from ChromaDB and manifest."""
    try:
        from urllib.parse import quote
        encoded_title = quote(title, safe="")
        r = requests.delete(f"{_rag_url()}/documents/{encoded_title}", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def search_library(query: str, k: int = 10, timeout: int = 15) -> Optional[Dict[str, Any]]:
    """POST /search — keyword search returning document-level results."""
    try:
        r = requests.post(
            f"{_rag_url()}/search",
            json={"query": query, "k": k},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def start_ingestion(files: List[Any], timeout: int = 30) -> Optional[Dict[str, Any]]:
    """POST /ingest — upload PDFs and trigger the ingestion pipeline."""
    try:
        multipart = [("files", (f.name, f.read(), "application/pdf")) for f in files]
        r = requests.post(f"{_rag_url()}/ingest", files=multipart, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def check_ingestion_status(job_id: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """GET /ingest/{job_id}/status — poll ingestion progress."""
    try:
        r = requests.get(f"{_rag_url()}/ingest/{job_id}/status", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}
