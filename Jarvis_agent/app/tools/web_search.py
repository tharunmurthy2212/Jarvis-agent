from typing import Dict, Any, List
from app.core.config import settings
from app.core.logger import logger

try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False


class WebSearchTool:
    """Provider-independent web search tool."""

    @staticmethod
    def search(query: str, max_results: int = 5) -> Dict[str, Any]:
        """Execute a web search and return structured source attributions."""
        if not query or not query.strip():
            return {"error": "Search query cannot be empty.", "results": []}

        limit = min(max(1, max_results), settings.SEARCH_MAX_RESULTS)

        if settings.SEARCH_PROVIDER == "none":
            return {
                "notice": "Web search is disabled in configuration (SEARCH_PROVIDER='none').",
                "results": []
            }

        # Try DuckDuckGo
        if HAS_DDGS:
            try:
                results: List[Dict[str, str]] = []
                with DDGS() as ddgs:
                    raw_results = list(ddgs.text(query.strip(), max_results=limit))
                    for item in raw_results:
                        results.append({
                            "title": item.get("title", "No title"),
                            "url": item.get("href", ""),
                            "snippet": item.get("body", "")
                        })

                if results:
                    return {
                        "query": query,
                        "provider": "duckduckgo",
                        "count": len(results),
                        "results": results
                    }
                else:
                    return {
                        "query": query,
                        "provider": "duckduckgo",
                        "count": 0,
                        "results": [],
                        "message": "No search results found for this query."
                    }
            except Exception as e:
                logger.warning(f"DuckDuckGo search error: {e}")
                return {
                    "query": query,
                    "provider": "duckduckgo",
                    "error": f"Search execution failed: {str(e)}",
                    "results": []
                }

        return {
            "notice": "Web search library is not installed or configured.",
            "results": []
        }
