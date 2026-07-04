# OpenClaw Source Manifest (0174EF)

Task origin: TASK_CONTENTOPS_0174EF_OPENCLAW_FRAMEWORK_FIT_RESEARCH_AND_DECISION_PACK_V0
Inspected: 2026-06-16.

> [!IMPORTANT]
> These sources are advisory context, not runtime authority. OpenClaw was NOT installed, cloned, run, or added as a dependency. The official repo was renamed over time (Warelay → Clawdbot/Moltbot → OpenClaw); upstream changes fast. Re-verify every claim from primary sources before any action. Third-party security claims are synthesized and were not independently reproduced.

## Official OpenClaw Sources
| Source | URL | Access status | Notes |
|---|---|---|---|
| OpenClaw repo landing | https://github.com/openclaw/openclaw | readable (landing/metadata) | Confirmed title/description "Your own personal AI assistant. Any OS. Any Platform." Deep file-tree NOT cloned. |
| OpenClaw docs site | https://openclaw.ai/ | via search synthesis | Gateway, skills, security/auth, ClawHub. |
| Gateway / control plane | https://openclaw.ai (gateway docs) | via search synthesis | Local WebSocket+HTTP daemon; routing; auth modes; Node proxying. |
| Skills system | https://openclaw.ai (skills docs) | via search synthesis | skills-as-markdown (SKILL.md), precedence hierarchy. |
| Security / auth model | https://openclaw.ai (security docs) | via search synthesis | Single-operator trust model; auth modes token/password/trusted_proxy/none; `openclaw security audit`. |
| ClawHub registry | https://openclaw.ai (ClawHub docs) | via search synthesis | Public skill registry; CLI install; GitHub-link install. |

## Third-Party Security / Technical Analysis (synthesis only)
| Topic | Representative sources | Caveat |
|---|---|---|
| Agentic-AI attack surface, prompt-injection→RCE | arXiv agentic-AI security papers; Giskard; Penligent | Not independently reproduced. |
| Skill poisoning via registry | Snyk; NSFOCUS; ReversingLabs | Specific issues may be patched; treat as illustrative. |
| Persistent-memory / context poisoning (SOUL.md/MEMORY.md) | NeuralTrust; Palo Alto Networks; Salt Security; dev.to | Mechanism-level claims; verify against current build. |
| Gateway RCE / weak default auth | arXiv; vendor write-ups; openclaw.ai security runbook | Exposure-dependent; loopback-bound default reduces risk. |
| Background / general framing | Cisco; Wikipedia; DigitalOcean; NordLayer | Some are overview/marketing; not primary. |

## ContentOps Internal Sources (read-only)
| Source | Path |
|---|---|
| Open-source benchmark (0174EA) | docs/research/social_automation_open_source_benchmark_0174EA.md |
| Official API constraints (0174EA) | docs/research/social_platform_official_api_constraints_0174EA.md |
| Source manifest (0174EA) | docs/research/social_automation_source_manifest_0174EA.md |
| Supervised reference architecture (0174EA) | docs/architecture/supervised_social_publishing_reference_architecture_0174EA.md |
| ADR 0174EA | docs/decisions/ADR_0174EA_AUTOMATION_NOW_SUPERVISED_NOT_AUTONOMOUS.md |
| Execution roadmap (after 0174EA) | docs/roadmaps/social_automation_execution_roadmap_after_0174EA.md |
| Account binding model | live_contentops/social_account_binding_model.py |
| Credential handle boundary | live_contentops/social_credential_handle_boundary.py |
| X read-only identity proof gate | live_contentops/x_oauth_live_read_only_identity_proof_gate.py |
| Security scan convention | tests/test_security_scans.py |

## Source Authority Note
- Official OpenClaw landing page was readable; everything deeper is search synthesis because cloning/installing is forbidden by this task.
- No ephemeral search-citation IDs are preserved as repo authority; only stable URLs and source names above.
- Where a claim could not be verified from primary material, the companion assessment marks it explicitly under "What Was Not Verified."
