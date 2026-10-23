import time
import inspect
from typing import Dict, Any, Callable, List, Optional
from pydantic import BaseModel
from app.core.logger import logger
from app.tools.calculator import SafeCalculator
from app.tools.datetime_tool import DateTimeTool
from app.tools.web_search import WebSearchTool
from app.tools.document_tool import DocumentTool


class ToolDefinition:
    """Metadata and execution handler for an approved tool."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
        permission: str = "safe"
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.permission = permission

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert tool definition to OpenAI function call format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class ToolRegistry:
    """Central registry and executor for approved assistant tools."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register(self, tool: ToolDefinition) -> None:
        """Register a new tool."""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: '{tool.name}' (Permission: {tool.permission})")

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Return list of tool definitions in OpenAI schema format."""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    async def execute(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with error isolation, timing, and parameter validation."""
        tool = self.get_tool(name)
        if not tool:
            return {
                "tool_name": name,
                "status": "error",
                "result": f"Unknown tool '{name}'. Available tools: {', '.join(self.list_tool_names())}",
                "execution_time_ms": 0.0
            }

        start = time.perf_counter()
        try:
            # Check if handler is coroutine
            if inspect.iscoroutinefunction(tool.handler):
                result = await tool.handler(**arguments)
            else:
                result = tool.handler(**arguments)

            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "tool_name": name,
                "status": "success",
                "result": result,
                "execution_time_ms": elapsed_ms
            }
        except TypeError as e:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.warning(f"Invalid arguments for tool '{name}': {e}")
            return {
                "tool_name": name,
                "status": "error",
                "result": f"Invalid arguments supplied for tool '{name}': {str(e)}",
                "execution_time_ms": elapsed_ms
            }
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
            return {
                "tool_name": name,
                "status": "error",
                "result": f"Tool execution failed: {str(e)}",
                "execution_time_ms": elapsed_ms
            }

    def _register_default_tools(self) -> None:
        """Register the baseline approved tools."""

        # 1. Calculator
        self.register(
            ToolDefinition(
                name="calculator",
                description="Safely evaluate mathematical formulas, arithmetic, exponentiation, trigonometry, square root, and log expressions.",
                parameters={
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate, e.g. '(125 * 4.5) / sqrt(16)'"
                        }
                    },
                    "required": ["expression"]
                },
                handler=SafeCalculator.evaluate
            )
        )

        # 2. DateTime Tool
        self.register(
            ToolDefinition(
                name="get_current_datetime",
                description="Get live verified system date, time, day of week, and timezone from the local computer.",
                parameters={
                    "type": "object",
                    "properties": {
                        "tz_name": {
                            "type": "string",
                            "description": "Optional IANA timezone name, e.g. 'America/New_York', 'UTC', 'Asia/Kolkata'. Defaults to local system timezone."
                        }
                    }
                },
                handler=DateTimeTool.get_current_datetime
            )
        )

        self.register(
            ToolDefinition(
                name="calculate_date_offset",
                description="Calculate a future or past date/time by adding or subtracting days, hours, or minutes.",
                parameters={
                    "type": "object",
                    "properties": {
                        "days": {"type": "integer", "description": "Days offset (positive or negative)"},
                        "hours": {"type": "integer", "description": "Hours offset"},
                        "minutes": {"type": "integer", "description": "Minutes offset"},
                        "base_iso": {"type": "string", "description": "Optional starting ISO date string"}
                    }
                },
                handler=DateTimeTool.calculate_date_offset
            )
        )

        # 3. Web Search
        self.register(
            ToolDefinition(
                name="web_search",
                description="Search the live web for fresh information, recent news, or reference articles.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search terms to look up on the web"},
                        "max_results": {"type": "integer", "description": "Number of results to return (1-5)"}
                    },
                    "required": ["query"]
                },
                handler=WebSearchTool.search
            )
        )

        # 4. Document Query Tool
        self.register(
            ToolDefinition(
                name="document_query",
                description="Search and extract cited passages from uploaded user documents (PDF, DOCX, TXT, CSV).",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Keywords or question regarding the documents"},
                        "document_id": {"type": "string", "description": "Optional specific document ID to restrict search"},
                        "top_k": {"type": "integer", "description": "Number of relevant snippets to retrieve"}
                    },
                    "required": ["query"]
                },
                handler=DocumentTool.query_documents
            )
        )


# Singleton registry
tool_registry = ToolRegistry()
