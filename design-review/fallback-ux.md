# Fallback UX — Pocket Mechanics

## Scenario A — API Failure (Network Error, Timeout, Model 500)

The user sees the chat input area become temporarily disabled. The last message bubble is replaced by a gentle notice:

> "Sorry, we couldn't get a response right now. Your conversation is saved — tap **Try Again** to resend your question."

A **Try Again** button appears directly below the message. If the retry also fails, the message updates to:

> "We're still having trouble connecting. Please check your internet connection or try again in a few minutes."

The user's original question remains visible in the chat so they do not have to retype it. No error codes, stack traces, or technical language are shown at any point.

---

## Scenario B — Low-Confidence Output

When the model returns a response but its confidence is low (e.g., an uncommon car model, vague symptom description, or a question that spans multiple possible causes), the user sees the response displayed with an amber-highlighted banner above it:

> "This answer may not be fully accurate for your specific vehicle. We recommend verifying with a certified mechanic before proceeding."

For repair guidance specifically:
- **High confidence** (above 0.85): The response is displayed normally.
- **Medium confidence** (0.50–0.85): The response is shown with the amber "Please verify" banner and a suggestion to consult a professional.
- **Low confidence** (below 0.50): Instead of showing a potentially wrong repair guide, the user sees:

> "We're not confident enough to give repair advice on this one. Here's what we suggest: describe the issue to a local mechanic or try rephrasing your question with more details (year, make, model, specific symptoms)."

This is critical for Pocket Mechanics because incorrect repair instructions could lead to physical harm or vehicle damage.

---

## Scenario C — Content Filter Rejection

If a user submits a prompt that is outside the automotive domain or gets flagged by content filters, the user sees:

> "That question is outside what Pocket Mechanics can help with. Try asking about a car problem, maintenance tip, or vehicle specification."

No explanation of why the content was rejected is shown. The input field remains active so the user can immediately ask a new question. Their rejected message is not displayed in the chat history.
