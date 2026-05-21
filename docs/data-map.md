# Data map — Pocket Mechanics

**Team:** Pocket Mechanics · **Course:** CS-AI-2025 · **Last updated:** 2026-05-21

This document satisfies the Safety Audit **Area 6 — Data governance** requirement. It mirrors the Design Review (Section 8) and describes what we store today vs. planned.

---

## 1. Data inventory

| Data type | Where stored | Retention | Who can access | User deletion |
|-----------|--------------|-----------|----------------|---------------|
| Chat messages (text) | In-memory session map on backend (`session_service`); planned Firestore per `user_id` | Session: until server restart or TTL; Firestore (planned): until account delete | Same `session_id` / authenticated user only | Clear session in UI; future: delete account |
| Engine-bay images | **Not** persisted in our DB; sent in request body to model API only | Request lifetime only (in memory) | User + model provider (OpenRouter / Google) | N/A — not stored by us |
| Car profile (make/model/year) | Planned Firestore `users/{uid}/profile` | Until user deletes account | Authenticated user | Delete account / profile in app (planned) |
| Firebase Auth (email, uid) | Firebase Auth (GCP) | Until account deleted | User; team via Firebase console for support | Firebase delete user |
| Episode / cost logs | `Backend/logs/episode-log.csv`, `cost-log.csv` (or `EPISODE_LOG_PATH` on Render) | Dev: repo-local file; prod: ephemeral disk or rotated file — **no user PII by policy** | Engineering team | Rotate/truncate files; not user-facing |
| MCP audit log | `logs/mcp-audit.jsonl` | Same as episode logs | Engineering team | Rotate/truncate |
| API keys | `Backend/.env` / Render env vars | N/A (secrets) | Deploy admins only | Revoke/rotate in provider consoles |

**Third-party AI processors:** OpenRouter and/or Google Gemini receive user prompts and optional images per request. Disclosed in Design Review and in-app copy.

**Regions (target):** Firebase/GCP **EU** (`europe-west`) when the production Firebase project is created.

---

## 2. Data flow (summary)

1. User types or uploads in **Vercel** frontend.
2. Frontend calls **Render** FastAPI with `session_id` (client UUID).
3. Backend loads/saves messages keyed by `session_id` only (no cross-session reads).
4. LLM provider returns text; backend logs tokens/cost to CSV (hashed MCP inputs in JSONL).
5. Images are not written to Firestore in the baseline design.

---

## 3. PII and logging policy

- Episode logs record: `session_id`, token counts, model id, latency, error **types** — not user names, emails, phone numbers, or full VINs.
- MCP audit log stores **`input_hash`** only (SHA-256 of redacted args); `_auth_token` is never logged.
- Prompts instruct the model not to repeat full VINs unnecessarily.

---

## 4. Cross-user isolation

- **Mechanism:** `session_service` dict keyed by `session_id`; no API to list another user’s session.
- **Test:** `tests/test_session_service.py::TestSessionService::test_session_isolation`
- **Evidence:** [`docs/evidence/isolation-test-output.txt`](evidence/isolation-test-output.txt)

---

## 5. API key security

- `.env` files are gitignored; never commit secrets.
- Verify: `git log --all -- .env Backend/.env` → no commits (see [`docs/evidence/git-env-check.txt`](evidence/git-env-check.txt)).

---

## 6. Related documents

- Design Review Section 8: [`docs/design-review/DESIGN-REVIEW.md`](design-review/DESIGN-REVIEW.md)
- Safety audit: [`docs/safety-audit.md`](safety-audit.md)
