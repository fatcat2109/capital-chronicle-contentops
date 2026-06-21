# Platform Review Bundle Operator Decision Gate Contract

> [!IMPORTANT]
> This is an operator decision gate contract report for schema validation only.
> It creates disabled decision options and active locks only, and is not a review UI or approval system.
> It cannot approve, reject, revise, export, publish, dispatch, schedule, or call any platform APIs.

- **Task Label**: `TASK_CONTENTOPS_0175AQ_PLATFORM_REVIEW_BUNDLE_OPERATOR_DECISION_GATE_V0`
- **Matrix Version**: `0175AQ_PLATFORM_REVIEW_BUNDLE_OPERATOR_DECISION_GATE_V1`
- **Source Baseline Commit**: `ab4a851ff60121cc3c3bdd85e25ed58c07aa9766`
- **Packet Hash**: `c6de6169638892a9bef70a53db931e5aec9cfa4cbb74b7b45d69d92828bad95d`
- **Ledger Family**: `platform_review_bundle_operator_decision_gate_future`
- **Next Required Gate**: `lane_c_platform_review_bundle_operator_decision_gate`

## Invariant Validation Safety Flags

| Invariant Flag | Required State | Status |
|---|---|---|
| `local_only` | `True` | ✅ |
| `fixture_only` | `True` | ✅ |
| `schema_only` | `True` | ✅ |
| `decision_gate_only` | `True` | ✅ |
| `review_bundle_only` | `True` | ✅ |
| `network_performed` | `False` | ✅ |
| `env_read` | `False` | ✅ |
| `credential_values_loaded` | `False` | ✅ |
| `platform_api_called` | `False` | ✅ |
| `provider_api_called` | `False` | ✅ |
| `account_binding_active` | `False` | ✅ |
| `scheduler_enabled` | `False` | ✅ |
| `autonomous_posting` | `False` | ✅ |
| `autonomous_reply_or_dm` | `False` | ✅ |
| `scraping` | `False` | ✅ |
| `ingestion_repo_mutated` | `False` | ✅ |
| `dqr_cleared_by_contentops` | `False` | ✅ |
| `readiness_cleared_by_contentops` | `False` | ✅ |
| `current_truth_promoted` | `False` | ✅ |
| `public_postable` | `False` | ✅ |
| `dispatch_ready` | `False` | ✅ |
| `platform_payload_created` | `False` | ✅ |
| `publishable_payload_created` | `False` | ✅ |
| `export_ready` | `False` | ✅ |
| `approval_granted` | `False` | ✅ |
| `approved_for_publication` | `False` | ✅ |
| `operator_approval_granted` | `False` | ✅ |
| `operator_identity_bound` | `False` | ✅ |
| `operator_signature_present` | `False` | ✅ |
| `payload_hash_locked` | `False` | ✅ |
| `financial_advice` | `False` | ✅ |
| `signal_language` | `False` | ✅ |
| `broker_order_execution` | `False` | ✅ |
| `raw_vendor_redistribution` | `False` | ✅ |
| `approved_internal_alpha_artifacts_available` | `False` | ✅ |
| `publishable_text` | `False` | ✅ |
| `platform_ready` | `False` | ✅ |

## Decision Gate Summary Counts

- **Registered Decision Gate Records**: `10`
- **Decision Options Configured**: `6`
- **Decision Locks Enforced**: `10`
- **Evidence Requirements Defined**: `5`

## Blocked Capabilities & Missing Gates

### Blocked Capabilities
- `live_publishing_dispatch`
- `autonomous_reply_automation`
- `live_credential_hydration`
- `active_scheduler_triggers`
- `manual_review_export`

### Missing Future Gates
- `lane_c_platform_review_bundle_operator_decision_gate`
- `production_key_vault_decrypter`
- `live_operator_signature_vault`

## Platform Operator Decision Gate Records

### Decision Gate: `decision_gate_x`

- **Source Bundle Item ID**: `bundle_item_x`
- **Source Render ID**: `dry_render_x`
- **Platform Target ID**: `x`
- **Platform Family**: `x_microblog`
- **Gate Status**: `decision_gate_blocked`
- **Operator Review Required**: `True`
- **Manual Decision Required**: `True`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Export Gate**: `export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`
- **Approval Granted**: `False`
- **Rejection Recorded**: `False`
- **Revision Requested**: `False`
- **Export Ready**: `False`
- **Dispatch Ready**: `False`

#### Decision Options (Disabled)

| Option ID | Enabled | Available Now | Requires Future Gate |
|---|---|---|---|
| `approve_for_publication` | `False` | `False` | `True` |
| `reject_bundle` | `False` | `False` | `True` |
| `request_revision` | `False` | `False` | `True` |
| `hold_for_more_evidence` | `False` | `False` | `True` |
| `export_for_manual_publish` | `False` | `False` | `True` |
| `dispatch_to_platform` | `False` | `False` | `True` |

#### Decision Locks (Active)

| Lock ID | Description | Active Status |
|---|---|---|
| `lock_no_operator_identity` | Operator identity is not bound to the session. | `True` |
| `lock_no_operator_signature` | Cryptographic approval signature is missing. | `True` |
| `lock_no_payload_hash_lock` | Payload hash lock is not verified. | `True` |
| `lock_unresolved_citations` | Citations are unresolved or pending verification. | `True` |
| `lock_unresolved_limitations` | Limitations acknowledgement is pending. | `True` |
| `lock_dqr_readiness_unresolved` | DQR audit and publish readiness checks are unresolved. | `True` |
| `lock_no_account_binding` | Platform account binding is inactive. | `True` |
| `lock_no_credential_gate` | Credential gate authentication is required but locked. | `True` |
| `lock_no_export_gate` | Export gate has not been cleared. | `True` |
| `lock_no_dispatch_gate` | Dispatch gate has not cleared the post. | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |

### Decision Gate: `decision_gate_telegram_channel_destination`

- **Source Bundle Item ID**: `bundle_item_telegram_channel_destination`
- **Source Render ID**: `dry_render_telegram_channel_destination`
- **Platform Target ID**: `telegram_channel_destination`
- **Platform Family**: `telegram_chat`
- **Gate Status**: `decision_gate_blocked`
- **Operator Review Required**: `True`
- **Manual Decision Required**: `True`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Export Gate**: `export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`
- **Approval Granted**: `False`
- **Rejection Recorded**: `False`
- **Revision Requested**: `False`
- **Export Ready**: `False`
- **Dispatch Ready**: `False`

#### Decision Options (Disabled)

| Option ID | Enabled | Available Now | Requires Future Gate |
|---|---|---|---|
| `approve_for_publication` | `False` | `False` | `True` |
| `reject_bundle` | `False` | `False` | `True` |
| `request_revision` | `False` | `False` | `True` |
| `hold_for_more_evidence` | `False` | `False` | `True` |
| `export_for_manual_publish` | `False` | `False` | `True` |
| `dispatch_to_platform` | `False` | `False` | `True` |

#### Decision Locks (Active)

| Lock ID | Description | Active Status |
|---|---|---|
| `lock_no_operator_identity` | Operator identity is not bound to the session. | `True` |
| `lock_no_operator_signature` | Cryptographic approval signature is missing. | `True` |
| `lock_no_payload_hash_lock` | Payload hash lock is not verified. | `True` |
| `lock_unresolved_citations` | Citations are unresolved or pending verification. | `True` |
| `lock_unresolved_limitations` | Limitations acknowledgement is pending. | `True` |
| `lock_dqr_readiness_unresolved` | DQR audit and publish readiness checks are unresolved. | `True` |
| `lock_no_account_binding` | Platform account binding is inactive. | `True` |
| `lock_no_credential_gate` | Credential gate authentication is required but locked. | `True` |
| `lock_no_export_gate` | Export gate has not been cleared. | `True` |
| `lock_no_dispatch_gate` | Dispatch gate has not cleared the post. | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |

### Decision Gate: `decision_gate_telegram_remote_operator`

- **Source Bundle Item ID**: `bundle_item_telegram_remote_operator`
- **Source Render ID**: `dry_render_telegram_remote_operator`
- **Platform Target ID**: `telegram_remote_operator`
- **Platform Family**: `telegram_chat`
- **Gate Status**: `decision_gate_blocked`
- **Operator Review Required**: `True`
- **Manual Decision Required**: `True`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Export Gate**: `export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`
- **Approval Granted**: `False`
- **Rejection Recorded**: `False`
- **Revision Requested**: `False`
- **Export Ready**: `False`
- **Dispatch Ready**: `False`

#### Decision Options (Disabled)

| Option ID | Enabled | Available Now | Requires Future Gate |
|---|---|---|---|
| `approve_for_publication` | `False` | `False` | `True` |
| `reject_bundle` | `False` | `False` | `True` |
| `request_revision` | `False` | `False` | `True` |
| `hold_for_more_evidence` | `False` | `False` | `True` |
| `export_for_manual_publish` | `False` | `False` | `True` |
| `dispatch_to_platform` | `False` | `False` | `True` |

#### Decision Locks (Active)

| Lock ID | Description | Active Status |
|---|---|---|
| `lock_no_operator_identity` | Operator identity is not bound to the session. | `True` |
| `lock_no_operator_signature` | Cryptographic approval signature is missing. | `True` |
| `lock_no_payload_hash_lock` | Payload hash lock is not verified. | `True` |
| `lock_unresolved_citations` | Citations are unresolved or pending verification. | `True` |
| `lock_unresolved_limitations` | Limitations acknowledgement is pending. | `True` |
| `lock_dqr_readiness_unresolved` | DQR audit and publish readiness checks are unresolved. | `True` |
| `lock_no_account_binding` | Platform account binding is inactive. | `True` |
| `lock_no_credential_gate` | Credential gate authentication is required but locked. | `True` |
| `lock_no_export_gate` | Export gate has not been cleared. | `True` |
| `lock_no_dispatch_gate` | Dispatch gate has not cleared the post. | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |

### Decision Gate: `decision_gate_substack`

- **Source Bundle Item ID**: `bundle_item_substack`
- **Source Render ID**: `dry_render_substack`
- **Platform Target ID**: `substack`
- **Platform Family**: `substack_newsletter`
- **Gate Status**: `decision_gate_blocked`
- **Operator Review Required**: `True`
- **Manual Decision Required**: `True`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Export Gate**: `export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`
- **Approval Granted**: `False`
- **Rejection Recorded**: `False`
- **Revision Requested**: `False`
- **Export Ready**: `False`
- **Dispatch Ready**: `False`

#### Decision Options (Disabled)

| Option ID | Enabled | Available Now | Requires Future Gate |
|---|---|---|---|
| `approve_for_publication` | `False` | `False` | `True` |
| `reject_bundle` | `False` | `False` | `True` |
| `request_revision` | `False` | `False` | `True` |
| `hold_for_more_evidence` | `False` | `False` | `True` |
| `export_for_manual_publish` | `False` | `False` | `True` |
| `dispatch_to_platform` | `False` | `False` | `True` |

#### Decision Locks (Active)

| Lock ID | Description | Active Status |
|---|---|---|
| `lock_no_operator_identity` | Operator identity is not bound to the session. | `True` |
| `lock_no_operator_signature` | Cryptographic approval signature is missing. | `True` |
| `lock_no_payload_hash_lock` | Payload hash lock is not verified. | `True` |
| `lock_unresolved_citations` | Citations are unresolved or pending verification. | `True` |
| `lock_unresolved_limitations` | Limitations acknowledgement is pending. | `True` |
| `lock_dqr_readiness_unresolved` | DQR audit and publish readiness checks are unresolved. | `True` |
| `lock_no_account_binding` | Platform account binding is inactive. | `True` |
| `lock_no_credential_gate` | Credential gate authentication is required but locked. | `True` |
| `lock_no_export_gate` | Export gate has not been cleared. | `True` |
| `lock_no_dispatch_gate` | Dispatch gate has not cleared the post. | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |

### Decision Gate: `decision_gate_linkedin`

- **Source Bundle Item ID**: `bundle_item_linkedin`
- **Source Render ID**: `dry_render_linkedin`
- **Platform Target ID**: `linkedin`
- **Platform Family**: `linkedin_professional`
- **Gate Status**: `decision_gate_blocked`
- **Operator Review Required**: `True`
- **Manual Decision Required**: `True`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Export Gate**: `export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`
- **Approval Granted**: `False`
- **Rejection Recorded**: `False`
- **Revision Requested**: `False`
- **Export Ready**: `False`
- **Dispatch Ready**: `False`

#### Decision Options (Disabled)

| Option ID | Enabled | Available Now | Requires Future Gate |
|---|---|---|---|
| `approve_for_publication` | `False` | `False` | `True` |
| `reject_bundle` | `False` | `False` | `True` |
| `request_revision` | `False` | `False` | `True` |
| `hold_for_more_evidence` | `False` | `False` | `True` |
| `export_for_manual_publish` | `False` | `False` | `True` |
| `dispatch_to_platform` | `False` | `False` | `True` |

#### Decision Locks (Active)

| Lock ID | Description | Active Status |
|---|---|---|
| `lock_no_operator_identity` | Operator identity is not bound to the session. | `True` |
| `lock_no_operator_signature` | Cryptographic approval signature is missing. | `True` |
| `lock_no_payload_hash_lock` | Payload hash lock is not verified. | `True` |
| `lock_unresolved_citations` | Citations are unresolved or pending verification. | `True` |
| `lock_unresolved_limitations` | Limitations acknowledgement is pending. | `True` |
| `lock_dqr_readiness_unresolved` | DQR audit and publish readiness checks are unresolved. | `True` |
| `lock_no_account_binding` | Platform account binding is inactive. | `True` |
| `lock_no_credential_gate` | Credential gate authentication is required but locked. | `True` |
| `lock_no_export_gate` | Export gate has not been cleared. | `True` |
| `lock_no_dispatch_gate` | Dispatch gate has not cleared the post. | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |

### Decision Gate: `decision_gate_threads`

- **Source Bundle Item ID**: `bundle_item_threads`
- **Source Render ID**: `dry_render_threads`
- **Platform Target ID**: `threads`
- **Platform Family**: `threads_microblog`
- **Gate Status**: `decision_gate_blocked`
- **Operator Review Required**: `True`
- **Manual Decision Required**: `True`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Export Gate**: `export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`
- **Approval Granted**: `False`
- **Rejection Recorded**: `False`
- **Revision Requested**: `False`
- **Export Ready**: `False`
- **Dispatch Ready**: `False`

#### Decision Options (Disabled)

| Option ID | Enabled | Available Now | Requires Future Gate |
|---|---|---|---|
| `approve_for_publication` | `False` | `False` | `True` |
| `reject_bundle` | `False` | `False` | `True` |
| `request_revision` | `False` | `False` | `True` |
| `hold_for_more_evidence` | `False` | `False` | `True` |
| `export_for_manual_publish` | `False` | `False` | `True` |
| `dispatch_to_platform` | `False` | `False` | `True` |

#### Decision Locks (Active)

| Lock ID | Description | Active Status |
|---|---|---|
| `lock_no_operator_identity` | Operator identity is not bound to the session. | `True` |
| `lock_no_operator_signature` | Cryptographic approval signature is missing. | `True` |
| `lock_no_payload_hash_lock` | Payload hash lock is not verified. | `True` |
| `lock_unresolved_citations` | Citations are unresolved or pending verification. | `True` |
| `lock_unresolved_limitations` | Limitations acknowledgement is pending. | `True` |
| `lock_dqr_readiness_unresolved` | DQR audit and publish readiness checks are unresolved. | `True` |
| `lock_no_account_binding` | Platform account binding is inactive. | `True` |
| `lock_no_credential_gate` | Credential gate authentication is required but locked. | `True` |
| `lock_no_export_gate` | Export gate has not been cleared. | `True` |
| `lock_no_dispatch_gate` | Dispatch gate has not cleared the post. | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |

### Decision Gate: `decision_gate_instagram`

- **Source Bundle Item ID**: `bundle_item_instagram`
- **Source Render ID**: `dry_render_instagram`
- **Platform Target ID**: `instagram`
- **Platform Family**: `instagram_media`
- **Gate Status**: `decision_gate_blocked`
- **Operator Review Required**: `True`
- **Manual Decision Required**: `True`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Export Gate**: `export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`
- **Approval Granted**: `False`
- **Rejection Recorded**: `False`
- **Revision Requested**: `False`
- **Export Ready**: `False`
- **Dispatch Ready**: `False`

#### Decision Options (Disabled)

| Option ID | Enabled | Available Now | Requires Future Gate |
|---|---|---|---|
| `approve_for_publication` | `False` | `False` | `True` |
| `reject_bundle` | `False` | `False` | `True` |
| `request_revision` | `False` | `False` | `True` |
| `hold_for_more_evidence` | `False` | `False` | `True` |
| `export_for_manual_publish` | `False` | `False` | `True` |
| `dispatch_to_platform` | `False` | `False` | `True` |

#### Decision Locks (Active)

| Lock ID | Description | Active Status |
|---|---|---|
| `lock_no_operator_identity` | Operator identity is not bound to the session. | `True` |
| `lock_no_operator_signature` | Cryptographic approval signature is missing. | `True` |
| `lock_no_payload_hash_lock` | Payload hash lock is not verified. | `True` |
| `lock_unresolved_citations` | Citations are unresolved or pending verification. | `True` |
| `lock_unresolved_limitations` | Limitations acknowledgement is pending. | `True` |
| `lock_dqr_readiness_unresolved` | DQR audit and publish readiness checks are unresolved. | `True` |
| `lock_no_account_binding` | Platform account binding is inactive. | `True` |
| `lock_no_credential_gate` | Credential gate authentication is required but locked. | `True` |
| `lock_no_export_gate` | Export gate has not been cleared. | `True` |
| `lock_no_dispatch_gate` | Dispatch gate has not cleared the post. | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |

### Decision Gate: `decision_gate_facebook_page`

- **Source Bundle Item ID**: `bundle_item_facebook_page`
- **Source Render ID**: `dry_render_facebook_page`
- **Platform Target ID**: `facebook_page`
- **Platform Family**: `facebook_page_media`
- **Gate Status**: `decision_gate_blocked`
- **Operator Review Required**: `True`
- **Manual Decision Required**: `True`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Export Gate**: `export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`
- **Approval Granted**: `False`
- **Rejection Recorded**: `False`
- **Revision Requested**: `False`
- **Export Ready**: `False`
- **Dispatch Ready**: `False`

#### Decision Options (Disabled)

| Option ID | Enabled | Available Now | Requires Future Gate |
|---|---|---|---|
| `approve_for_publication` | `False` | `False` | `True` |
| `reject_bundle` | `False` | `False` | `True` |
| `request_revision` | `False` | `False` | `True` |
| `hold_for_more_evidence` | `False` | `False` | `True` |
| `export_for_manual_publish` | `False` | `False` | `True` |
| `dispatch_to_platform` | `False` | `False` | `True` |

#### Decision Locks (Active)

| Lock ID | Description | Active Status |
|---|---|---|
| `lock_no_operator_identity` | Operator identity is not bound to the session. | `True` |
| `lock_no_operator_signature` | Cryptographic approval signature is missing. | `True` |
| `lock_no_payload_hash_lock` | Payload hash lock is not verified. | `True` |
| `lock_unresolved_citations` | Citations are unresolved or pending verification. | `True` |
| `lock_unresolved_limitations` | Limitations acknowledgement is pending. | `True` |
| `lock_dqr_readiness_unresolved` | DQR audit and publish readiness checks are unresolved. | `True` |
| `lock_no_account_binding` | Platform account binding is inactive. | `True` |
| `lock_no_credential_gate` | Credential gate authentication is required but locked. | `True` |
| `lock_no_export_gate` | Export gate has not been cleared. | `True` |
| `lock_no_dispatch_gate` | Dispatch gate has not cleared the post. | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |

### Decision Gate: `decision_gate_tiktok`

- **Source Bundle Item ID**: `bundle_item_tiktok`
- **Source Render ID**: `dry_render_tiktok`
- **Platform Target ID**: `tiktok`
- **Platform Family**: `tiktok_video`
- **Gate Status**: `decision_gate_blocked`
- **Operator Review Required**: `True`
- **Manual Decision Required**: `True`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Export Gate**: `export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`
- **Approval Granted**: `False`
- **Rejection Recorded**: `False`
- **Revision Requested**: `False`
- **Export Ready**: `False`
- **Dispatch Ready**: `False`

#### Decision Options (Disabled)

| Option ID | Enabled | Available Now | Requires Future Gate |
|---|---|---|---|
| `approve_for_publication` | `False` | `False` | `True` |
| `reject_bundle` | `False` | `False` | `True` |
| `request_revision` | `False` | `False` | `True` |
| `hold_for_more_evidence` | `False` | `False` | `True` |
| `export_for_manual_publish` | `False` | `False` | `True` |
| `dispatch_to_platform` | `False` | `False` | `True` |

#### Decision Locks (Active)

| Lock ID | Description | Active Status |
|---|---|---|
| `lock_no_operator_identity` | Operator identity is not bound to the session. | `True` |
| `lock_no_operator_signature` | Cryptographic approval signature is missing. | `True` |
| `lock_no_payload_hash_lock` | Payload hash lock is not verified. | `True` |
| `lock_unresolved_citations` | Citations are unresolved or pending verification. | `True` |
| `lock_unresolved_limitations` | Limitations acknowledgement is pending. | `True` |
| `lock_dqr_readiness_unresolved` | DQR audit and publish readiness checks are unresolved. | `True` |
| `lock_no_account_binding` | Platform account binding is inactive. | `True` |
| `lock_no_credential_gate` | Credential gate authentication is required but locked. | `True` |
| `lock_no_export_gate` | Export gate has not been cleared. | `True` |
| `lock_no_dispatch_gate` | Dispatch gate has not cleared the post. | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |

### Decision Gate: `decision_gate_youtube`

- **Source Bundle Item ID**: `bundle_item_youtube`
- **Source Render ID**: `dry_render_youtube`
- **Platform Target ID**: `youtube`
- **Platform Family**: `youtube_video`
- **Gate Status**: `decision_gate_blocked`
- **Operator Review Required**: `True`
- **Manual Decision Required**: `True`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Export Gate**: `export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`
- **Approval Granted**: `False`
- **Rejection Recorded**: `False`
- **Revision Requested**: `False`
- **Export Ready**: `False`
- **Dispatch Ready**: `False`

#### Decision Options (Disabled)

| Option ID | Enabled | Available Now | Requires Future Gate |
|---|---|---|---|
| `approve_for_publication` | `False` | `False` | `True` |
| `reject_bundle` | `False` | `False` | `True` |
| `request_revision` | `False` | `False` | `True` |
| `hold_for_more_evidence` | `False` | `False` | `True` |
| `export_for_manual_publish` | `False` | `False` | `True` |
| `dispatch_to_platform` | `False` | `False` | `True` |

#### Decision Locks (Active)

| Lock ID | Description | Active Status |
|---|---|---|
| `lock_no_operator_identity` | Operator identity is not bound to the session. | `True` |
| `lock_no_operator_signature` | Cryptographic approval signature is missing. | `True` |
| `lock_no_payload_hash_lock` | Payload hash lock is not verified. | `True` |
| `lock_unresolved_citations` | Citations are unresolved or pending verification. | `True` |
| `lock_unresolved_limitations` | Limitations acknowledgement is pending. | `True` |
| `lock_dqr_readiness_unresolved` | DQR audit and publish readiness checks are unresolved. | `True` |
| `lock_no_account_binding` | Platform account binding is inactive. | `True` |
| `lock_no_credential_gate` | Credential gate authentication is required but locked. | `True` |
| `lock_no_export_gate` | Export gate has not been cleared. | `True` |
| `lock_no_dispatch_gate` | Dispatch gate has not cleared the post. | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |
