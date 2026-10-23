from typing import List, Dict, Any, Optional
from app.core.prompts import build_system_prompt
from app.memory.store import memory_store
from app.documents.retrieval import DocumentRetriever
from app.schemas.api import ChatMessage
from app.core.config import settings


class ContextBuilder:
    """Builds structured prompt messages incorporating system persona, memories, documents, and history."""

    @classmethod
    def build_messages(
        cls,
        user_message: str,
        session_id: str,
        use_memory: bool = True,
        document_ids: Optional[List[str]] = None,
        system_prompt_override: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        messages: List[Dict[str, Any]] = []

        # 1. System Prompt
        system_text = build_system_prompt(system_prompt_override)

        # 2. Long-term memory injection
        if use_memory and settings.ENABLE_MEMORY:
            memories_text = memory_store.get_memories_text_context()
            if memories_text:
                system_text += f"\n\n### USER PREFERENCES & MEMORIES\n{memories_text}"

        # 3. Document grounding injection
        if document_ids and len(document_ids) > 0:
            doc_chunks = DocumentRetriever.query(
                query_text=user_message,
                document_ids=document_ids,
                top_k=4
            )
            if doc_chunks:
                doc_text = "\n\n".join(
                    f"--- Source: {c.filename} (Page {c.page or 'N/A'}) ---\n{c.snippet}"
                    for c in doc_chunks
                )
                system_text += (
                    f"\n\n### RELEVANT DOCUMENT EXCERPTS (REFERENCE ONLY)\n"
                    f"{doc_text}\n\n"
                    f"Use the excerpts above to answer accurately. Cite the source document when appropriate."
                )

        messages.append({"role": "system", "content": system_text})

        # 4. Conversation History
        if use_memory:
            history: List[ChatMessage] = memory_store.get_recent_messages(
                session_id=session_id,
                limit=settings.MAX_HISTORY_MESSAGES
            )
            for msg in history:
                msg_dict: Dict[str, Any] = {"role": msg.role, "content": msg.content}
                if msg.tool_call_id:
                    msg_dict["tool_call_id"] = msg.tool_call_id
                if msg.tool_name:
                    msg_dict["name"] = msg.tool_name
                messages.append(msg_dict)

        # 5. Current message (if not already recorded in history)
        if not messages or messages[-1].get("content") != user_message:
            messages.append({"role": "user", "content": user_message})

        return messages
