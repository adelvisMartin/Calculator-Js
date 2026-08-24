# Contributing to InSave Recovery

By contributing, you agree that your contribution may be distributed under the license applicable to the part of the project you modify. For GPL-covered software in the combined Android work, that means GPL-3.0-only unless a specific file/component states another applicable license. Do not submit code you do not have the right to contribute.

Read `LICENSE`, `THIRD_PARTY_NOTICES.md`, `TRADEMARKS.md`, `BRAND-ASSETS-LICENSE.md`, `SECURITY.md` and `CODE_OF_CONDUCT.md` before a substantial contribution.

## Branch and change discipline

Do not make feature work directly on the stable/default production branch. Recovery changes should use a dedicated branch and preserve the last-known-good reconstruction path until a replacement has passed the same gates.

Each change should have one principal purpose: provider/runtime, States, downloads/player, UI, security, build/CI or documentation. Avoid mixing unrelated refactors with a P0 bug fix.

## Before coding

1. Reproduce or define the behavior with evidence.
2. Identify whether the change belongs to InSave product code, upstream engine behavior or Recovery build tooling.
3. Add/adjust a regression gate before broad refactoring when practical.
4. Confirm no user data must be deleted/reset to apply the fix.
5. If adding a dependency/runtime, identify its exact source, version/revision, checksum strategy and license before merging it.

## Coding rules

- Kotlin/Android code should prefer typed models and explicit error states.
- No business/provider logic in Activity/Fragment when a repository/use-case boundary can own it.
- No global mutable playlist selection.
- No unbounded retries.
- No user-controlled string concatenation into shell commands.
- No secret/token/cookie logging.
- No mandatory public third-party fallback endpoint.
- No broad storage permission added to another flavor without explicit security/distribution review.
- Keep advanced downloader/runtime details behind diagnostics/settings.
- Do not introduce a dependency merely to avoid a small, maintainable implementation.
- Do not remove copyright, license or third-party attribution notices during refactors.

## Public repository / secrets

Never commit real:

- passwords or API keys;
- authentication cookies;
- session/visitor/PO tokens from users;
- signed media URLs when they contain sensitive query material;
- production signing keys/keystores;
- database/service credentials;
- private user files or unsanitized personal logs.

Use example/fake values in fixtures. If a secret is accidentally committed, rotate it; deleting the current file is not enough.

## Recovery patch rules

While the patch-driven Recovery system remains active:

- every textual patch must fail loudly when its required anchor is missing;
- each patch should include a postcondition assertion;
- avoid replacing large blocks when a smaller semantic transformation is possible;
- do not add a new patch when the same fix can be cleanly implemented in the emerging owned source tree;
- record the upstream commit the patch expects.

## Testing requirements

Minimum for a normal PR:

- compile affected source;
- relevant unit tests;
- provider/status/repository contract test where applicable;
- lint/static checks for touched InSave code;
- no new critical warning without explicit justification.

Additional for downloader/runtime changes:

- real Android E2E public-media conversion when the release gate requires it;
- Provider A failure fallback path where relevant;
- independent batch jobs;
- packaged native runtime validation;
- runtime checksum/provenance verification;
- third-party license inventory update if the payload changes.

Additional for States:

- WhatsApp + Business fixture coverage;
- Images + Videos;
- more than six items;
- scroll/search/filter;
- permission denied/fallback behavior.

Additional for navigation/UI:

- Back behavior;
- process death/configuration change where state is important;
- accessibility/content descriptions;
- screenshot evidence only as supplemental proof.

Additional for branding/launcher changes:

- application icon/roundIcon contract;
- every launchable alias checked;
- final APK resource extracted/verified where the release gate requires it;
- no third-party fork presented as an official InSave build.

## Commit conventions

Use clear scoped messages, for example:

- `fix(insave): ...`
- `feat(statuses): ...`
- `refactor(providers): ...`
- `test(android): ...`
- `security(runtime): ...`
- `docs(insave): ...`
- `docs(legal): ...`
- `ci(insave): ...`
- `chore(repo): ...`

## Review checklist

Reviewers should ask:

- Does this preserve historical accepted behavior?
- Can a provider failure affect unrelated jobs?
- Does it increase permission/network exposure?
- Is input validated at the trust boundary?
- Could it leak sensitive values in diagnostics?
- Is there an automated regression test?
- Does it make Recovery scripts more fragile?
- Does it create a migration/storage compatibility issue?
- Can the change be rolled back without data loss?
- Was any new dependency/runtime license and provenance reviewed?
- Does the change preserve GPL/third-party notices?
- Does branding create confusion between official and unofficial builds?

## Third-party code

Do not paste substantial code from another project without recording its origin and license. If external code is necessary:

1. record the upstream project and exact revision/version;
2. confirm license compatibility with the combined work;
3. preserve required copyright/license notices;
4. update `THIRD_PARTY_NOTICES.md` and SBOM/release provenance as applicable;
5. keep modifications distinguishable where the upstream license requires it.

## Brand contributions

The public GPL software license does not grant blanket rights to the InSave name/logo/launcher artwork. Brand changes need maintainer approval. Fork authors should rename/rebrand redistributed modified builds according to `TRADEMARKS.md`.

## Release changes

Any source change after a candidate has been signed/hashed invalidates the previous QA sign-off. Regenerate the APK, SHA-256 and test evidence.

Never ship or label an APK as a newer version merely by renaming the file.

## Documentation requirements

Update the relevant document when changing:

- architecture/provider ordering -> `ARCHITECTURE.md`;
- permissions/security/signing -> `SECURITY-PRIVACY.md`;
- release gates -> `QA-RELEASE.md`;
- production hardening priorities -> `ROADMAP-HARDENING.md`;
- dependency/runtime licensing -> `../THIRD_PARTY_NOTICES.md` and `LEGAL-DISTRIBUTION.md`;
- repository layout/hygiene -> `REPOSITORY-STRUCTURE.md`;
- candidate behavior -> release notes and `../CHANGELOG.md`.

## Definition of done

A task is complete when implementation, automated evidence, documentation, security/licensing provenance and rollback/migration considerations agree. A green compile without behavioral evidence is not sufficient for P0 functionality.
