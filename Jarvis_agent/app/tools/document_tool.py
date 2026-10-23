from typing import Dict, Any, Optional
from app.documents.retrieval import DocumentRetriever


class DocumentTool:
    """Tool allowing JARVIS to inspect and retrieve citations from uploaded files."""

    @staticmethod
    def query_documents(query: str, document_id: Optional[str] = None, top_k: int = 3) -> Dict[str, Any]:
        """Search across stored document chunks for relevant passages."""
        doc_ids = [document_id] if document_id else None
        results = DocumentRetriever.query(query_text=query, document_ids=doc_ids, top_k=top_k)

        if not results:
            return {
                "query": query,
                "count": 0,
                "message": "No matching passages found in the uploaded documents.",
                "results": []
            }

        return {
            "query": query,
            "count": len(results),
            "results": [
                {
                    "document_id": r.document_id,
                    "filename": r.filename,
                    "page": r.page,
                    "snippet": r.snippet,
                    "relevance_score": r.score
                }
                for r in results
            ]
        }
