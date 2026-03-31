# Capstone Design Review

**Course:** CS-AI-2025 — Building AI-Powered Applications \| Spring 2026  
**Assessment:** Design Review — 10 points  
**Due:** Thursday 2 April 2026 at 23:59 Georgia Time  
**Submission:** Team repo (see required tree in Lab 3 README) + Google Form (link on Teams)

**Team:** Pocket Mechanics  
**Project:** Pocket Mechanics  
**Repo:** https://github.com/R0manOza/Pocket_Mechanics  

---

## Section 1 — Problem Statement and Users


**Problem statement (one sentence):**  
Non-mechanic car owners struggle to **name parts and follow correct maintenance steps from their own engine-bay photos** because **generic videos and forums do not map to their exact vehicle and view**, which means **they waste time, buy the wrong parts, or risk unsafe mistakes**.

**Who exactly has this problem:**  
A car owner who does their own light maintenance (or wants to learn) but opens the hood and cannot confidently match what they see to the right procedure or part name—especially under time pressure (e.g., before a trip) or when English-language resources do not match their car.

**What they do today without your solution:**  
They search forums and videos with vague keywords, compare random stock photos to their engine bay, skim owner’s manuals, or message a friend/mechanic—often still unsure they identified the right component or step sequence for *their* car.

**Why AI is the right tool:**  
Conventional search needs good text queries; many users cannot describe parts accurately. Multimodal AI can **ground answers in the user’s actual photo** (vision + language): identify likely visible components, explain them in plain language, and suggest next steps while flagging uncertainty—something keyword search and static manuals do not do in one flow.

---

## Section 2 — Proposed Solution and Features


**Solution summary (3–5 sentences):**  
Pocket Mechanics is a web app where the user **uploads an engine-bay photo** and asks a question (e.g., “What is this part?” or “Where do I add oil?”). A **backend** validates and preprocesses the image, builds a structured multimodal prompt with optional **saved car profile** (make/model/year), and calls a **vision-capable model** (Gemini 3 Flash via OpenRouter). The app returns a **clear explanation, likely part identification, and safety-aware guidance**, with **fallback UX** when the model is uncertain or the API fails. **Firestore** stores profile and chat text—not raw images—by default.

**Core features:**

| Feature | AI-powered? | The AI differentiator |
|--------|-------------|------------------------|
| Part identification from an uploaded engine-bay photo | Yes | Maps **pixels in the user’s photo** to likely components and plain-language explanations—not generic text-only search. |
| Maintenance Q&A grounded in the photo + car profile | Yes | Combines **vision + structured vehicle context** for answers tailored to what the user is actually looking at. |
| Step-by-step guidance with safety disclaimers | Yes (generation + policy) | Produces **guided steps** while forcing **uncertainty and “verify with manual/mechanic”** behavior when risk is high. |
| Optional “buy list” / part lookup (if implemented) | Partial / planned | Uses identified part names/spec hints to **narrow search**—still verified by the user before purchase. |

**The one feature that would not exist without AI:**  
**Identifying and explaining car parts from the user’s own engine-bay photo in context**—without multimodal understanding, the product collapses to generic chat that cannot reliably see what the user sees.

---

## Section 3 — Measurable Success Criteria



| Criterion | How you will measure it | Target |
|-----------|-------------------------|--------|
| **Part identification quality (top-1)** | Manually verified test set of **25** engine-bay photos across **≥ 5** makes/models/years; compare model top label to ground truth. | **≥ 80%** (≥ **20/25** correct) |
| **Safety fallback (uncertainty → clarify/refuse)** | Replay **15** low-confidence scenarios (blur, occlusion, missing vehicle info); record whether the app **avoids** direct repair steps and **asks to clarify** or **refuses with safety messaging**. | **100%** (**15/15**) |
| **End-to-end latency** | Time from **Analyze** click to **results on screen**; **30** runs on a typical home connection; take **90th percentile**. | **p90 ≤ 6 seconds** |

---

## Section 4 — Architecture

**See:** [`architecture-diagram.svg`](./architecture-diagram.png)

The diagram shows: **User’s browser (frontend)**, **API backend**, **OpenRouter**, **Gemini 3 Flash (vision)**, **Firebase (Firestore) storage**, and **directed arrows** for requests and responses. Images are **not** persisted in our storage layer (processed in memory / sent to the AI provider only).

**Technology stack:**

| Layer | Technology | Why |
|-------|------------|-----|
| Frontend | Web UI in the browser (e.g. React + Tailwind) | Fast iteration; natural fit for upload + results UI. |
| Backend | API server (FastAPI or Node/Express), hosted (e.g. Railway) | Validates inputs, holds API keys, applies safety rules, talks to OpenRouter and Firestore. |
| Primary AI model | **Gemini 3 Flash (vision)** via **OpenRouter** | Multimodal; model swap is mostly a config change on OpenRouter. |
| Secondary model (fallback) | **GPT-4o mini** (or similar) via **OpenRouter** | Cheaper/faster fallback if primary is down or rate-limited; same router integration. |
| Storage | **Firebase Firestore** (+ **Firebase Auth** for accounts) | Structured user/car profile + chat text; **security rules** per user; no image blobs stored by design. |
| Hosting | **Vercel** (frontend) + **Railway** (backend), or equivalent | Common free/low-cost capstone deployment pattern. |

**Multimodal capabilities (check all that apply now or planned by Week 8):**

- [x] Text generation  
- [x] Vision / image understanding 
- [?] Image generation (maybe)
- [x] Audio TTS or STT  
- [ ] Document / PDF understanding  
- [ ] Function calling  
- [ ] RAG  

---

## Section 5 — Prompt and Data Flow

**User action:**  
The user uploads an engine-bay photo, types a question (e.g. “What part is this and where do I put oil?”), and clicks **Analyze**.

**Preprocessing:**  
Validate file type/size; reject oversize or non-images with a friendly message. Resize (e.g. max dimension **1280px**), compress to JPEG if needed, trim/limit question length. Load **saved car profile** (make/model/year) from Firestore if present.

**Prompt construction:**  
- **System message:** beginner-friendly car assistant; analyze the **uploaded image**; use **car profile** when available; **do not** claim certainty when the view is ambiguous; separate **identified parts**, **uncertainty**, and **safe next steps**; safety-first tone.  
- **User message:** image + user question + optional car profile + optional short issue summary—**not** concatenated into the system string (structured multimodal messages).

**API call:**  
**Gemini 3 Flash (vision)** via **OpenRouter** (`https://openrouter.ai/api/v1`), e.g. `temperature=0.2`, `max_tokens=800`, timeout/retry policy on failures.

**Response parsing:**  
Prefer **structured JSON** (e.g. `identified_part`, `confidence_note`, `explanation`, `next_steps`, `safety_warning`). If parsing fails, treat as error and use fallback UX (no raw stack traces to the user).

**Confidence / validation:**  
Use model signals if available; otherwise rules: non-empty response, presence of required fields, explicit “unclear image” / uncertainty language → trigger **clarify/refuse** path instead of definitive repair steps.

**User output:**  
Success: result card with likely part, explanation, next steps, safety note; thumbnail of analyzed photo.  
Fallback: clearer photo prompt + **Try Again**; low confidence → amber banner or blocked repair steps per [`fallback-ux.md`](./fallback-ux.md). API failure → soft “couldn’t connect” + retry.

---

## Section 6 — Team Roles and Contract


**Team members and roles:**

| Name | Primary role |
|------|----------------|
| Tirnike | Backend, databases, DevOps |
| Levan | Frontend, UX, testing |
| Roman | AI integration, documentation, deployment / DevOps |

**Team Contract:** committed at repo root as **`TEAM-CONTRACT.md`**.

**Link:** https://github.com/R0manOza/Pocket_Mechanics/blob/main/TEAM-CONTRACT.md

---

## Section 7 — Safety Threats and Fallback UX


### Safety Threats


| Threat | Relevant? | Your mitigation |
|--------|-----------|-------------------|
| Prompt injection — user input hijacks system behaviour | Yes | User text only in **user** messages; fixed **system** instructions; length limits; reject “ignore previous instructions” patterns. |
| Hallucination in high-stakes output | Yes | Safety-first system prompt; clarify/refuse on ambiguity; **never** present output as authoritative; footer: verify with **manual / qualified mechanic**. |
| Bias affecting specific user groups | Yes | Test diverse vehicles and languages; log mismatches by segment; ask for make/model/year when confidence is low; document known limitations in UI if needed. |
| Content policy violation (image generation, user-generated prompts) | Low / Yes (text + images to model) | Moderation pre-check on text; friendly refusal + rephrase; log **category + timestamp** only—not full prompts—for review. |
| Privacy violation via stored model inputs or logs | Yes | **No image persistence** in Firestore by design; minimal logs; disclosure on upload; align with provider retention policies. |
| Data exfiltration via model response | Partial | No secrets in prompts; server-side keys; redact sensitive patterns in outputs; no other users’ data in context. |

**Top risk you are most concerned about:**  
**Wrong or overconfident repair guidance**—because it can cause **injury or vehicle damage**; we prioritize uncertainty handling, refusal/clarify paths, and clear “verify with manual/mechanic” messaging.

### Fallback UX


**The user sees** gentle, plain-language messages: on connection failure, a short notice that the answer could not be loaded, with **Try Again** and their question preserved; on low confidence, an **amber banner** that the answer may not match their vehicle and they should check with a mechanic before acting, or a message that we are **not confident enough for repair steps** and they should add details or seek a professional; on policy rejection, a single line that the question is outside scope, with the input still ready for a new question—**never** raw errors or the word “AI” as blame. *(Full scenarios: [`fallback-ux.md`](./fallback-ux.md).)*

---

## Section 8 — Data Governance


| Question | Your answer |
|----------|-------------|
| **What user data does your app collect or process?** | Typed questions; **uploaded engine-bay images** (in memory for the request); optional **account** data via Firebase Auth (e.g. email if used); **car profile** (make, model, year, engine if provided); **chat / issue history** text in Firestore for continuity. **No voice** in the current design. |
| **Where is it stored? (service name, country)** | **Firebase** (Firestore + Auth) in a **GCP region chosen for the project**—target **EU** (e.g. `europe-west`) for GDPR alignment; exact region is set when the Firebase project is created (provisional until then). |
| **How long is it retained?** | Profile and chat text: **until the user deletes the account** or requests deletion, unless a shorter retention policy is adopted later (e.g. inactive-account cleanup). **Images:** not stored in Firestore; only processed for the API call unless we explicitly add optional “save photo” later (off by default). |
| **Who has access to it?** | **The authenticated user** via the app; **the development team** via Firebase console for support/debugging; course staff may view the repo for grading—**not** end-user production data unless shared for support. |
| **How can a user request deletion?** | **Delete account / delete my data** in the app when implemented; otherwise **email the team** at the project support address listed in the app/README. |
| **Does your app send user data to third-party AI APIs? Which ones?** | **Yes** — user question and **image** are sent to the **model provider** (e.g. **Google Gemini** accessed via **OpenRouter**). Metadata (e.g. car profile) may be included in the prompt. Users are told this on upload / in privacy copy. |

---

## Section 9 — IRB-Light Checklist

**Check all that apply:**

- [x] My app collects or processes **images** that may incidentally include **real people** (e.g. reflection/background in an engine-bay photo)  
- [ ] My app collects or processes audio recordings  
- [ ] My app handles personal health information  
- [ ] My app handles financial information  
- [ ] My app involves users under 18  
- [ ] My app processes documents containing personal data  


**Images (may include incidental likenesses / plates / VIN areas):** On first upload, the user sees a short disclosure that the **photo is sent to an AI service** for analysis, is **not stored** in our database by default, and may contain sensitive details—**avoid** photographing people or documents when possible. Retention: **no image storage** in Firestore in the baseline design; provider-side retention follows **Google / OpenRouter** terms (disclosed in-app).

---

## Section 10 — Submission Checklist

Complete before **Thursday 2 April 2026 23:59** (Georgia time).

- [x] All sections above have no `[fill in]` placeholders left (confirm Firebase region once the project is created).  
- [x] Architecture diagram committed and readable: [`architecture-diagram.svg`](./architecture-diagram.svg); if the course requires **`docs/design-review/architecture-diagram.png`**, export from SVG and add that path.  
- [x] `TEAM-CONTRACT.md` in repo root with all member names in Signatures.  
- [x] `.env` is **not** committed (verify [`.gitignore`](../.gitignore)).  
- [ ] Lab 1 work visible or linked in repo.  
- [ ] Lab 2 proposal and vision call visible in repo.  
- [ ] `lab-3/generation-strategy.md` committed (per Lab 3 README).  
- [ ] Team repo matches the tree in the Lab 3 README.  
- [ ] Google Form completed by one team member.  

---

## Source fragments (optional)

These files were merged into this document; you may keep them for editing sections in isolation:

- [`architecture.md`](./raw/architecture.md)  
- [`success_criteria.md`](./raw/success_criteria.md)  
- [`dataFlow.md`](./raw/dataFlow.md)  
- [`safety_threats.md`](./raw/safety_threats.md)  
- [`fallback-ux.md`](./raw/fallback-ux.md)  
- [`dataGovernance.md`](./raw/dataGovernance.md)  
