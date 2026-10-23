import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import DocumentNotFoundError, DocumentProcessingError
from app.memory.database import get_db_connection
from app.schemas.api import DocumentMetadata
from app.documents.extractor import DocumentExtractor


class DocumentStore:
    """Manages document storage, chunking, and database metadata."""

    def __init__(self, storage_dir: str | None = None):
        self.storage_dir = Path(storage_dir or settings.DOCUMENTS_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _chunk_text(self, text: str, page: Optional[int] = None) -> List[Dict[str, Any]]:
        """Split text into overlapping chunk windows."""
        chunk_size = settings.DOCUMENT_CHUNK_SIZE
        overlap = settings.DOCUMENT_CHUNK_OVERLAP
        chunks = []

        if len(text) <= chunk_size:
            return [{"content": text, "page": page}]

        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append({"content": chunk, "page": page})
            if end >= len(text):
                break
            start += chunk_size - overlap

        return chunks

    def process_and_save(self, filename: str, content_bytes: bytes) -> DocumentMetadata:
        """Extract, chunk, persist to SQLite and disk."""
        # Sanitize filename
        safe_filename = Path(filename).name
        ext = Path(safe_filename).suffix.lower()

        # Extract text & pages
        full_text, sections = DocumentExtractor.extract_text(safe_filename, content_bytes)

        doc_id = str(uuid.uuid4())
        file_path = self.storage_dir / f"{doc_id}{ext}"

        # Save to disk safely
        file_path.write_bytes(content_bytes)

        # Generate chunks
        all_chunks: List[Dict[str, Any]] = []
        for sec in sections:
            sec_chunks = self._chunk_text(sec["text"], page=sec.get("page"))
            all_chunks.extend(sec_chunks)

        if not all_chunks:
            all_chunks = [{"content": "[No extractable text]", "page": 1}]

        # Create quick summary preview
        summary_preview = (full_text[:300] + "...") if len(full_text) > 300 else full_text
        now = self._now()

        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO documents (id, filename, file_type, file_size_bytes, char_count, uploaded_at, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    safe_filename,
                    ext.replace(".", ""),
                    len(content_bytes),
                    len(full_text),
                    now,
                    summary_preview
                )
            )

            for idx, chunk in enumerate(all_chunks):
                conn.execute(
                    """
                    INSERT INTO document_chunks (document_id, chunk_index, content, page)
                    VALUES (?, ?, ?, ?)
                    """,
                    (doc_id, idx, chunk["content"], chunk.get("page"))
                )

        logger.info(f"Ingested document '{safe_filename}' as ID {doc_id} with {len(all_chunks)} chunks.")

        return DocumentMetadata(
            id=doc_id,
            filename=safe_filename,
            file_type=ext.replace(".", ""),
            file_size_bytes=len(content_bytes),
            char_count=len(full_text),
            chunk_count=len(all_chunks),
            uploaded_at=now,
            summary=summary_preview
        )

    def list_documents(self) -> List[DocumentMetadata]:
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                SELECT d.id, d.filename, d.file_type, d.file_size_bytes, d.char_count,
                       d.uploaded_at, d.summary, COUNT(c.id) as chunk_count
                FROM documents d
                LEFT JOIN document_chunks c ON d.id = c.document_id
                GROUP BY d.id
                ORDER BY d.uploaded_at DESC
                """
            )
            rows = cursor.fetchall()
            return [
                DocumentMetadata(
                    id=r["id"],
                    filename=r["filename"],
                    file_type=r["file_type"],
                    file_size_bytes=r["file_size_bytes"],
                    char_count=r["char_count"],
                    chunk_count=r["chunk_count"],
                    uploaded_at=r["uploaded_at"],
                    summary=r["summary"]
                )
                for r in rows
            ]

    def get_document(self, doc_id: str) -> Optional[DocumentMetadata]:
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                SELECT d.id, d.filename, d.file_type, d.file_size_bytes, d.char_count,
                       d.uploaded_at, d.summary, COUNT(c.id) as chunk_count
                FROM documents d
                LEFT JOIN document_chunks c ON d.id = c.document_id
                WHERE d.id = ?
                GROUP BY d.id
                """,
                (doc_id,)
            )
            r = cursor.fetchone()
            if not r:
                return None
            return DocumentMetadata(
                id=r["id"],
                filename=r["filename"],
                file_type=r["file_type"],
                file_size_bytes=r["file_size_bytes"],
                char_count=r["char_count"],
                chunk_count=r["chunk_count"],
                uploaded_at=r["uploaded_at"],
                summary=r["summary"]
            )

    def delete_document(self, doc_id: str) -> bool:
        with get_db_connection() as conn:
            cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            affected = cursor.rowcount > 0

        # Remove local file if present
        for f in self.storage_dir.glob(f"{doc_id}.*"):
            try:
                f.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Could not remove physical file {f}: {e}")

        return affected


document_store = DocumentStore()
