---
name: Institutional ContentOps
colors:
  surface: '#fbf8ff'
  surface-dim: '#dad9e3'
  surface-bright: '#fbf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f2fd'
  surface-container: '#eeedf7'
  surface-container-high: '#e8e7f1'
  surface-container-highest: '#e3e1ec'
  on-surface: '#1a1b22'
  on-surface-variant: '#47464b'
  inverse-surface: '#2f3038'
  inverse-on-surface: '#f1effa'
  outline: '#77767b'
  outline-variant: '#c8c5cb'
  surface-tint: '#5f5e61'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#1b1b1e'
  on-primary-container: '#858387'
  inverse-primary: '#c8c5ca'
  secondary: '#5d5e60'
  on-secondary: '#ffffff'
  secondary-container: '#dfdfe0'
  on-secondary-container: '#616364'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#1a1b22'
  on-tertiary-container: '#83838c'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e4e1e6'
  primary-fixed-dim: '#c8c5ca'
  on-primary-fixed: '#1b1b1e'
  on-primary-fixed-variant: '#47464a'
  secondary-fixed: '#e2e2e3'
  secondary-fixed-dim: '#c6c6c7'
  on-secondary-fixed: '#1a1c1d'
  on-secondary-fixed-variant: '#454748'
  tertiary-fixed: '#e2e1eb'
  tertiary-fixed-dim: '#c6c6cf'
  on-tertiary-fixed: '#1a1b22'
  on-tertiary-fixed-variant: '#45464e'
  background: '#fbf8ff'
  on-background: '#1a1b22'
  surface-variant: '#e3e1ec'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-mono:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  status-code:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 12px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  container-max: 1440px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 32px
  stack-xs: 4px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 24px
---

## Brand & Style
The design system is engineered for high-stakes institutional editorial environments where precision and trust are paramount. It adopts a **Modern Corporate** aesthetic with a lean toward **Minimalist/Structural** design, prioritizing content clarity and operational efficiency over decorative elements.

The visual language draws inspiration from high-end developer tools and fintech dashboards, utilizing a rigorous grid, deliberate whitespace, and a restrained palette. The emotional response is one of calm authority; the interface acts as a quiet, reliable framework for complex decision-making and content governance. It avoids trend-heavy "glass" or "neon" effects in favor of physical metaphors of paper, ink, and architectural structure.

## Colors
The palette is rooted in a "Light Institutional" theme, utilizing a spectrum of Zinc and Graphite to create a sophisticated, low-fatigue environment.

- **Surfaces:** Use `#F9FAFB` for the lowest background layer and `#FFFFFF` for elevated cards or inspector panels to create subtle depth.
- **Borders:** A universal 1px stroke using `#E4E4E7` provides structural definition without visual noise.
- **Typography:** Primary text is set in `#18181B` (Zinc-900) for maximum legibility, with secondary metadata in `#71717A`.
- **Semantic Accents:** Colors are used strictly for status and intent. Amber is reserved for "Review Required," Red for "Blockers," and Green for "Verified/Live" states. Blue and other decorative hues are intentionally omitted to maintain a neutral, evidence-based atmosphere.
- **Dark Evidence Mode:** When active, the palette flips to a Matte Graphite (`#09090B`) background with Zinc-800 (`#27272A`) borders and muted text, simulating a secure compliance-room environment.

## Typography
The typographic system uses a dual-font strategy to distinguish between editorial content and technical metadata.

- **Primary Sans (Inter):** Used for all UI controls, body prose, and headers. It is chosen for its exceptional legibility and neutral, professional tone. Letter spacing is slightly tightened on headlines to maintain a "dense" institutional feel.
- **Monospace (JetBrains Mono):** This is a functional font used for all "evidence" data—Object IDs, timestamps, commit hashes, and system status codes. This distinction helps users immediately identify raw data versus descriptive text.
- **Hierarchy:** Maintain high contrast between labels and values. Labels should often be in the Monospace font at a smaller size (11-12px) to denote their secondary, "metadata" nature.

## Layout & Spacing
The layout follows a **Fixed-Fluid Hybrid** model. The main content area uses a structured 12-column grid for dashboard views, while document editors utilize a centered, fixed-width "prose" lane to maximize focus.

- **Inspector Rail:** A fixed 320px right-hand rail is used for object-centric metadata, properties, and the "Evidence" feed.
- **Density:** The system prioritizes "Comfortable Density." Data tables use 12px vertical padding on rows to balance information density with touch/click precision.
- **Rhythm:** All spacing units are multiples of 4px. Use 24px gutters as the standard separator between major UI panels to maintain a breathable, premium feel.

## Elevation & Depth
This design system rejects heavy shadows in favor of **Tonal Layering and Precise Outlines**.

- **Level 0 (Background):** `#F9FAFB`. The base of the application.
- **Level 1 (Panels/Cards):** `#FFFFFF` with a 1px `#E4E4E7` border. No shadow.
- **Level 2 (Modals/Popovers):** `#FFFFFF` with a 1px border and a very subtle, tight ambient shadow: `0 4px 6px -1px rgba(0, 0, 0, 0.05)`.
- **Interaction:** Hover states on interactive rows should use a subtle background shift to `#F4F4F5` rather than an elevation change. This keeps the interface feeling "flat" and architecturally sound.

## Shapes
The shape language is "Soft" yet disciplined. A **4px radius (0.25rem)** is the default for buttons, input fields, and status tokens. This minimal rounding provides a modern touch without sacrificing the professional, institutional rigor of the interface. Larger containers like cards may use up to 8px, but never more, to ensure the UI feels "constructed" rather than "molded."

## Components
- **Buttons:** Primary buttons are Solid Zinc-900 with white text. Secondary buttons use a White background with a 1px Zinc-200 border. No gradients or glows.
- **Status Tokens:** Rectangular chips with a `label-mono` typeface. Use a subtle background tint (e.g., 10% opacity of the status color) with a 1px solid border of the full-strength status color.
- **Inspector Rail:** A persistent vertical panel for "Object Properties." Use a consistent 16px internal padding. Sections are divided by 1px horizontal lines.
- **Safety Lock Strips:** For high-stakes actions (e.g., "Publish to Production"), use a diagonal "hazard" pattern in the sidebar or a locked-state toggle that requires a double-action to engage.
- **Data Tables:** Bordered on all sides. Header cells use `#F4F4F5` background with uppercase `label-mono` text.
- **Evidence Chips:** Small, monospaced badges used for IDs (e.g., `REF-8821`). These should look like small physical tags, often placed in the margins or after titles.