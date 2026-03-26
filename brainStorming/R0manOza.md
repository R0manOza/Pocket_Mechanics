# Individual Problem Brainstorm

**CS-AI-2025 | Spring 2026 | Lab 1**


**Your Name:** Roman Gurgenidze  
**GitHub Username:** R0manOza
**Date:** 2026-03-13

---

## H1: Hassle

*What process in your daily life is tedious, error-prone, or needlessly manual?*

**WHO has this problem?**  
Car owners who are not mechanics (for example: someone who owns a 2014 Ford Focus but does not know engine-bay parts or basic maintenance procedures).

**PROBLEM in one sentence:**  
They can’t confidently identify car parts or follow the right step-by-step instructions (and fear doing something wrong), so they waste time searching or relying on guesswork.

**CURRENT SOLUTION:**  
They look up videos/forums for generic info, compare random images, open a manual, or ask a mechanic/friend for help; sometimes they still can’t tell which exact component they’re seeing in their own engine bay.

**AI ANGLE:**  
Vision-based part recognition + visual question answering over an uploaded engine-bay photo, combined with multimodal “explain and guide” for step-by-step tutorials from manuals (instruction generation).

**WHY IT MATTERS:**  
It reduces time-to-answer, prevents costly mistakes (wrong part/location, wrong steps), and helps people do safer maintenance themselves—without needing prior car knowledge.

Example questions this agent should handle:
- “This is my engine bay—what is this part?”
- “Where is the spark plug?”
- “Where is the battery?”
- “Where do I put the oil in?”
- “How do I drain the oil on a 2015 Ford Focus?”

Example multimodal workflow:
1. User uploads a clear engine-bay image.
2. Agent points out likely components, explains what each part is, and answers follow-up questions.
3. User asks for a specific maintenance task; agent provides a careful tutorial and a checklist.

---

## H2: Hardship

*What problem do you see in your community or country that affects real people?*

**WHO has this problem?**  
Drivers who need parts or maintenance help but don’t have easy access to a mechanic (or can’t afford frequent trips).

**PROBLEM in one sentence:**  
They struggle to get the correct part name/locations and then to find the correct replacement or procedure, which can lead to delays and extra costs.

**CURRENT SOLUTION:**  
They guess parts based on symptoms, then search online with vague keywords, or they buy the wrong item because they can’t confirm what the part is in their specific car.

**AI ANGLE:**  
Multimodal assistance that (1) identifies a part from an image, (2) extracts the likely part name/spec, and (3) helps generate a “buy list” by searching for matching items in online stores.

**WHY IT MATTERS:**  
Faster correct identification means correct purchases, fewer returns, and less downtime—especially important for people relying on their car for work or school.

---

## H3: Horizon

*What new capability does multimodal AI unlock that was impossible 2 years ago?*

**WHO has this problem?**  
Anyone who wants to learn car maintenance through guided help instead of paying for repeated explanations.

**PROBLEM in one sentence:**  
They need personalized, photo-based guidance that turns “I don’t know what I’m looking at” into “I know exactly what to do next.”

**CURRENT SOLUTION:**  
Static manuals and generic videos require the user to already understand car terminology and how parts relate inside the engine bay.

**AI ANGLE:**  
Multimodal “contextual tutoring”: the AI reads the visual context (what the user shows), then maps it to the correct location/instructions and explains it in beginner-friendly language.

**WHY IT MATTERS:**  
It lowers the skill barrier so users can learn maintenance tasks safely and confidently, and it makes tutorials usable even when the user can’t describe the problem technically.

---

## Self-Assessment (Complete Before Committing)

**Which of your three problems has the most specific WHO?**  
H1 (the non-mechanic car owner, e.g., a 2015 Focus owner facing engine-bay identification).

**Which has the strongest AI angle (where AI is truly necessary, not just nice to have)?**  
H1 (image-based part identification + visual Q&A) because without computer vision the user can’t reliably confirm what they’re seeing.

**Which would you fight hardest for if your team had to choose?**  
H1, because it directly supports the core “take a picture and get answers/tutorials” experience.

**Is there a problem you thought of but discarded? What was it, and why did you drop it?**  
We considered a text-only “car troubleshooting chatbot,” but it’s too hard for users who can’t accurately describe parts/symptoms; the visual-first approach is more accessible.