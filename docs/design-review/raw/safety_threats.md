# Safety Threats — Pocket Mechanics

Pocket Mechanics helps non-mechanics identify car parts from an uploaded engine-bay photo and provides step-by-step maintenance guidance (and potentially a “buy list” of parts).

## Filled Threat Table

| Threat | Relevant? | Mitigation |
|---|---|---|
| Prompt injection | Yes — users can type free-form questions/instructions alongside an uploaded photo. | User text is passed to the model only as a **user message** (never concatenated into system instructions); we enforce a strict allowlist of tool/intent actions, length-limit user text, and strip/ignore attempts to override safety rules (e.g., “ignore previous instructions”). |
| Hallucination in high-stakes output | Yes — incorrect guidance for repairs/maintenance can cause injury (hot surfaces, high voltage), vehicle damage, or unsafe driving conditions. | We add a **“safety-first” policy** in the system prompt: require uncertainty signaling, ask clarifying questions when the photo/model is ambiguous, refuse “critical safety” instructions without verification, and always show a prominent footer: “Verify with your owner’s manual / a qualified mechanic before performing repairs.” |
| Bias affecting specific user groups | Yes — performance may vary by language and by vehicle make/model/year (and by photo quality tied to different phone cameras). | We test with a diverse set of vehicles (multiple makes/years) and languages, log misidentifications by segment (language + vehicle metadata + image-quality signals), and add UX that explicitly asks for make/model/year when confidence is low to reduce uneven outcomes. |
| Content policy violation | Low — normal use is car photos + maintenance questions, but users can still submit abusive/sexual/violent text or unrelated images. | We pre-screen user text (and image metadata where available) with a moderation check; if rejected, we show a clear refusal + rephrase guidance, and we log only the **policy category + timestamp** (not the full prompt/image) for review. |
| Privacy violation via logs or model memory | Yes — engine-bay photos can include faces, license plates, VIN stickers, addresses on paperwork, or other personal info. | We do not store raw uploaded images by default; we process in memory, send only what’s required to the AI API, and delete request payloads after the response; logs are minimized (no full prompts/images), and the upload UI includes a plain-language disclosure of what is sent to the AI and retained. |
| Data exfiltration | Partial — we may have API keys/server configuration and (later) user sessions; a malicious prompt could try to extract system prompts or secrets. | We never place secrets in prompts; API keys stay server-side only; we redact known secret patterns from any model output before display, and we keep each request context limited to that session’s inputs (no cross-user data in the prompt). |

## Top Risk Statement

Our biggest safety concern is **hallucinated or mis-grounded maintenance instructions**, because a confident but wrong step (e.g., touching a hot component, incorrect jack placement, wrong fluid/part) can cause injury or vehicle damage; we mitigate this by enforcing uncertainty + clarification behavior, refusing safety-critical steps when ambiguous, and displaying a strong “verify with manual/mechanic” disclaimer on every repair guide.

