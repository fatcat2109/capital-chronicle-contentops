---
name: Technical Matte Operator
colors:
  surface: '#141313'
  surface-dim: '#141313'
  surface-bright: '#3a3939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1c'
  surface-container: '#201f20'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353435'
  on-surface: '#e5e2e1'
  on-surface-variant: '#c6c6ca'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#8f9094'
  outline-variant: '#45474a'
  surface-tint: '#c6c6ca'
  primary: '#c6c6ca'
  on-primary: '#2f3034'
  primary-container: '#121417'
  on-primary-container: '#7d7e82'
  inverse-primary: '#5d5e62'
  secondary: '#c4c6ce'
  on-secondary: '#2d3037'
  secondary-container: '#464950'
  on-secondary-container: '#b6b8c0'
  tertiary: '#cfc5bc'
  on-tertiary: '#362f29'
  tertiary-container: '#18130e'
  on-tertiary-container: '#867d75'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e2e2e6'
  primary-fixed-dim: '#c6c6ca'
  on-primary-fixed: '#1a1c1f'
  on-primary-fixed-variant: '#45474a'
  secondary-fixed: '#e1e2ea'
  secondary-fixed-dim: '#c4c6ce'
  on-secondary-fixed: '#191c22'
  on-secondary-fixed-variant: '#44474d'
  tertiary-fixed: '#ece0d8'
  tertiary-fixed-dim: '#cfc5bc'
  on-tertiary-fixed: '#201b15'
  on-tertiary-fixed-variant: '#4d453f'
  background: '#141313'
  on-background: '#e5e2e1'
  surface-variant: '#353435'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  body-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 16px
  mono-label:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.02em
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  safety-status:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
spacing:
  safety-ribbon-height: 32px
  nav-width: 220px
  gutter: 1rem
  panel-padding: 1.25rem
  stack-sm: 0.25rem
  stack-md: 0.75rem
---

## Brand & Style

The design system is engineered for high-stakes institutional environments where precision, auditability, and speed of comprehension are paramount. It adopts a **Technical Matte** aesthetic—a synthesis of high-density functionalism and modern digital cockpit design.

The brand personality is authoritative, cold, and hyper-logical. It evokes the emotional response of a mission-critical governance terminal: calm under pressure, transparent in its logic, and unyielding in its safety protocols. 

Visually, the system utilizes a **Corporate / Modern** framework stripped of decorative flourish and pushed toward **Minimalist Brutalism**. Key characteristics include:
- **Zero Gradients:** Solid fills only to ensure optical clarity across different panel types.
- **Flat Depth:** Hierarchy is established through tonal stepping rather than shadows.
- **Data Density:** Tight groupings and small, legible typography allow for maximum information display without cognitive overload.
- **Rigid Structure:** A strict adherence to 1px alignment and gridlines to reinforce the "instrumentation" feel.

## Colors

The palette is strictly functional, utilizing a dark-mode-only foundation to reduce eye strain during prolonged monitoring. 

- **Foundation:** The base uses a dark graphite (#121417) for the primary background, with panels layered in a slightly lighter black-blue (#1A1D23).
- **Functional Accents:**
    - **Cyan/Blue:** Reserved for system metadata, information nodes, and active navigation states.
    - **Amber:** Indicates "Review Required" or "Pending State." It is a cautionary color, not a warning.
    - **Red:** Used exclusively for "Kill-Switch" active states, blockers, or critical system failures.
    - **Green:** Indicates "Validation Pass" or "Safe State." 
- **Semantics:** Color never implies market sentiment (bull/bear). It exclusively communicates the health and status of the governance logic and software gates.
- **Borders:** A consistent 1px stroke (#2A2E35) is used to define panel boundaries and input areas.

## Typography

The typography system prioritizes legibility at small sizes. **Inter** is the primary typeface for UI controls and labels, chosen for its excellent x-height and neutral character. **JetBrains Mono** is employed for all variable data, hash IDs, evidence references, and terminal outputs to distinguish machine-generated content from interface instructions.

- **Scale:** Sizes are intentionally compact (11px-20px) to support high information density.
- **Hierarchy:** Bold weights are used sparingly for section headers; status is primarily communicated through color and mono-spacing.
- **Casing:** Uppercase is used for global safety statuses and button labels to provide a distinct "cockpit" feel.

## Layout & Spacing

The layout is a **fixed-fluid hybrid** designed to behave like a physical hardware console.

- **Safety Ribbon:** A persistent 32px bar at the top of the viewport displays global status (Local Only, Kill Switch, etc.). This never scrolls.
- **Navigation:** A 220px vertical left-hand navigation column provides a clear hierarchical map of the terminal.
- **Grid System:** The content area utilizes a column-based grid with 1px vertical and horizontal gridlines separating logical groupings. 
- **Grouping:** Information is organized into "Modules" or "Cards" with a standard 1.25rem internal padding.
- **Rhythm:** A tight 4px baseline grid ensures that technical data lines up perfectly across adjacent columns, facilitating easy "eye-scanning" of tabular data.

## Elevation & Depth

This design system avoids physical shadows or blurs. Depth is purely architectural, expressed through **Tonal Layers** and **1px Borders**.

1.  **Level 0 (Base):** #121417 — The main terminal background.
2.  **Level 1 (Panels):** #1A1D23 — Used for content modules, tables, and the navigation bar.
3.  **Level 2 (Insets):** #000000 — Used for input fields, terminal logs, and "sunken" data areas to suggest where the operator enters information.

Visual separation is reinforced by 1px solid borders in #2A2E35. Active states (such as the selected nav item) use a cyan left-border indicator rather than a drop shadow.

## Shapes

The shape language is **Sharp (0px)**. 

To maintain the institutional, technical feel, all panels, buttons, chips, and input fields utilize 90-degree corners. This maximizes pixel-perfect rendering and reinforces the rigid, non-decorative nature of the governance software. 

The only exception to the "sharp" rule is the use of circular status indicators (pills) for small binary lights, though the containers they sit in remain strictly rectangular.

## Components

- **Safety Ribbon Chips:** Small, rectangular tags in the top bar. High-contrast text on dark backgrounds; color-coded by severity.
- **Buttons:** Sharp 1px bordered boxes. Primary actions use a subtle cyan border; secondary actions use gray. No hover gradients; hover states are indicated by a slight shift in background luminosity or border brightness.
- **Status Chips:** Mono-spaced text inside a sharp border. The background color should be a low-opacity version of the status color (e.g., 10% Cyan) with a 100% opacity border and text.
- **Data Tables:** No row stripping. Use 1px horizontal dividers. Monospace font for all numeric and ID data. 
- **Vertical Nav:** Clean text list. The active state is indicated by the Cyan primary color for the text and a 2px vertical bar on the extreme left.
- **Inputs:** Darker background than the panel (#000000), 1px border. Focus state is a 1px Cyan border glow.
- **Evidence Cards:** Grouped containers for review data. Must include a header with a "Mono-Label" describing the source or hash of the evidence.