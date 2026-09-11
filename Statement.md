# Problem Statement

Manual video surveillance does not scale. Security personnel monitoring multiple camera
feeds are prone to fatigue and attention lapses, and suspicious behavior — loitering in a
restricted area, sudden fast movement, or unauthorized zone entry — is often missed until
after an incident has occurred. Most existing CCTV setups only provide raw footage with no
automated interpretation, leaving detection and response entirely dependent on a human
watching a screen in real time.

SentinelAI addresses this gap by turning a standard video feed into an intelligent monitoring
system that automatically detects people, tracks their movement, scores their behavior for
risk, and raises human-readable, explainable alerts — reducing reliance on constant manual
attention while keeping a clear audit trail of why each alert was raised.

## Scope of the Project

SentinelAI covers the full pipeline from raw video input to actionable, explained alerts:

- **Input sources:** webcam, local video file, or IP camera (RTSP) feeds
- **Detection & tracking:** person detection via YOLOv8, multi-object tracking across
  frames to compute dwell time and movement speed
- **Zone management:** defining and managing restricted/monitored polygon zones per camera
- **Risk scoring:** a hybrid engine combining a trained Random Forest classifier with
  rule-based heuristics (loitering duration, movement speed, zone breaches) to produce a
  0–100 risk score and a threat level (Low / Warning / Critical)
- **Explainability:** natural-language justification generated for every alert, so a human
  reviewer can immediately understand what triggered it and why
- **Presentation & operations:** a dashboard for live monitoring, an alerts/incidents log,
  basic analytics/reporting, and JWT-based authentication for API and frontend access

Out of scope for this version: facial recognition/identity matching, multi-site deployment
across distributed hardware, and cloud-native scaling — these are noted as future
enhancements rather than current features.

## Target Users

- **Security personnel / control room operators** monitoring live feeds who need
  prioritized, explained alerts rather than raw footage to watch continuously
- **Facility/campus/retail security managers** who need an incident log and analytics for
  after-the-fact review and reporting
- **Small-to-mid scale deployments** (a single site or a handful of cameras) such as
  offices, campuses, warehouses, or retail stores, where dedicated 24/7 human monitoring is
  impractical

## High-Level Features

1. Multi-source video ingestion (webcam / file / RTSP)
2. Real-time person detection and tracking (YOLOv8-based)
3. Configurable restricted-zone management per camera
4. Hybrid ML + heuristic risk scoring engine (0–100 score, threat level classification)
5. Explainable AI alert generation (human-readable reasoning per alert)
6. Live monitoring dashboard with alerts log, incidents log, and analytics/reporting
7. Secure access via JWT authentication
8. Automated testing (pytest) and containerized deployment (Docker/Docker Compose)
