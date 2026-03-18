"""
RAG Overview — View, search, and manage documents in the SPEAR RAG database.

Accessible from the Streamlit sidebar. Requires authentication if AUTH_ENABLED=true.
"""

import os
import sys
import time
import streamlit as st
from dotenv import load_dotenv

# Ensure the chatbot directory is on the path so helpers can be imported
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

from shared_styles import apply_sidebar_background
apply_sidebar_background()

from rag_overview_helpers import (
    check_health,
    list_documents,
    get_manifest,
    get_document_content,
    delete_document,
    search_library,
    start_ingestion,
    check_ingestion_status,
)

# ── Auth gate ────────────────────────────────────────────────────────────────
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
if AUTH_ENABLED:
    if not st.session_state.get("authentication_status"):
        st.warning("Please log in from the main page to access this section.")
        st.stop()

# ── Sidebar profile ─────────────────────────────────────────────────────────
from auth_setup import render_sidebar_profile
render_sidebar_profile(page_key="rag")

# ── Page config ──────────────────────────────────────────────────────────────
st.title("RAG Document Library")
st.caption("View, search, and ingest documents in the SPEAR knowledge base")

# ── Server health ────────────────────────────────────────────────────────────
rag_url = os.getenv("RAG_API_URL", "http://localhost:8002")
if check_health():
    st.success(f"RAG service is reachable at `{rag_url}`")
else:
    st.error(f"Cannot reach RAG service at `{rag_url}`")
    st.info("Make sure the RAG service is running. Features will not work while the service is offline.")
    st.stop()

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_view, tab_search, tab_ingest = st.tabs(["View Documents", "Search Library", "Ingest New Documents"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: View Documents
# ═══════════════════════════════════════════════════════════════════════════════
with tab_view:
    if st.button("Refresh Document List", key="refresh_docs"):
        st.session_state.pop("_rag_doc_list", None)

    # Cache the document list in session state to avoid re-fetching on every rerun
    if "_rag_doc_list" not in st.session_state:
        with st.spinner("Loading documents from RAG database..."):
            st.session_state._rag_doc_list = list_documents()

    doc_data = st.session_state._rag_doc_list

    if doc_data and "error" in doc_data:
        st.error(f"Could not reach RAG service: {doc_data['error']}")
    elif doc_data and "documents" in doc_data:
        docs = doc_data["documents"]
        st.markdown(f"**{doc_data['total_documents']}** documents in the database")

        if not docs:
            st.info("No documents found. Use the **Ingest New Documents** tab to add some.")
        else:
            for i, doc in enumerate(docs):
                with st.expander(f"{doc['title']}  ({doc['chunk_count']} chunks)"):
                    st.markdown(f"**Source PDF:** `{doc['source_pdf']}`")

                    col_read, col_delete = st.columns([1, 1])

                    # Button to load and display full content
                    with col_read:
                        if st.button("Read Document", key=f"read_{i}"):
                            with st.spinner("Loading document content..."):
                                result = get_document_content(doc["title"])

                            if result and "error" in result:
                                st.error(f"Failed to load: {result['error']}")
                            elif result and "content" in result:
                                st.markdown("---")
                                st.markdown(result["content"])
                            else:
                                st.warning("No content returned.")

                    # Delete button with confirmation
                    with col_delete:
                        confirm_key = f"confirm_del_{i}"
                        if confirm_key not in st.session_state:
                            st.session_state[confirm_key] = False

                        if not st.session_state[confirm_key]:
                            if st.button("Delete Document", key=f"del_{i}", type="secondary"):
                                st.session_state[confirm_key] = True
                                st.rerun()
                        else:
                            st.warning(f"Delete **{doc['title']}**? This cannot be undone.")
                            col_yes, col_no = st.columns(2)
                            with col_yes:
                                if st.button("Yes, delete", key=f"del_yes_{i}", type="primary"):
                                    with st.spinner("Deleting..."):
                                        result = delete_document(doc["title"])
                                    if result and "error" in result:
                                        st.error(f"Delete failed: {result['error']}")
                                    else:
                                        st.success(
                                            f"Deleted {result.get('chunks_removed', '?')} chunks."
                                        )
                                        st.session_state.pop("_rag_doc_list", None)
                                        st.session_state[confirm_key] = False
                                        st.rerun()
                            with col_no:
                                if st.button("Cancel", key=f"del_no_{i}"):
                                    st.session_state[confirm_key] = False
                                    st.rerun()
    else:
        st.warning("Unexpected response from RAG service.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: Search Library
# ═══════════════════════════════════════════════════════════════════════════════
with tab_search:
    st.markdown("Search across all documents by keyword.")

    query = st.text_input("Search query", placeholder="e.g., tropical cyclone, SPEAR, ocean model")
    num_results = st.slider("Max results", min_value=1, max_value=20, value=5)

    if st.button("Search", key="search_btn") and query.strip():
        with st.spinner("Searching..."):
            results = search_library(query.strip(), k=num_results)

        if results and "error" in results:
            st.error(f"Search failed: {results['error']}")
        elif results and "results" in results:
            if not results["results"]:
                st.info("No matching documents found.")
            else:
                for j, hit in enumerate(results["results"]):
                    st.markdown(f"### {j + 1}. {hit['title']}")
                    st.markdown(f"**Keyword matches:** {hit['match_count']}")
                    st.markdown(f"> {hit['best_snippet']}...")

                    if st.button("Read Full Document", key=f"search_read_{j}"):
                        with st.spinner("Loading..."):
                            content = get_document_content(hit["title"])
                        if content and "content" in content:
                            st.markdown("---")
                            st.markdown(content["content"])
                        elif content and "error" in content:
                            st.error(content["error"])

                    st.markdown("---")
        else:
            st.warning("Unexpected response.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: Ingest New Documents
# ═══════════════════════════════════════════════════════════════════════════════
with tab_ingest:
    st.markdown(
        "Upload PDF documents to add them to the RAG knowledge base. "
        "Documents are processed with **Nougat OCR** for high-quality text extraction, "
        "then chunked and embedded into the vector database. "
        "Pages which are difficult for Nougat OCR text extraction fallback to **PyPDF** "
        "(usually pages with figures)."
    )
    st.warning(
        "Nougat OCR can be slow, especially without GPU access. "
        "Processing may take several minutes per document."
    )

    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        key="pdf_uploader",
    )

    if uploaded_files and st.button("Start Ingestion", key="ingest_btn"):
        with st.status("Ingesting documents...", expanded=True) as status:
            st.write(f"Uploading {len(uploaded_files)} file(s)...")
            result = start_ingestion(uploaded_files)

            if result and "error" in result:
                status.update(label="Ingestion failed", state="error")
                st.error(f"Upload failed: {result['error']}")

            elif result and result.get("status") == "skipped":
                # All files were duplicates
                status.update(label="No new documents", state="complete")
                st.info(result.get("message", "All files already exist in the database."))
                if result.get("skipped_duplicates"):
                    st.write("**Skipped (already ingested):**")
                    for name in result["skipped_duplicates"]:
                        st.write(f"- {name}")

            elif result and result.get("job_id"):
                job_id = result["job_id"]
                st.write(f"Job started: `{job_id}`")

                # Show skipped duplicates if any
                if result.get("skipped_duplicates"):
                    st.info(
                        f"Skipped {len(result['skipped_duplicates'])} duplicate(s): "
                        + ", ".join(result["skipped_duplicates"])
                    )

                # Poll for status
                while True:
                    time.sleep(5)
                    poll = check_ingestion_status(job_id)

                    if poll and "error" in poll:
                        status.update(label="Ingestion failed", state="error")
                        st.error(f"Status check failed: {poll['error']}")
                        break

                    job_status = poll.get("status", "unknown")
                    elapsed = poll.get("elapsed_seconds", 0)

                    if job_status == "nougat_running":
                        st.write(f"Running Nougat OCR... ({elapsed:.0f}s)")
                    elif job_status == "rag_running":
                        st.write(f"Embedding into vector database... ({elapsed:.0f}s)")
                    elif job_status == "completed":
                        status.update(label="Ingestion complete!", state="complete")
                        st.success("Documents have been added to the RAG database.")
                        # Clear cached doc list so it refreshes
                        st.session_state.pop("_rag_doc_list", None)
                        break
                    elif job_status == "failed":
                        status.update(label="Ingestion failed", state="error")
                        st.error("Pipeline failed. Check logs below.")
                        if poll.get("log"):
                            st.code(poll["log"], language="text")
                        break
                    else:
                        st.write(f"Status: {job_status} ({elapsed:.0f}s)")
            else:
                status.update(label="Ingestion failed", state="error")
                st.error("Unexpected response from ingestion endpoint.")
