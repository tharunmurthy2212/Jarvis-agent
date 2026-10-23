from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Path
from app.schemas.api import DocumentMetadata, DocumentQueryRequest, DocumentQueryResult
from app.documents.store import document_store
from app.documents.retrieval import DocumentRetriever
from app.core.exceptions import DocumentProcessingError
from app.core.logger import logger

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("", response_model=DocumentMetadata, status_code=201, summary="Upload and extract document")
async def upload_document(
    file: UploadFile = File(...)
) -> DocumentMetadata:
    """
    Upload and index a PDF, DOCX, TXT, or CSV document for JARVIS grounding.
    """
    try:
        content_bytes = await file.read()
        metadata = document_store.process_and_save(
            filename=file.filename or "uploaded_document.txt",
            content_bytes=content_bytes
        )
        return metadata
    except DocumentProcessingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to ingest uploaded document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process document upload.")


@router.get("", response_model=List[DocumentMetadata], summary="List all indexed documents")
async def list_documents() -> List[DocumentMetadata]:
    return document_store.list_documents()


@router.get("/{document_id}", response_model=DocumentMetadata, summary="Get document metadata")
async def get_document(
    document_id: str = Path(..., description="Document UUID")
) -> DocumentMetadata:
    doc = document_store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.delete("/{document_id}", summary="Delete document and extracted content")
async def delete_document(
    document_id: str = Path(..., description="Document UUID to delete")
):
    deleted = document_store.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"status": "success", "message": f"Document '{document_id}' deleted."}


@router.post("/{document_id}/query", response_model=List[DocumentQueryResult], summary="Query document passages")
async def query_document(
    document_id: str,
    request: DocumentQueryRequest
) -> List[DocumentQueryResult]:
    doc = document_store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    results = DocumentRetriever.query(
        query_text=request.query,
        document_ids=[document_id],
        top_k=request.top_k
    )
    return results
