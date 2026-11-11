CC-468 is being built from operating HEAD `3ff62c1c172e63249d066153c8335a64aec46972` on `backlog/cc-468-substack-growth`.

The existing CPI reaction-table consumer now accepts NFP, FOMC and PPI public desk records. It carries the full source into the native writer, preserves exact table cells and gaps, and uses the existing article compiler and coordinator. Historical CPI projections keep their policy and shape. `scripts/prepare_cpi_reaction_page_v1.py --event NFP|FOMC|PPI` selects the corresponding family without introducing another store or publisher.

Validation on 12 November 2026: `python -m pytest -q tests/test_event_reaction_pages_cc468.py tests/test_cpi_reaction_page_cc425.py --tb=short` passed 27 tests in 4.27 seconds. This is a targeted result, not a full-suite result. The daily Note, held-source preparation and swap shortlist follow in this same item. Seven daily public readbacks, three public pages and the fourteen-day subscriber-source comparison remain operational acceptance work after the first stream integrates this delivery.

This exec performs no live step, public write or schedule change. It uses the no-red-tape skill: held computed statistics feed the existing consumer; public redistribution rights and exact source cells stay enforced. Top-level requested model and effort: gpt-6.1-sol/max; actual runtime model and effort telemetry: CONFIGURED_NOT_OBSERVED.
