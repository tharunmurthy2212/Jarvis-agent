import pytest
from app.tools.registry import ToolRegistry, ToolDefinition


@pytest.mark.asyncio
async def test_tool_registry_execution():
    registry = ToolRegistry()

    # Execute registered calculator
    calc_res = await registry.execute("calculator", {"expression": "100 * 5"})
    assert calc_res["status"] == "success"
    assert calc_res["result"]["result"] == 500

    # Execute registered datetime
    dt_res = await registry.execute("get_current_datetime", {})
    assert dt_res["status"] == "success"
    assert "local_time" in dt_res["result"]

    # Execute unknown tool
    unknown_res = await registry.execute("non_existent_tool", {})
    assert unknown_res["status"] == "error"
    assert "Unknown tool" in unknown_res["result"]


@pytest.mark.asyncio
async def test_custom_tool_registration():
    registry = ToolRegistry()

    def greet(name: str) -> str:
        return f"Greetings, {name}!"

    tool = ToolDefinition(
        name="custom_greet",
        description="Greets a user by name",
        parameters={
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"]
        },
        handler=greet
    )

    registry.register(tool)
    assert "custom_greet" in registry.list_tool_names()

    res = await registry.execute("custom_greet", {"name": "Commander"})
    assert res["status"] == "success"
    assert res["result"] == "Greetings, Commander!"
