# Media Plan Specification (Planning Only)

*This is a media/chart/card planning specification document. No actual visual rendering or image files are generated.*

**Article Title:** US Oil Export Surge: Production and SPR Dynamics Reshape Global Markets
**Draft Status:** `candidate_only`

## Asset Specifications

### US Oil Export Surge (HERO_CARD)
- **Asset ID:** `media_hero_card_v0`
- **Purpose:** Visual banner card for Substack and social preview platforms.
- **Subtitle Spec:** SPR and shale dynamics reshape global trade flows
- **Data Inputs:** None
- **Source Status:** candidate
- **Numeric Policy:** qualitative only
- **Required Caveat Overlay:** *"For review only - candidate graphics context."*
- **Layout Notes:** Dark mode background, stylized crude pipeline icon, and overlay title with clear candidate tag.
- **Should Generate Now:** `False`

### WTI Spot vs US Crude Oil Exports (CHART)
- **Asset ID:** `media_chart_wti_exports_v0`
- **Purpose:** Double-axis comparison plot of WTI crude spot prices vs. EIA exports.
- **Subtitle Spec:** Requires verified EIA crude exports / SPR / WTI data before rendering.
- **Data Inputs:** US Crude Oil Exports (EIA), WTI Crude Spot Price
- **Source Status:** candidate
- **Numeric Policy:** exact numeric plotting blocked until database values are promoted
- **Required Caveat Overlay:** *"Data requires verified main database series before rendering."*
- **Layout Notes:** Line plot charting weekly WTI prices against weekly export volumes.
- **Should Generate Now:** `False`

## Safety Invariants & Gating
- **Image Generation Permitted:** `false`
- **Chart Render Permitted:** `false`
- **Reason:** Reselected topic remains in `candidate_only` status. Exact numeric charting requires verified database promotion of the underlying series.
