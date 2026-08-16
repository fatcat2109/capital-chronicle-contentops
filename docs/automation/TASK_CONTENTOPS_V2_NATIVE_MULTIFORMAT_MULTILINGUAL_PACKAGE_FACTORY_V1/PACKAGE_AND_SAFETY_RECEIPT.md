# Package and Safety Receipt

## Package index

The runtime package index reports `PASS_CONTENT_ADDRESSED_PACKAGES` with eight manifests:

| Format | Locale | Package ID |
|---|---|---|
| Short | en | `pkg_2dfe4af587fd8135d04bae456b8c5b30a1560be91232b34f520cf7f05a71c0b2` |
| Longform | en | `pkg_33715fff75a0204cf430bbb763cb5ff9b6339e370b323c1d754aa6a91f24b4db` |
| Short | es | `pkg_226a7a4a7a22a469d46adb14523f24da7ae28b26c5ea6f623cef7b135be50ddd` |
| Longform | es | `pkg_75ad8f93bdc26a766c2b153dce20deaba5c707207a34c25555969d6a4b348fb4` |
| Short | pt-BR | `pkg_a979a7250abea79cd5f14a26529200d7b055b4f7eeefdd8fbbadd319ddf97f74` |
| Longform | pt-BR | `pkg_99ecfa92d7e5314494c41a063e642e99716d301e56c2b3a3bbbf5ad53ad8bc43` |
| Short | ja | `pkg_2ac7500fb5020a1b93f9618e314f8b9d20e6f2aa5a2603ba207e5d34300bf46f` |
| Longform | ja | `pkg_500ff4b61a71c794f961b53ff6ca89fae0c1467c4586709b7d813bda420f18b5` |

Package identity covers story/film identity, format, locale, exact artifact hashes, localized
metadata, chapters, rights/evidence references, intended future surfaces, generation version,
and hard boundaries. Generation timestamps and transport state are excluded from identity.

Each manifest carries:

- `transport: null`
- `publication_state: PACKAGE_ONLY_ZERO_PUBLIC_WRITE`
- `video_public_write_authority: false`
- `v1_mutation_authority: false`
- `scheduler_mutation_authority: false`
- `allow_4k: false`

The manifest validator rejects credential-, password-, secret-, session-, token-, cookie-,
and destination-account-like keys.

## Orchestration receipt

- Parent implementation/deterministic orchestration: HIGH lane.
- English Short creative author + bounded repair: separate XHIGH lane.
- Spanish localization + actual-media review: isolated XHIGH lane.
- Brazilian Portuguese localization + actual-media review: isolated XHIGH lane.
- Japanese localization + actual-media review: isolated XHIGH lane.
- No locale lane performed rendering, deterministic package work, Git operations, or platform
  operations.
- No nested lower-reasoning editorial routing occurred.

## Safety boundary audit

- No V1 code path or live runtime/store mutation.
- No scheduler, browser profile, public-write owner, or platform transport invocation.
- No credentials, cookies, tokens, sessions, or destination-account state read or written.
- No 4K render.
- No cloud TTS and no voice cloning.
- No change to the accepted 14:08 picture stream.
- No Git merge to `master` and no push other than the explicit task branch.
