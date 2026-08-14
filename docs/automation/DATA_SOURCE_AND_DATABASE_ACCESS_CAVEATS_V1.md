# Capital Chronicle ContentOps — Data Source and Database Access Caveats V1

Authority date: 2026-08-15
Status: `CURRENT_OPERATIONAL_CAVEAT`
Scope: V1/V2 evidence acquisition, database/source ingestion, primary-document retrieval, and audit provenance.

## 1. Purpose

A public source or public API does not guarantee that every delivery path for that source is reachable from every ContentOps runtime IP.

This document records the first confirmed Census access-path incident so future workers do not misclassify an edge/network block as a source outage, fabricate substitute evidence, or repeatedly retry an access path that is being denied.

## 2. Confirmed Census incident — 2026-08-15

Story context: U.S. Census Bureau, Advance Monthly Sales for Retail and Food Services, July 2026, release `CB26-131`, released 2026-08-14.

Target primary document:

`https://www.census.gov/retail/marts/www/marts_current.pdf`

Observed on the Capital Chronicle workstation/runtime network:

- direct retrieval from `www.census.gov` returned an edge/Cloudflare `403` response;
- an attempted browser-print path produced a Cloudflare block page and was rejected as evidence;
- attempts against the alternate Census web host were also blocked from the same normal egress path;
- Jim manually enabled a VPN and was then able to access the official Census site/PDF;
- Jim supplied the actual seven-page PDF to ChatGPT for independent audit;
- the supplied PDF is internally consistent with release `CB26-131`, page count `7`, file size `372889` bytes, and SHA-256 `d11ac4c5faf5518932b6b77461bf68c61d2bc39c3d291932efb1b9e009dc5be7`.

Operational interpretation:

`SOURCE_EDGE_IP_BLOCK / ACCESS_PATH_SPECIFIC`

Do **not** classify this incident as a Census-wide outage or as proof that the Census Data API is unavailable.

## 3. Why a public Census API can coexist with a blocked Census PDF/web path

The Census Data API and the Census web/PDF delivery surfaces are different access paths.

The Census Data API is a standardized data service exposed through `api.census.gov` for datasets made available through that API. Census release pages and PDF artifacts such as MARTS releases are served through `www.census.gov` paths and may traverse different CDN/WAF/edge controls.

Therefore all of the following can be true at the same time:

1. the Census Data API is public and functioning;
2. a specific `www.census.gov` PDF or HTML path is blocked for one egress IP;
3. the same PDF becomes reachable from a different network path;
4. the API does not necessarily provide a byte-identical substitute for the exact release document required by an evidence task.

The exact Census edge rule that caused this incident is **not proven**. The VPN result is consistent with an IP-/network-path-sensitive WAF/CDN decision, but ContentOps must not claim a specific reputation, geolocation, rate-limit, or bot-detection cause without direct evidence.

## 4. Canonical acquisition policy

When a trusted public source is blocked on one access path:

1. **Record the incident once.**
   - host;
   - requested URL;
   - timestamp;
   - HTTP status/error class;
   - whether the response was an edge/WAF/block page;
   - runtime/network identity only at a non-secret descriptive level;
   - no cookies, auth headers, tokens, or private session data.

2. **Do not aggressively retry or automate WAF circumvention.**
   - no proxy rotation;
   - no automated VPN switching;
   - no anti-bot bypass;
   - no private/hidden endpoint discovery.

3. **Distinguish access surfaces.**
   - `OFFICIAL_API_FETCH` when an official Census API dataset supplies the exact required data;
   - `DIRECT_OFFICIAL_FETCH` when exact official HTML/PDF bytes are retrieved normally;
   - `OPERATOR_SUPPLIED_PRIMARY_DOCUMENT` when Jim manually obtains and supplies the official primary file;
   - `OFFICIAL_HTML_EXACT_SOURCE_DERIVATIVE` when exact official release text is available but authoritative PDF bytes are not;
   - `EDGE_BLOCKED` when the exact required path cannot be reached safely.

4. **Do not silently substitute an API response for a required primary document.**
   If the task requires exact release wording, page geometry, footnotes, tables, or document-native evidence, an API value alone is not equivalent to the release PDF.

5. **Operator-supplied primary bytes are acceptable when provenance is explicit.**
   Persist:
   - original official URL;
   - release number/date/data period;
   - acquisition class `OPERATOR_SUPPLIED_PRIMARY_DOCUMENT`;
   - file size;
   - page count;
   - SHA-256;
   - immutable local evidence filename/ID;
   - later direct-fetch hash comparison if normal access becomes available.

6. **Mutable `*_current` URLs must never be treated as immutable evidence identity.**
   For example, `marts_current.pdf` is a moving pointer. Snapshot the exact bytes and key them by release identity, such as:

   `census_CB26-131_advance_retail_july_2026_2026-08-14.pdf`

   The original `marts_current.pdf` URL remains source metadata, not durable object identity.

## 5. Database/source-record fields recommended for this class of incident

Where the current schema permits, preserve or derive fields equivalent to:

- `source_id`
- `source_family = U.S._CENSUS_BUREAU`
- `source_surface = API | HTML | PDF | ARCHIVE`
- `original_url`
- `release_number`
- `release_date`
- `data_period`
- `acquisition_class`
- `retrieved_at`
- `http_status`
- `access_status = OK | EDGE_BLOCKED | DEGRADED`
- `edge_block_observed = true|false`
- `operator_vpn_required_for_manual_access = true|false`
- `content_sha256`
- `byte_size`
- `page_count`
- `immutable_evidence_id`
- `provenance_notes`

Do not store VPN configuration, VPN credentials, local IP details, cookies, request headers, or other secret/session material.

## 6. Census-specific fallback order

For Census evidence, use the narrowest truthful path that satisfies the claim:

1. exact official API dataset/value when the API actually covers the required datum;
2. exact official release HTML;
3. exact official PDF bytes;
4. official historical-release/archive surface;
5. operator-supplied official primary document with immutable hash;
6. abstain/block if the required evidence cannot be acquired or equivalently grounded.

The order is not a ranking of evidentiary strength in every case. If document wording/footnotes/page geometry are material, the exact PDF/HTML release can be required even when an API value exists.

## 7. Production rule

The fact that Jim manually used a VPN to retrieve this Census PDF is an operational clue, not permission for ContentOps to automate VPN/proxy circumvention.

Production automation must remain compatibility-first and fail closed:

`NORMAL_OFFICIAL_ACCESS -> SAFE_OFFICIAL_ALTERNATIVE -> OPERATOR_PRIMARY_BYTES -> ABSTAIN/BLOCK`

Never:

`BLOCKED -> ROTATE_PROXY/VPN -> EVADE_EDGE_CONTROLS`

## 8. Current Retail release evidence

For the 2026-08-14 Retail Sales release, the independently supplied PDF confirms:

- release `CB26-131`;
- July 2026 advance retail and food services sales `$763.6B`;
- month-over-month change `-0.6%` with `±0.4%` 90% margin;
- year-over-year change `+5.0%` with `±0.5%` margin;
- the data are seasonally/holiday/trading-day adjusted but not adjusted for price changes;
- next advance release scheduled for 2026-09-16 at 8:30 a.m. EDT;
- category changes used by the breaking-news proof are present in the official tables.

Keep statistical caveats intact. In particular, the release states that comparisons across industries have not been tested for significance.

## 9. Hard rule for future workers

A `403`, Cloudflare/WAF page, stale `*_current` response, or source-specific access failure is **evidence about the access path**, not evidence about the truth or nonexistence of the underlying official source.

Preserve the distinction, record the failure honestly, use another authorized official acquisition surface when it is genuinely equivalent, and never manufacture missing source bytes.