import json
from typing import List, Dict, Any, Optional
import httpx
from app.llm.base import BaseLLMProvider, LLMResponse, LLMToolCall
from app.core.exceptions import (
    LLMError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.core.logger import logger
from app.core.config import settings


class OpenAICompatibleProvider(BaseLLMProvider):
    """Adapter for OpenAI-compatible chat completion APIs (Groq, OpenAI, OpenRouter, Ollama, etc.)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.default_model = default_model or settings.LLM_MODEL
        self.timeout = timeout or settings.LLM_REQUEST_TIMEOUT

    async def chat_complete(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        endpoint = f"{self.base_url}/chat/completions"
        target_model = model or self.default_model

        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature if temperature is not None else settings.LLM_TEMPERATURE,
            "max_tokens": max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS,
        }

        if tools and len(tools) > 0:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        logger.info(f"Sending LLM request to {endpoint} (model: {target_model}, messages: {len(messages)})")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, headers=headers, json=payload)

                if response.status_code == 401 or response.status_code == 403:
                    raise LLMAuthenticationError(
                        f"Authentication failed with status code {response.status_code}."
                    )
                elif response.status_code == 429:
                    raise LLMRateLimitError(
                        f"Rate limit or quota exceeded with status code 429."
                    )
                elif response.is_error:
                    error_text = response.text[:300]
                    raise LLMError(
                        f"Provider responded with error {response.status_code}: {error_text}"
                    )

                data = response.json()
                return self._parse_response(data, target_model)

        except httpx.TimeoutException:
            raise LLMTimeoutError(f"LLM request timed out after {self.timeout}s.")
        except httpx.ConnectError as e:
            raise LLMError(f"Failed to connect to LLM provider at {self.base_url}: {str(e)}")
        except (LLMAuthenticationError, LLMRateLimitError, LLMTimeoutError, LLMError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error communicating with LLM provider: {e}", exc_info=True)
            raise LLMError(f"LLM communication error: {str(e)}")

    def _parse_response(self, data: Dict[str, Any], model_used: str) -> LLMResponse:
        try:
            choices = data.get("choices", [])
            if not choices:
                return LLMResponse(content="", model_used=model_used, finish_reason="empty")

            first_choice = choices[0]
            message = first_choice.get("message", {})
            content = message.get("content")
            finish_reason = first_choice.get("finish_reason")

            tool_calls: List[LLMToolCall] = []
            raw_tool_calls = message.get("tool_calls", [])

            if raw_tool_calls:
                for tc in raw_tool_calls:
                    tc_id = tc.get("id", "call_default")
                    func = tc.get("function", {})
                    fn_name = func.get("name", "")
                    fn_args_raw = func.get("arguments", "{}")
                    try:
                        if isinstance(fn_args_raw, dict):
                            fn_args = fn_args_raw
                        else:
                            fn_args = json.loads(fn_args_raw) if fn_args_raw else {}
                    except json.JSONDecodeError:
                        fn_args = {"raw": fn_args_raw}

                    tool_calls.append(
                        LLMToolCall(
                            id=tc_id,
                            name=fn_name,
                            arguments=fn_args
                        )
                    )

            usage = data.get("usage", {})
            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                model_used=data.get("model", model_used),
                finish_reason=finish_reason,
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens")
            )
        except Exception as e:
            raise LLMError(f"Failed to parse LLM response format: {str(e)}")
