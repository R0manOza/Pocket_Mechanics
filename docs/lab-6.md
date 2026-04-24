# Lab 6 — Pocket Mechanics (implementation notes)

**Course context:** Lab 6 — *Streaming, Memory, and MCP* (see repo `Lab-6/README.md` and `Lab-6/GRADING-RUBRIC.md`).

This document describes **what we implemented in the team repo** for Lab 6 and how to run and verify it.

---

## 1) Streaming endpoint (SSE)

### Route

- **`POST /api/ai/stream`**
- **Content-Type:** `text/event-stream`
- **Body (JSON):**

| Field | Type | Required | Notes |
|------|------|----------|--------|
| `message` | string | yes | User’s new message |
| `session_id` | string | yes | Stable id per conversation (e.g. `crypto.randomUUID()` in the browser) |
| `system` | string | no | Overrides default Pocket Mechanics system prompt |
| `model` | string | no | Overrides model (OpenRouter slug or Gemini short name) |

### Event format

- Each token: `data: {"token":"..."}\n\n`
- Summary (includes timing fields required by the lab rubric):  
  `data: {"usage":{"input_tokens":...,"output_tokens":...,"stream_start_ms":...,"stream_end_ms":...,"latency_ms":...}}\n\n`
- End: `data: [DONE]\n\n`

### Backend routing (same keys as Lab 5)

- **`OPENROUTER_KEY` set** (and both keys set) → streaming uses **OpenRouter** with `stream=True` (native token deltas + usage when available).
- **`GEMINI_API_KEY` only** → streaming uses **Google AI Studio** (`google-generativeai`) with `stream=True` / chat history.

### Quick test (curl)

Start the API from **`Backend/`** (see `Backend/README.md`), then:

**PowerShell — avoid inline JSON on the command line.** Continuation lines, smart quotes from copy/paste, or `-d "$body"` (variable inside double quotes) often break JSON and produce `json_invalid`.

**Recommended:** run the helper script from `Backend/` (starts `curl` with `--data-binary @file`):

```powershell
cd Backend
.\scripts\test-stream.ps1
```

**Or** write ASCII JSON to a file yourself, then:

```powershell
Set-Content -Path .\body.json -Value '{"message":"Hi","session_id":"s1"}' -Encoding Ascii -NoNewline
curl.exe -N -X POST http://127.0.0.1:8000/api/ai/stream -H "Content-Type: application/json" --data-binary "@body.json"
```

**Why one-liners fail:** `--data-raw '{...}'` can still fail if the `{`/`"` characters are **Unicode “smart quotes”** from a document, or if PowerShell parses the line differently than you expect.

**cmd.exe** (works with escaped inner quotes):

```bat
curl.exe -N -X POST http://127.0.0.1:8000/api/ai/stream -H "Content-Type: application/json" -d "{\"message\":\"Hi\",\"session_id\":\"s1\"}"
```

`-N` disables curl buffering so you see chunks sooner in the terminal.

### Interactive docs

Open **`http://127.0.0.1:8000/docs`** → **`POST /api/ai/stream`** (FastAPI Swagger).

---

## 2) Session memory

### Implementation

- File: `Backend/services/session_service.py`
- **In-memory** map: `session_id → list[{role, content}, ...]`
- **Sliding window:** keeps all `system` messages + last **20 turns × 2** non-system messages (same idea as `Lab-6/examples/fastapi-scaffold/services/session_service.py`).

### Behaviour

Every streaming request:

1. Loads history for `session_id`
2. Ensures a `system` message exists (default Pocket Mechanics assistant)
3. Appends the new **user** `message`
4. Streams the model reply
5. Appends the **assistant** full text to history
6. Saves trimmed history

### Instructor-style check

Use the **same `session_id`** across multiple `POST /api/ai/stream` calls and ask follow-ups that reference earlier turns (see rubric script in `Lab-6/GRADING-RUBRIC.md`).

---

## 3) Episode log (streaming audit trail)

### File

- Default path: **`Backend/logs/episode-log.csv`**
- Override: env **`EPISODE_LOG_PATH`**

### What gets logged

- On each stream: `user_message` then `stream_end` with **`stream_start_ms`**, **`stream_end_ms`**, token counts, model id, computed **`cost_usd`** (same pricing table pattern as the Lab 6 episode logger example).

This complements the Lab 5 **`logs/cost-log.csv`** (blocking `/api/ai/generate` calls).

---

## 4) MCP server (team repo)

### Location

`mcp-server/` (required folder name per Lab 6 rubric).

### Tool

- **`ask_pocket_mechanics_tip`**
- **Read-only:** HTTP `POST` to your running backend **`/api/ai/generate`** (real model output).
- **Args:** `question` (required), `vehicle_hint` (optional).

### Configure

- **`POCKET_MECHANICS_API_URL`** (optional, default `http://127.0.0.1:8000`)

### Run

See `mcp-server/README.md`:

```bash
cd mcp-server
pip install -r requirements.txt
python server.py
```

### Test

**Use two terminals.** `python server.py` speaks **JSON-RPC on stdin** — if you type `npx ...` into that same window, the server treats your keystrokes as invalid MCP messages (exactly the error you saw).

1. **Terminal A:** start the FastAPI backend (`uvicorn` in `Backend/`).
2. **Terminal B:** run MCP Inspector (it will **spawn** your server as a child process — you usually do **not** leave `python server.py` running manually first):

```powershell
cd mcp-server
npx @modelcontextprotocol/inspector
```

In the Inspector UI: transport **stdio**, command **`python`**, args: **full path** to `mcp-server\server.py`, then **Connect** and call **`ask_pocket_mechanics_tip`**.

(Advanced: if you manually run `python server.py`, do not type into that window — only the MCP client may write to stdin.)

---

## 5) Git checkpoint (Lab 6)

When the team is ready:

```bash
git add .
git commit -m "lab6: streaming + session memory + mcp server"
git tag lab6-mcp-checkpoint
git push origin main --tags
```

---

