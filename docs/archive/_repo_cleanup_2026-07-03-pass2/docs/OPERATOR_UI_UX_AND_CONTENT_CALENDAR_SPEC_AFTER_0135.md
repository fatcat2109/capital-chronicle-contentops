# Operator UI/UX and Content Calendar Spec (0135)

## Purpose
This spec defines the UX data contract and calendar structure for the future static frontend prototype (0136). It establishes how the UI states, screens, banners, and actions are structured, strictly without creating a frontend app or exposing real execution paths.

## Screens and Safety Banners
The operator console spans multiple local-only screens ranging from content intake queue to manual metrics review.
Every screen mandates the presence of strict safety banners (e.g., `local_only`, `publish_ready_false`, `no_credentials_loaded`).

## Content Calendar Model
Lanes flow monotonically from backlog towards `manual_publish_tracking` and `manual_metrics_pending`. No state may declare a post "public_ready" or "scheduled" or "auto_published". It is mock readiness or manual publish only.

## Handoff Contract
This specification represents the handoff. No react/vite app is generated here. All components will receive dry-run cards and placeholders only. No live API integration is permitted.
