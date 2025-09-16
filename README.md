# Service with AI Model for Automating the Issuing and Return of Tools to Aviation Engineers

*Innopolis University, “Practical Machine Learning and Deep Learning” and "Introduction to CV" courses*

---

## Team

| **Name**        | **Role (work distribution)**  | **Innopolis Email**                                                         |
| --------------- | ----------------------------- | --------------------------------------------------------------------------- |
| Arthur Babkin   | ML Engineer & Project Manager | [a.babkin@innopolis.university](mailto:a.babkin@innopolis.university)       |
| Vladimir Rublev | ML Engineer & Backend         | [v.rublev@innopolis.university](mailto:v.rublev@innopolis.university)       |
| Kirill Shumskii | ML Engineer & R\&D            | [ki.shumskii@innopolis.university](mailto:ki.shumskii@innopolis.university) |

### Near-term sprints

As a team, we will jointly run an expanded research effort and search for more dataset. We consider this mission-critical: the more relevant data we find and curate, the better. In parallel, we will split responsibilities for models training, models comparison/benchmarking, and hyperparameter search among ourselves (with periodic rotations to cross-check results).

### Other important information

We are developing this project in alignment with the “Introduction to CV” course. In parallel, we will also develop it as part of the [LCT Hackathon on i.moscow (the best and the hardest ML related hackathon in Russia)](https://i.moscow/cabinet/lct/hackatons/61745724cf074a308d8652836b49387e/) to accelerate data collection, validate assumptions with mentors, and benchmark progress against other teams, who also will participate there.

---

## Project Topic & Short Description

### Final Goal

Build a computer vision service that automates identification and tracking of hand tools when they are issued to, and returned by, aircraft engineers. The system recognizes tools from camera streams or photos, reconciles the detected set with the tools recorded as issued / requested from the warehouse, and logs the result in the maintenance management system (MMS). If discrepancies exceed a threshold, the system triggers a manual check.

### Why it matters

In aviation, safety is paramount and maintenance is performed daily. Manual tool tracking is accurate but time-consuming (up to 1.5 hours per shift across staff) and prone to human error. Automating this flow reduces labor costs, shortens turnaround, and lowers the risk of FOD (Foreign Object Debris) and associated incidents.

### Target users

Line maintenance engineers, tool crib/warehouse operators, and QA managers within airlines/MROs.

---

## Repository

**Repo:** [https://github.com/I-y6o-I/aircraft-engeneering-tools-detecton](https://github.com/I-y6o-I/aircraft-engeneering-tools-detecton)

---

## Related Work: Competitors and SOTA

We consider two main families for object detection; for anomaly detection we will benchmark classical industrial AD datasets to model “missing/extra tool” events.

* **YOLO family** — Fast, widely used object detectors pretrained on large datasets (e.g., COCO).
  *Pros:* mature tooling and tutorials; real-time inference on edge; good transfer learning.
  *Cons:* requires fine-tuning for domain-specific tool classes; limited global context.
  *Refs:* `redmon2018yolov3`, `bochkovskiy2020yolov4`

* **DINO (transformer-based)** — State-of-the-art (SOTA) DETR-style detector with stronger context modeling.
  *Pros:* excellent accuracy on COCO; robust with crowded scenes/occlusions.
  *Cons:* heavier training; typically needs more compute/data.
  *Ref:* `zhang2022dino`

---

## Data Sets (initial plan)

* **Open Images V7 (tools subset).** Public images with labels for many hand tools. We’ll experiment with it and augment it as needed.
  *Ref:* `kuznetsova2020openimages`
* **Hackathon-provided data (if available).** We plan to obtain and use any datasets shared by the hackathon organizers/partners.
* **Manual annotation option.** If necessary, we will collect in-house photos and perform manual labeling to cover domain-specific tool types and layouts that are missing from public datasets.

---

## System Scope & Final Product

A prototype AI service with:

1. Image/video ingestion (1 FPS baseline).
2. Tool detection (YOLO/DINO or another model specially fine-tuned on our task).
3. Set reconciliation against MMS (issued/requested) with tolerance logic.
4. Logging of results & alerts; trigger manual verification if discrepancy exceeds threshold.
5. Simple web UI or embeddable widget for the tool-crib station.

---

## Success Criteria & Metrics

We prioritize **missing-tool risk** (low FN) and usable latency:

* **Recall per frame** ≥ 0.98
* **mAP\@50:95** ≥ 0.45
* **Event precision** (per issue/return event) ≥ 0.90
* **Inference time** < 1 s at 1 FPS on target hardware

---

## References

This README mirrors our LaTeX write-up; see `refs.bib` in the repo for full citations:

* `redmon2018yolov3`
* `bochkovskiy2020yolov4`
* `zhang2022dino`
* `kuznetsova2020openimages`
