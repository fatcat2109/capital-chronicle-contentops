# ContentOps Genericity and Domain Generalization Standard V1

Status: mandatory architecture authority for new ContentOps features.

## Generic by Default

ContentOps core logic is capability-first. It reasons from evidence authority,
permission, identity, event relationship, time, geography, entity, metric,
unit, claim lineage, source capability, update chains, article mode, gaps,
publication state, observations, uncertainty, and operator state. A scenario is
a fixture, never an architecture boundary.

Topic knowledge belongs in adapters, capability registries, configuration,
source parsers, bounded extraction rules, or fixtures. Generic core modules
must not contain topic-name branches, scenario IDs, URLs, hashes, dates, fixed
candidate/gap/idea/platform counts, or scenario-specific score weights.

## Separation of Responsibilities

- Core: versioned contracts, verification, generic outcomes, feature
  evaluation, ranking arithmetic, append-only decisions, and safety firewalls.
- Adapters: historical lineage, source formats, topic knowledge, and migration.
- Registries and configuration: capabilities, normalization, weights,
  thresholds, penalties, applicability, authority gates, and calibration state.
- Fixtures: synthetic or governed examples used to execute and test the core.

Core must not import a domain adapter. Adapters may import the core. A new
source, topic, domain, platform, or article mode should normally require an
adapter/registry/configuration addition and generic tests, not a core branch.

## Anti-Overfitting and Cross-Domain Proof

When a fixture fails, determine whether the fixture is invalid or the generic
abstraction is incomplete. Repair the contract or algorithm and validate the
repair in at least two unrelated domains. Do not add a one-off branch solely
to satisfy a scenario.

A feature claiming PASS must execute generic algorithms across at least 15
domain fixtures covering data, policy, rates, cross-asset markets, supply,
legal/regulatory actions, geopolitical change, physical disruption, official
documents, corporate events, confirmation, and contradiction. The matrix must
cover numeric and nonnumeric evidence; single and multiple sources,
geographies, and asset classes; scheduled and unscheduled events; authorized
and unauthorized evidence; empty, singleton, and multi-item histories,
candidates, gaps, and ideas; unavailable metrics; authoritative explicit zero;
and multiple update chains. Serialization alone is not proof.

## Unavailable Data

Unavailable, blocked, unsupported, and explicit zero are distinct states.
Unavailable values remain null with reason codes and are not silently scored
as zero. Content analysis may proceed without metrics. Performance learning
requires authoritative metric-bearing observations and adequate cohorts. One
content item distributed across multiple platforms remains one content sample.

## Evidence, Permission, and Time

Authority and permission are independent of topic. Exact consumed bytes,
declared and actual hashes, repository/branch/commit/path bindings, schema and
producer versions, logical identity, record hashes, cutoff/as-of time, and
point-in-time rules must verify before a governed artifact is accepted. Fail
closed on mismatch, missing cutoff, or future leakage.

Performance observations may influence only bounded packaging, timing,
headline, visual, format, and audience hypotheses. They may never change
claims, numeric truth, source authority, permissions, DQR, exact/proxy/context
labels, citations, risk language, or publication blockers.

## Outcome Semantics

Source-declared relationship, evidence state, authority state, history
relationship, content-gap state, actionable learning outcome, and publication
disposition are separate fields. Duplicate is identity, not filler. Packaging
gaps concern payload structure, not factual authority. Confirmation,
contradiction, correction, material update, and new phase require their
specific governed evidence. No-publication is a valid result.

## Model-Assisted Judgments

The deterministic core must run without a live model. A model record preserves
provider, model, prompt version/hash, input/output hashes, structured schema,
confidence, validation, concise rationale, and evidence references. Hidden
chain-of-thought is not stored. Model output cannot grant authority,
permission, or publication eligibility, and deterministic blockers prevail.

## PASS Evidence

Before a feature can claim generic PASS it must provide:

1. Versioned contracts and external validated configuration.
2. Cross-domain algorithm-execution evidence meeting the matrix above.
3. A machine-readable genericity guard with zero prohibited findings.
4. Empty, singleton, multi-item, unavailable, explicit-zero, authority, time,
   compatibility, deterministic, append-only, and safety tests.
5. Changed/protected-path inventories and a no-publication/no-policy-mutation
   declaration.
6. Independent review when the task classification requires it.
