import re
import math
from typing import List, Dict, Any, Optional
from collections import Counter
from app.memory.database import get_db_connection
from app.schemas.api import DocumentQueryResult
from app.core.logger import logger


class DocumentRetriever:
    """Retrieves and ranks the most relevant document chunks for grounded AI answers."""

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Convert text to clean lower-case alphanumeric tokens."""
        return re.findall(r'\b[a-zA-Z0-9_]{2,}\b', text.lower())

    @classmethod
    def query(
        cls,
        query_text: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 3
    ) -> List[DocumentQueryResult]:
        """Retrieve top_k matching chunks across specified (or all) documents."""
        query_tokens = cls._tokenize(query_text)
        if not query_tokens:
            return []

        query_tf = Counter(query_tokens)

        with get_db_connection() as conn:
            if document_ids and len(document_ids) > 0:
                placeholders = ",".join("?" for _ in document_ids)
                cursor = conn.execute(
                    f"""
                    SELECT c.id, c.document_id, c.chunk_index, c.content, c.page, d.filename
                    FROM document_chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE c.document_id IN ({placeholders})
                    """,
                    document_ids
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT c.id, c.document_id, c.chunk_index, c.content, c.page, d.filename
                    FROM document_chunks c
                    JOIN documents d ON c.document_id = d.id
                    """
                )
            rows = cursor.fetchall()

        if not rows:
            return []

        scored_results = []
        for r in rows:
            content = r["content"]
            doc_tokens = cls._tokenize(content)
            if not doc_tokens:
                continue

            doc_tf = Counter(doc_tokens)
            doc_len = len(doc_tokens)

            # Compute term overlap score (BM25-like TF scoring)
            score = 0.0
            for term, q_count in query_tf.items():
                if term in doc_tf:
                    tf = doc_tf[term]
                    # Sublinear TF scaling
                    score += (1.0 + math.log(tf)) * (1.0 / (1.0 + math.log(doc_len / 50.0 + 1.0)))

            if score > 0:
                scored_results.append((
                    score,
                    DocumentQueryResult(
                        document_id=r["document_id"],
                        filename=r["filename"],
                        chunk_id=r["chunk_index"],
                        snippet=content,
                        page=r["page"],
                        score=round(score, 4)
                    )
                ))

        # Sort descending by score
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_results[:top_k]]
