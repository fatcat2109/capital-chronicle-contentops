# V6 Unified Capability Env Readiness Operator Runbook

## Purpose

Use this readiness packet to choose the next product lane without repeating one-gate micro-task ceremony.

## Safe Commands

Generate deterministic committed sample:

```powershell
python -m live_contentops.unified_capability_env_readiness_v6 --sample --output docs/automation/V6_UNIFIED_CAPABILITY_ENV_READINESS/sample_unified_capability_env_readiness_packet.json
```

Generate local presence-only operator packet:

```powershell
python -m live_contentops.unified_capability_env_readiness_v6 --scan-mode both --dotenv-path .env --output scratch/local_capability_env_readiness.json
```

Do not commit local operator packets if they are generated from a real environment.

## Rules

- Report key names and booleans only.
- Do not print values, lengths, prefixes, suffixes, hashes, digests, or env lines.
- Do not perform provider or live writes from this readiness task.
