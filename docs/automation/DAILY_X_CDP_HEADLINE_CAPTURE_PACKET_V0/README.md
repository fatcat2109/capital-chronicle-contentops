# Daily X CDP Headline Capture Packet (Step 1)

This module implements Step 1 of the definitive Daily ContentOps loop: capturing/ingesting X/CDP headlines from the last successful checkpoint or the last 24 hours, and segmenting them into a local evidence file.

## Operation

- Daily ContentOps begins by collecting X/CDP headlines from the last successful checkpoint, or from the last 24 hours when no checkpoint exists.
- The headline pull is written to a local evidence file (`headlines_raw_v0.json`) before any downstream article decision.
- Headlines are clustered, deduped, ranked, and eventually converted into article ideas.
- Public dispatch remains separately gated and is not treated as proven by the fast fixture-based Discord post.
- ContentOps does not mutate the main database; the Capital Chronicle local database remains the numeric/source/context authority.

## Verification Details
- **Capture Mode**: `fixture_local` (live X/CDP capture not proven, no browser/session scrape occurred).
- **Previous Checkpoint**: Derived from `checkpoint_state_v0.json` or falls back to last 24 hours.
- **Output Files**:
  - `headlines_raw_v0.json`: Normalized lists of captured headlines.
  - `checkpoint_state_v0.json`: Tracks historical run windows.
  - `run_evidence_v0.json`: Proves task completion boundaries.
