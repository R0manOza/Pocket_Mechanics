# Safety Threats — Pocket Mechanics

## 1. Prompt Injection

**Relevant:** Yes

User messages are passed as the `user` role in a structured message format, never concatenated into the system prompt string. The system prompt is a separate, immutable block that the API receives independently from user content. Input is sanitized to strip known injection patterns (e.g., "ignore previous instructions") before being sent to the model.

---

## 2. Hallucination in High-Stakes Output

**Relevant:** Yes

Car repair advice can affect physical safety (e.g., brake work, electrical systems, jacking up a vehicle). All repair-related responses include a standing disclaimer: "Always verify with a certified mechanic before performing safety-critical repairs." Responses with low confidence scores are flagged with an amber warning or withheld entirely (see Fallback UX — Scenario B). The model is instructed via the system prompt to say "I'm not sure" rather than guess on safety-critical questions.

---

## 3. Bias Affecting Specific User Groups

**Relevant:** Yes

Users describe car problems in many languages and dialects. We test the model with diverse input phrasing (e.g., colloquial vs. technical descriptions, non-native English phrasing) to ensure response quality does not degrade. If we detect systematically lower quality for certain input styles, we log those cases for review and adjust prompts accordingly.

---

## 4. Content Policy Violation

**Relevant:** N/A — Pocket Mechanics does not include image generation or open-ended creative text generation. The model is scoped to automotive Q&A, which has a low risk of generating policy-violating content. Off-topic prompts are redirected (see Fallback UX — Scenario C).

---

## 5. Privacy Violation via Logs or Model Memory

**Relevant:** Yes

Users may mention personal details (location, license plate, VIN) when describing their car. We minimize logging by storing only the question topic and response metadata, not full user messages. Our API provider's data retention policy is reviewed and disclosed in the app's privacy notice. Full conversation text is not retained beyond the active session unless the user explicitly saves it.

---

## 6. Data Exfiltration

**Relevant:** Yes

The system prompt contains no secrets, API keys, or other users' data. We validate that model responses do not echo back system prompt text before displaying them. Each user session is isolated — the model has no access to other users' conversations or data.
