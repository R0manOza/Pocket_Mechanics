# Individual Problem Brainstorm

**CS-AI-2025 | Spring 2026 | Lab 1**

**Your Name:** Roman Gurgenidze  
**GitHub Username:** TODO (add yours)  
**Date:** 2026-03-13

---

## H1: Hassle

*What process in your daily life is tedious, error-prone, or needlessly manual?*

**WHO has this problem?**  
People who have a home camera (doorbell cam / indoor cam) but don’t have time to constantly check it—especially renters or apartment residents who get many notifications.

**PROBLEM in one sentence:**  
They get flooded with noisy alerts and still miss the important moments because cameras record too much and the “event history” is not summarized in a human-friendly way.

**CURRENT SOLUTION:**  
They scroll through motion clips manually, rely on basic motion detection, or just ignore alerts; when something happens (package missing, suspicious person), it’s hard to find the right clip quickly.

**AI ANGLE:**  
Vision-based event detection + video summarization: the AI acts like a security guard—labels events (person at door, package delivered, car pulled up, loitering), writes timestamped logs, and lets the user search: “show all events with a person between 2–4pm.”

**WHY IT MATTERS:**  
Less stress and faster answers: you can quickly verify what happened (and when), reduce false alarms, and have a clear record for disputes (packages, vandalism, unauthorized entry).

---

## H2: Hardship

*What problem do you see in your community or country that affects real people?*

**WHO has this problem?**  
Families and small shop owners who cannot afford a professional security service but want better safety monitoring than “record everything and hope.”

**PROBLEM in one sentence:**  
Security incidents are often discovered late, and when they are discovered the video evidence is hard to navigate, making response and reporting slower.

**CURRENT SOLUTION:**  
Cheap cameras with motion alerts, or manual review after the fact; many people stop checking because alerts are too frequent and unhelpful.

**AI ANGLE:**  
Anomaly detection + structured logging: the AI flags unusual patterns (someone returning multiple times, loitering near the door, movement at odd hours) and creates an incident-style report with the top clips and a short summary.

**WHY IT MATTERS:**  
Better safety outcomes without paid monitoring: faster recognition of suspicious activity, easier reporting, and a stronger sense of control for people who are at work or away from home.

---

## H3: Horizon

*What new capability does multimodal AI unlock that was impossible 2 years ago?*

**WHO has this problem?**  
Users with multiple cameras (front door + hallway + garage) who need a single “what happened last night?” view, including short explanations.

**PROBLEM in one sentence:**  
Multi-camera footage creates too much data, and humans can’t efficiently connect events across cameras or summarize them into a story.

**CURRENT SOLUTION:**  
Manually checking each camera timeline, or only reacting when a push notification is noticed; cross-camera investigation is slow and frustrating.

**AI ANGLE:**  
Multimodal timeline understanding: the AI creates a unified event timeline across cameras (with confidence scores), generates a daily summary, and supports Q&A like “when did the delivery arrive?” or “did anyone enter the garage?”

**WHY IT MATTERS:**  
Turns cameras from “raw video storage” into a usable safety system: less time spent reviewing footage and higher chance of catching real issues early.

---

## Self-Assessment (Complete Before Committing)

**Which of your three problems has the most specific WHO?**  
H1: home camera owners who get many noisy motion alerts and don’t have time to review clips.

**Which has the strongest AI angle (where AI is truly necessary, not just nice to have)?**  
H3: cross-camera event correlation + natural-language search over events is hard without vision-language understanding and summarization.

**Which would you fight hardest for if your team had to choose?**  
H1, because it’s a very clear pain point (too many alerts, too hard to find the right clip) and easy to validate with anyone who owns a doorbell camera.

**Is there a problem you thought of but discarded? What was it, and why did you drop it?**  
“Just store more footage” or “better motion sensitivity settings”; dropped because storage doesn’t solve the core problem (humans still can’t review everything), and the value comes from summarization + searchable logs.

