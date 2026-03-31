# Measurable Success Criteria — Pocket Mechanics

Pocket Mechanics helps users upload an engine-bay photo, identify parts, and receive step-by-step maintenance guidance with safe fallback behaviour when the model is uncertain.

## Criteria Table

| What you measure | Target number | How you measure it |
|---|---:|---|
| **Criterion 1 — Part identification quality (top-1 accuracy)** | **≥ 80%** | On a **manually verified test set of 25 engine-bay photos** spanning **at least 5 different car makes/models/years** and mixed lighting conditions, the model’s **top predicted part label** matches the ground-truth part in **≥ 20/25** cases. |
| **Criterion 2 — Safety fallback reliability (uncertainty → clarify/refuse)** | **100%** | For **15 replayed “low-confidence” scenarios** (blurry photo, occluded component, look-alike parts, missing make/model/year), the app **does not output a direct step-by-step repair instruction**; instead it **asks a clarifying question** (e.g., requests make/model/year or a different angle) or **refuses with a safety message** in **15/15** cases. |
| **Criterion 3 — Latency (end-to-end photo analysis)** | **p90 ≤ 6 seconds** | In a test environment on a standard home internet connection, measure from **“Analyze” button click** to **results rendered**; across **30 runs**, the **90th percentile** completion time is **≤ 6s**. |

