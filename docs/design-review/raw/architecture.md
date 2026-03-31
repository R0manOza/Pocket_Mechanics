# Architecture — Pocket Mechanics

See diagram: `design-review/architecture-diagram.svg`

Pocket Mechanics is a web app where users upload an engine-bay photo and ask a maintenance question. The backend validates and preprocesses the request, calls a multimodal model through OpenRouter, and returns a structured, safety-aware answer. Only structured account/profile data and text chat history are stored; uploaded images are processed in memory and not persisted.

## Technology Stack Table

| Layer | Technology | Why |
|---|---|---|
| Frontend | Web UI in the user’s browser  | Fast UI iteration; easy image upload + result rendering. |
| Backend | API server (FastAPI or Node/Express) | Central place to validate inputs, resize/compress images, apply safety fallbacks, and keep secrets server-side. |
| AI model | **Gemini 3 Flash (vision)** via **OpenRouter** | Vision-capable model for engine-bay photos; OpenRouter makes model swapping a config change. |
| Storage | **Firebase Firestore** | Store user profile + session text; keep images out of storage for privacy; team-friendly auth + rules. |
| Hosting | Vercel (frontend) + Railway (backend)  | Common capstone-friendly deployment targets with free tiers. |

## Diagram Notes (What Data Flows Where)

- **Browser → Backend**: HTTPS multipart form containing the photo + question text (and optional structured car metadata like make/model/year).
- **Backend → OpenRouter → Gemini**: preprocessed image (resized/compressed) + user question + car profile in a structured prompt format.
- **Backend → Firestore**: user profile and session records (question/response text). **No image blobs** are written.
- **Backend → Browser**: formatted answer (identified part, explanation, next steps, safety banner) and fallback messages when uncertain.

