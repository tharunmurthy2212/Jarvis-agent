import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import JarvisError, LLMError, LLMAuthenticationError, LLMRateLimitError, LLMTimeoutError
from app.schemas.api import ChatRequest, ChatResponse, ToolCallResult
from app.memory.store import memory_store
from app.tools.registry import tool_registry
from app.llm.factory import get_llm_provider
from app.llm.tts_adapter import tts_adapter
from app.assistant.context import ContextBuilder


class AssistantEngine:
    """Core conversation orchestrator for JARVIS."""

    def __init__(self):
        self.tool_registry = tool_registry
        self.memory_store = memory_store

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        session_id = self.memory_store.get_or_create_session(request.session_id)
        now_str = datetime.now(timezone.utc).isoformat()

        # Record user message in store if memory is active
        if request.use_memory:
            self.memory_store.add_message(
                session_id=session_id,
                role="user",
                content=request.message
            )

        # Build initial conversation context
        messages = ContextBuilder.build_messages(
            user_message=request.message,
            session_id=session_id,
            use_memory=request.use_memory,
            document_ids=request.document_ids
        )

        tools_schema = self.tool_registry.get_openai_tools()
        provider = get_llm_provider()
        all_executed_tool_results: List[ToolCallResult] = []
        iteration = 0
        final_reply = ""
        model_used = request.model_override or settings.LLM_MODEL

        try:
            while iteration < settings.MAX_TOOL_ITERATIONS:
                iteration += 1

                # Query LLM Provider
                llm_response = await provider.chat_complete(
                    messages=messages,
                    tools=tools_schema if tools_schema else None,
                    model=model_used,
                    temperature=request.temperature_override,
                )
                model_used = llm_response.model_used

                # If no tool calls, we have our final reply
                if not llm_response.tool_calls:
                    final_reply = llm_response.content or "I have processed your request, sir."
                    break

                # Process tool calls
                logger.info(f"Iteration {iteration}: Assistant requested {len(llm_response.tool_calls)} tool call(s).")

                # Append assistant tool-call intention to message history
                tool_calls_payload = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments) if isinstance(tc.arguments, dict) else str(tc.arguments)
                        }
                    }
                    for tc in llm_response.tool_calls
                ]
                messages.append({
                    "role": "assistant",
                    "content": llm_response.content or "",
                    "tool_calls": tool_calls_payload
                })

                # Execute requested tools
                for tc in llm_response.tool_calls:
                    exec_result = await self.tool_registry.execute(tc.name, tc.arguments)
                    tool_result_obj = ToolCallResult(
                        tool_name=tc.name,
                        tool_args=tc.arguments,
                        result=exec_result.get("result"),
                        status=exec_result.get("status", "success"),
                        execution_time_ms=exec_result.get("execution_time_ms")
                    )
                    all_executed_tool_results.append(tool_result_obj)

                    # Feed tool output back to model
                    tool_output_str = (
                        json.dumps(exec_result.get("result"))
                        if not isinstance(exec_result.get("result"), str)
                        else exec_result.get("result")
                    )
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.name,
                        "content": tool_output_str
                    })

                    # If memory enabled, record tool transaction in message store
                    if request.use_memory:
                        self.memory_store.add_message(
                            session_id=session_id,
                            role="tool",
                            content=tool_output_str,
                            tool_call_id=tc.id,
                            tool_name=tc.name
                        )

            if not final_reply and iteration >= settings.MAX_TOOL_ITERATIONS:
                final_reply = "I completed the requested operations, but reached the maximum tool reasoning depth."

        except LLMAuthenticationError as e:
            final_reply = "I encountered an authentication error communicating with the AI provider. Please verify your LLM_API_KEY in configuration."
            logger.warning(f"LLM auth error: {e}")
        except LLMRateLimitError as e:
            final_reply = "The AI provider rate limit or quota has been reached. Please try again in a few moments."
            logger.warning(f"LLM rate limit error: {e}")
        except LLMTimeoutError as e:
            final_reply = "The AI provider request timed out. Please retry your request."
            logger.warning(f"LLM timeout error: {e}")
        except LLMError as e:
            final_reply = f"I encountered a communication issue with the AI provider: {e.safe_message}"
            logger.error(f"LLM error: {e}")
        except Exception as e:
            final_reply = "An unexpected error occurred while processing your request. Please try again."
            logger.error(f"Unexpected engine error: {e}", exc_info=True)

        # Record assistant reply to memory store
        if request.use_memory:
            self.memory_store.add_message(
                session_id=session_id,
                role="assistant",
                content=final_reply
            )

        # Optional Voice TTS synthesis
        audio_url: Optional[str] = None
        if request.generate_voice:
            try:
                audio_url = await tts_adapter.synthesize(final_reply)
            except Exception as e:
                logger.warning(f"Voice synthesis failed: {e}")

        return ChatResponse(
            session_id=session_id,
            reply=final_reply,
            tool_calls=all_executed_tool_results,
            audio_url=audio_url,
            model_used=model_used,
            timestamp=now_str
        )


# Singleton assistant engine
assistant_engine = AssistantEngine()
