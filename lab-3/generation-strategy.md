# Generation strategy (Lab 3)

**Project:** Pocket Mechanics

## Primary multimodal path

- **Model:** Gemini 3 Flash (vision) via OpenRouter for engine-bay photo + user question.
- **Temperature:** Low (e.g. 0.2) for stable part labels and instructions.
- **Output shape:** Prefer structured JSON (`identified_part`, `explanation`, `next_steps`, `safety_warning`, `confidence_note`) when the API supports it; otherwise labeled sections in plain text.

## Fallback

- **Secondary model:** GPT-4o mini (or similar) via OpenRouter if primary is unavailable or rate-limited; same message schema.
- **Non-AI fallback:** If both fail, UI shows retry / check connection (see Design Review Section 7).

## Image handling

- Resize/compress before API call; **do not** persist raw uploads in Firestore by default.
