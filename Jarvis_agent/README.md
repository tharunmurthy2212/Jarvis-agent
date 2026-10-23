# JARVIS — Modular Personal AI Assistant

> **"I am JARVIS, your personal AI assistant. I help you learn, automate tasks, write code, and solve problems."**

JARVIS is a high-performance, modular personal AI assistant backend engineered for Windows 11. It provides grounded conversational reasoning, persistent SQLite memory, safe mathematical evaluations, live system timekeeping, document extraction & RAG retrieval, voice synthesis integration, and OpenAI-compatible multi-provider routing.

---

## 1. System Architecture

```
                                  +---------------------------------------+
                                  |     Custom Client UI / REST API       |
                                  +-------------------+-------------------+
                                                      |
                                                      v
+-----------------------------------------------------+-------------------------------------------------------+
|                                              FASTAPI BACKEND                                                |
|                                                                                                             |
|  +--------------------+  +--------------------+  +----------------------+  +-----------------------------+  |
|  |   /api/chat        |  |  /api/sessions     |  |   /api/memory        |  |   /api/documents            |  |
|  |  (Assistant Loop)  |  |  (History Logs)    |  |  (Cross-Session Fact)|  |  (PDF/DOCX/CSV/TXT Ingest)  |  |
|  +---------+----------+  +---------+----------+  +----------+-----------+  +--------------+--------------+  |
|            |                       |                        |                             |                 |
|            v                       v                        v                             v                 |
|  +---------+-----------------------+------------------------+-----------------------------+--------------+  |
|  |                                  ASSISTANT CONVERSATION ENGINE                                        |  |
|  |   - Multi-Turn Loop      - Grounded Context Assembly      - Rate Limit & Timeout Protection           |  |
|  +---------------------------------+---------------------------------------------------------------------+  |
|                                    |                                                                        |
|                  +-----------------+-----------------+                                                      |
|                  |                                   |                                                      |
|                  v                                   v                                                      |
|       +---------------------+             +--------------------+                                            |
|       |   APPROVED TOOLS    |             |    LLM ADAPTER     |                                            |
|       | - Safe Calculator   |             | - Groq             |                                            |
|       | - Live Clock / Date |             | - OpenAI           |                                            |
|       | - Web Search (DDG)  |             | - Ollama (Local)   |                                            |
|       | - Document RAG      |             | - OpenRouter       |                                            |
|       +---------------------+             +--------------------+                                            |
|                                                                                                             |
+-----------------------------------------------------+-------------------------------------------------------+
                                                      |
                                                      v
                                        +-----------------------------+
                                        |    PERSISTENT SQLITE STORE  |
                                        |  (data/jarvis.db + Chunks)  |
                                        +-----------------------------+
```

---

## 2. Prerequisites

- **Operating System:** Windows 11 / Windows 10
- **Language:** Python 3.11 or newer (Python 3.14 compatible)
- **Shell:** Windows PowerShell

---

## 3. Quick Start (Windows 11 PowerShell)

### Step 1: Clone or Navigate to Directory
```powershell
cd c:\Users\tharu\OneDrive\Desktop\Vibe_Coding\Jarvis_agent
```

### Step 2: Set up Virtual Environment & Install Dependencies
Using `uv` (recommended) or standard `python`:

```powershell
# Using uv:
uv venv .venv
uv pip install -r requirements.txt

# Or using standard python:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy the `.env.example` template into `.env`:
```powershell
Copy-Item .env.example .env
```

Open `.env` and insert your credentials:
```env
# LLM Provider (Groq / OpenAI / Ollama)
LLM_PROVIDER=groq
LLM_API_KEY=enter your api key # enter your api key
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-120b
LLM_TEMPERATURE=0.5
LLM_MAX_TOKENS=4096

# Fish Audio TTS (JARVIS Voice Synthesis)
FISH_AUDIO_API_KEY=enter your api key # enter your api key
FISH_AUDIO_MODEL_ID=05b36da8574341d0803391491850db20

# Server Settings
APP_HOST=127.0.0.1
APP_PORT=8000
DATABASE_PATH=data/jarvis.db
ENABLE_MEMORY=true
```

### Step 4: Start the JARVIS Backend
Run using the convenience PowerShell launcher:
```powershell
.\run.ps1
```
Or start directly with Uvicorn:
```powershell
uv run python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 4. API Documentation & Examples

Interactive Swagger documentation is available at:
`http://127.0.0.1:8000/docs`

### A. Health & Operational Telemetry
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get | ConvertTo-Json
```

### B. Chat with Multi-Tool Reasoning & Memory
```powershell
$body = @{
    message = "Calculate sqrt(144) * 12 and tell me today's day and date."
    session_id = $null
    use_memory = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/chat" -Method Post -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 5
```

### C. Document Upload & Grounded Q&A
```powershell
# 1. Upload PDF, DOCX, TXT, or CSV
$uploadRes = curl.exe -s -F "file=@specifications.pdf" "http://127.0.0.1:8000/api/documents" | ConvertFrom-Json
$docId = $uploadRes.id

# 2. Ask questions grounded in the uploaded document
$chatBody = @{
    message = "What are the security constraints mentioned on page 2?"
    document_ids = @($docId)
    use_memory = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/chat" -Method Post -ContentType "application/json" -Body $chatBody | ConvertTo-Json -Depth 5
```

### D. Managing Long-term Memory
```powershell
# Add long-term user preference
$mem = @{ content = "User is Senior Architect on Project Aegis"; category = "preference" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/memory" -Method Post -ContentType "application/json" -Body $mem

# List all stored memories
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/memory" -Method Get | ConvertTo-Json

# Clear memories
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/memory" -Method Delete
```

---

## 5. Running Automated Tests

Run the full pytest suite (22 unit & integration tests) without incurring API charges:

```powershell
uv run python -m pytest -v
```

---

## 6. Security & Sandboxing Architecture

1. **No Code Execution (`eval`/`exec`):** The calculator uses a pure Python Abstract Syntax Tree (AST) evaluator whitelist. Malicious expressions, imports, and system calls are strictly rejected.
2. **Untrusted Data Isolation:** Document uploads and web search snippets are treated as untrusted reference context and cannot override system persona rules.
3. **Secret Protection:** API keys and credentials are automatically redacted from logs and never returned in API payloads.
4. **Local Isolation:** SQLite uses parameterized queries (`?`) to prevent SQL injection, and document paths are sanitized against directory traversal attacks.

---

## 7. Future Extension & Custom Tools

Adding new approved tools to JARVIS is straightforward. In `app/tools/registry.py`:

```python
from app.tools.registry import tool_registry, ToolDefinition

def check_disk_space() -> dict:
    return {"status": "nominal", "free_gb": 450}

tool_registry.register(
    ToolDefinition(
        name="check_disk_space",
        description="Checks available disk space on the local workstation.",
        parameters={"type": "object", "properties": {}},
        handler=check_disk_space
    )
)
```
