import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.llm.base import LLMResponse, LLMToolCall


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "calculator" in data["tools_registered"]
    assert "version" in data


def test_system_stats_endpoint(client):
    response = client.get("/api/system/stats")
    assert response.status_code == 200
    data = response.json()
    assert "cpu_percent" in data
    assert "ram_percent" in data
    assert "connected_llms" in data


def test_memory_crud_endpoints(client):
    # Create memory
    res = client.post("/api/memory", json={"content": "Prefers dark mode interface", "category": "preference"})
    assert res.status_code == 201
    mem = res.json()
    mem_id = mem["id"]
    assert mem["content"] == "Prefers dark mode interface"

    # List memories
    res_list = client.get("/api/memory")
    assert res_list.status_code == 200
    assert any(m["id"] == mem_id for m in res_list.json())

    # Delete memory
    res_del = client.delete(f"/api/memory/{mem_id}")
    assert res_del.status_code == 200


def test_document_upload_and_list(client):
    file_payload = {"file": ("manual.txt", b"JARVIS system activation protocols.", "text/plain")}
    res = client.post("/api/documents", files=file_payload)
    assert res.status_code == 201
    doc = res.json()
    doc_id = doc["id"]
    assert doc["filename"] == "manual.txt"

    # List
    res_list = client.get("/api/documents")
    assert res_list.status_code == 200
    assert any(d["id"] == doc_id for d in res_list.json())

    # Delete
    res_del = client.delete(f"/api/documents/{doc_id}")
    assert res_del.status_code == 200


@pytest.mark.asyncio
async def test_chat_endpoint_mocked(client):
    mock_llm_response = LLMResponse(
        content="I am JARVIS, at your service, sir.",
        model_used="test-model",
        tool_calls=[]
    )

    with patch("app.llm.openai_adapter.OpenAICompatibleProvider.chat_complete", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_llm_response

        payload = {
            "message": "Status report.",
            "use_memory": True
        }
        res = client.post("/api/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["reply"] == "I am JARVIS, at your service, sir."
        assert data["session_id"] is not None
