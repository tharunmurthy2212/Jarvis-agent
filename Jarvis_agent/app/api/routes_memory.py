from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from app.schemas.api import MemoryItem, CreateMemoryRequest
from app.memory.store import memory_store

router = APIRouter(prefix="/api/memory", tags=["Long-term Memory"])


@router.get("", response_model=List[MemoryItem], summary="List stored memories and user preferences")
async def list_memories(
    category: Optional[str] = Query(None, description="Filter memories by category")
) -> List[MemoryItem]:
    return memory_store.list_memories(category=category)


@router.post("", response_model=MemoryItem, status_code=201, summary="Store a new memory or preference")
async def create_memory(request: CreateMemoryRequest) -> MemoryItem:
    return memory_store.add_memory(content=request.content, category=request.category)


@router.delete("/{memory_id}", summary="Delete a specific memory")
async def delete_memory(
    memory_id: str = Path(..., description="UUID of memory to delete")
):
    deleted = memory_store.delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory record not found.")
    return {"status": "success", "message": f"Memory '{memory_id}' deleted."}


@router.delete("", summary="Clear all long-term memories")
async def clear_all_memories():
    count = memory_store.clear_all_memories()
    return {"status": "success", "message": f"Cleared {count} memory record(s)."}
