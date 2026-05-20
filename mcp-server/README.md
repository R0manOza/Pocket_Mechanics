# Pocket Mechanics — MCP server (Lab 6 + Lab 8 production)

[Model Context Protocol](https://modelcontextprotocol.io) server with **Bearer auth**, **Pydantic validation**, **JSON audit logging**, and **sanitised errors**.

| Module | Role |
|--------|------|
| `auth.py` | `MCP_SECRET_KEY` verification |
| `validated_tool.py` | Input schema |
| `audit_logger.py` | JSONL audit (`input_hash`, latency, status) |
| `server.py` | MCP stdio entrypoint |

## Prerequisites

- Python **3.11+**
- Backend running with a valid **`.env`** (e.g. `GEMINI_API_KEY` or `OPENROUTER_KEY`): see `Backend/README.md`
- Default API base: `http://127.0.0.1:8000` (override with `POCKET_MECHANICS_API_URL`)

## Install

```bash
cd mcp-server
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Run (stdio)

**Normally you do not run this alone in a terminal and then type commands into it.** The MCP server reads **JSON-RPC from stdin**. Anything you type (including `npx ...`) is parsed as MCP traffic and will error.

### Recommended: MCP Inspector spawns the server

1. Start your **FastAPI** backend first (`Backend/` — port **8000**).
2. Open a **second** terminal:

```powershell
cd mcp-server
npx @modelcontextprotocol/inspector
```

3. In the Inspector UI:
   - Transport: **stdio**
   - Command: `python` (or full path to `.venv\Scripts\python.exe`)
   - Args: **absolute path** to this file: `...\Pocket_Mechanics\mcp-server\server.py`
4. **Connect**, then invoke **`ask_pocket_mechanics_tip`**.

### Manual stdio (advanced / debugging only)

```bash
python server.py
```

Leave this process **alone** — only an MCP client should pipe JSON-RPC to stdin.

## Cursor (`~/.cursor/mcp.json` example)

```json
{
  "mcpServers": {
    "pocket-mechanics": {
      "command": "C:/path/to/Pocket_Mechanics/mcp-server/.venv/Scripts/python.exe",
      "args": ["C:/path/to/Pocket_Mechanics/mcp-server/server.py"],
      "env": {
        "POCKET_MECHANICS_API_URL": "http://127.0.0.1:8000"
      }
    }
  }
}
```

## Tool: `ask_pocket_mechanics_tip`

- **When to use:** User asks a **car maintenance / parts / fluids** question in natural language (not general trivia).
- **Input:** `question` (required), `vehicle_hint` (optional, e.g. `2014 Ford Focus`).
- **Output:** JSON string with `answer`, `model`, and `source`=`pocket_mechanics_api`.
