# Content Lifecycle V5 Binding

## Overview
This document logs the binding of the Python Content Lifecycle Spine / Operator Review Read Model into the V5 cockpit static read-model layer.

## Metadata
* **Task Label**: `TASK_CONTENTOPS_0175BF_OPERATOR_REVIEW_READ_MODEL_TO_V5_QUEUE_BINDING_V0`
* **Source Packet Hash**: `33a1e02cf92174ecb0772fea66b6d26bbfc07292f3b9900fee4f40f89d17d279`
* **Local-Only Safety Classification**: `local-only-compliance-read-model`

## Generated & Modified File Paths
* Exporter tool: [export_v5_lifecycle_read_model.py](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/tools/export_v5_lifecycle_read_model.py)
* Generated TS data packet: [contentLifecycleReadModelPacket.ts](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/data/contentLifecycleReadModelPacket.ts)
* Read model adapter: [contentLifecycleReadModelAdapter.ts](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/data/contentLifecycleReadModelAdapter.ts)
* Selectors extension: [selectors.ts](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/selectors.ts)
* Operator Review view: [OperatorReviewQueue.tsx](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/views/OperatorReviewQueue.tsx)

## UI Surfaces Touched
* **Operator Review Queue**: Added the **Content Lifecycle Spine** panel in the right sidebar. It renders all 16 stages, highlighting the current active position and showing states (completed/pending/blocked) with calm institutional statuses. Clicking any stage maps the properties to the global `selected` state, projecting details onto the generic `InspectorRail`.
