# Census Access Incident — Breaking Retail Owner-Defect Repair V2

Date: 2026-08-15
Task: `TASK_CONTENTOPS_V2_BREAKING_NEWS_OWNER_DEFECT_REPAIR_V2`
General policy: `docs/automation/DATA_SOURCE_AND_DATABASE_ACCESS_CAVEATS_V1.md`

## Incident

The ContentOps workstation/runtime could not retrieve the official Census MARTS PDF through the normal network path. Requests to the Census web/PDF surface returned a Cloudflare/edge `403` or block-page response. The blocked response was rejected and was not accepted as primary evidence.

Jim later reported that he had to enable a VPN to regain access to the Census website and obtain the official PDF manually.

This establishes that the observed failure is network-/egress-path sensitive. It does **not** establish the exact WAF rule and must not be described as a proven geolocation, rate-limit, bot-score, or IP-reputation decision.

## Operator-supplied primary document

Jim supplied the official seven-page Census PDF for independent audit.

Primary identity:

- release: `CB26-131`
- title: `Advance Monthly Sales for Retail and Food Services, July 2026`
- public release: `2026-08-14 08:30 EDT`
- original official moving URL: `https://www.census.gov/retail/marts/www/marts_current.pdf`
- acquisition class: `OPERATOR_SUPPLIED_PRIMARY_DOCUMENT`
- page count: `7`
- byte size: `372889`
- SHA-256: `d11ac4c5faf5518932b6b77461bf68c61d2bc39c3d291932efb1b9e009dc5be7`

The uploaded file confirms the headline values and source language used by the Retail breaking-news proof, including `$763.6 billion`, `-0.6 percent (±0.4 percent)` month-over-month, `+5.0 percent (±0.5 percent)` year-over-year, the `not for price changes` caveat, and the 2026-09-16 next-release date.

The PDF also confirms the selected category month-over-month changes in Table 2, including motor vehicle & parts dealers `-1.8%`, nonstore retailers `-2.2%`, clothing & clothing accessories stores `+1.9%`, and food services & drinking places `+0.5%`.

## Durable evidence rule

The path `marts_current.pdf` is a moving pointer and must never be used as durable object identity.

The exact bytes should be ingested under a release-keyed immutable identity, for example:

`census_CB26-131_advance_retail_july_2026_2026-08-14.pdf`

with the original URL retained as source metadata.

## API distinction

The existence of the public Census Data API does not make the Census web/PDF path equivalent or guarantee reachability from the same IP. `api.census.gov` is a data-service surface; `www.census.gov/retail/...` delivers release HTML/PDF artifacts and can encounter a different edge/network decision.

When exact release wording, footnotes, page geometry, or document-native evidence is material, an API datum is not a byte-equivalent replacement for the primary PDF.

## Production safety

Jim's successful manual VPN access is recorded as incident evidence only.

It is **not** authorization for ContentOps automation to rotate VPNs/proxies or evade anti-bot/WAF controls.

Canonical fallback remains:

`NORMAL_OFFICIAL_ACCESS -> SAFE_OFFICIAL_ALTERNATIVE -> OPERATOR_PRIMARY_BYTES -> ABSTAIN/BLOCK`

No automated WAF circumvention.