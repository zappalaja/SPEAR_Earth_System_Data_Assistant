"""
Document Processor for Reference Materials
===========================================

This module processes PDF and text documents from the reference_documents folder
and makes their content available to the chatbot as additional context.

The system is designed to be simple and lightweight:
1. Scans reference_documents folder at startup
2. Extracts text from PDFs and text files
3. Creates summaries for the knowledge base
4. Makes document list available to chatbot
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import PyPDF2


# ============================================================================
# CONFIGURATION
# ============================================================================

REFERENCE_DOCS_PATH = "reference_documents"
MAX_DOCUMENT_LENGTH = 50000  # Characters (to avoid token limits)
SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".md"]


# ============================================================================
# DOCUMENT EXTRACTION
# ============================================================================

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extract text content from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text as string, or None if extraction fails
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""

            # Extract text from all pages
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"

            return text.strip()

    except Exception as e:
        print(f"Warning: Could not extract text from {pdf_path}: {e}")
        return None


def extract_text_from_txt(txt_path: str) -> Optional[str]:
    """
    Read text from a text file.

    Args:
        txt_path: Path to the text file

    Returns:
        File content as string, or None if reading fails
    """
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            return file.read().strip()

    except Exception as e:
        print(f"Warning: Could not read {txt_path}: {e}")
        return None


def extract_text_from_file(file_path: str) -> Optional[str]:
    """
    Extract text from a file based on its extension.

    Args:
        file_path: Path to the file

    Returns:
        Extracted text, or None if extraction fails
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in [".txt", ".md"]:
        return extract_text_from_txt(file_path)
    else:
        return None


# ============================================================================
# DOCUMENT SCANNING
# ============================================================================

def scan_reference_documents() -> Dict[str, str]:
    """
    Scan the reference_documents folder and extract text from all supported files.

    Returns:
        Dictionary mapping filename to extracted text
    """
    documents = {}

    # Check if reference documents folder exists
    if not os.path.exists(REFERENCE_DOCS_PATH):
        print(f"Warning: {REFERENCE_DOCS_PATH} folder not found")
        return documents

    # Walk through all files in the folder and subfolders
    for root, dirs, files in os.walk(REFERENCE_DOCS_PATH):
        for filename in files:
            # Skip README files
            if filename.lower() == "readme.md":
                continue

            # Check if file extension is supported
            ext = Path(filename).suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            # Get full file path
            file_path = os.path.join(root, filename)

            # Extract text
            text = extract_text_from_file(file_path)

            if text:
                # Truncate if too long
                if len(text) > MAX_DOCUMENT_LENGTH:
                    text = text[:MAX_DOCUMENT_LENGTH] + "\n\n[Document truncated due to length...]"

                # Store with relative path as key
                rel_path = os.path.relpath(file_path, REFERENCE_DOCS_PATH)
                documents[rel_path] = text
                print(f"✓ Loaded: {rel_path} ({len(text)} characters)")

    return documents


# ============================================================================
# KNOWLEDGE BASE INTEGRATION
# ============================================================================

def create_document_summary(documents: Dict[str, str]) -> str:
    """
    Create a summary of available documents for the knowledge base.

    Args:
        documents: Dictionary of filename -> text content

    Returns:
        Formatted string summarizing available documents
    """
    if not documents:
        return "\n\n## REFERENCE DOCUMENTS\n\nNo reference documents loaded.\n"

    summary = "\n\n" + "=" * 80 + "\n"
    summary += "REFERENCE DOCUMENTS\n"
    summary += "=" * 80 + "\n\n"
    summary += f"**{len(documents)} document(s) available for reference:**\n\n"

    for filename in sorted(documents.keys()):
        summary += f"- {filename}\n"

    summary += "\n**Important Guidelines for Using Reference Documents:**\n\n"
    summary += "1. When information from these documents is relevant to a user's question, reference them\n"
    summary += "2. Cite the specific document when using information from it\n"
    summary += "3. If a document contradicts the knowledge base, mention both and note the source\n"
    summary += "4. These documents provide SPEAR-specific details that enhance the base knowledge\n"
    summary += "5. Increase confidence ratings when responses are backed by official documentation\n\n"

    summary += "**Document Content Preview:**\n\n"

    # Add brief preview of each document (first 500 chars)
    for filename, text in sorted(documents.items()):
        summary += f"### {filename}\n"
        preview = text[:500].replace('\n', ' ').strip()
        summary += f"{preview}...\n\n"

    return summary


def build_documents_prompt() -> str:
    """
    Build the reference documents section for the system prompt.

    Returns:
        Formatted prompt section with document information
    """
    try:
        # Scan for documents
        documents = scan_reference_documents()

        # Create summary
        summary = create_document_summary(documents)

        return summary

    except Exception as e:
        print(f"Warning: Error loading reference documents: {e}")
        return "\n\n## REFERENCE DOCUMENTS\n\nError loading reference documents.\n"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def list_available_documents() -> List[str]:
    """
    Get list of available reference documents.

    Returns:
        List of document filenames
    """
    documents = scan_reference_documents()
    return sorted(documents.keys())


def get_document_content(filename: str) -> Optional[str]:
    """
    Get the full content of a specific document.

    Args:
        filename: Name or relative path of the document

    Returns:
        Document text content, or None if not found
    """
    documents = scan_reference_documents()
    return documents.get(filename)


def search_documents(query: str) -> Dict[str, List[str]]:
    """
    Simple keyword search across all documents.

    Args:
        query: Search term

    Returns:
        Dictionary mapping filename to matching lines
    """
    documents = scan_reference_documents()
    results = {}

    query_lower = query.lower()

    for filename, text in documents.items():
        matching_lines = []
        for line in text.split('\n'):
            if query_lower in line.lower():
                matching_lines.append(line.strip())

        if matching_lines:
            results[filename] = matching_lines[:5]  # Limit to 5 matches per document

    return results


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("Scanning reference documents...")
    print("=" * 60)

    documents = scan_reference_documents()

    if documents:
        print(f"\n Found {len(documents)} document(s):\n")
        for filename, text in documents.items():
            print(f" {filename}")
            print(f"     - Length: {len(text):,} characters")
            print(f"     - Preview: {text[:100].replace(chr(10), ' ')}...")
            print()
    else:
        print("\n No documents found")
        print(f"\nPlace PDF, TXT, or MD files in the '{REFERENCE_DOCS_PATH}' folder")
        print("Then run this script again to test document loading")

    print("\n" + "=" * 60)
    print("Document processor ready")
