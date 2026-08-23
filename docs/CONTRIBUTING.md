# Contributing to InSave Recovery

## Branch and change discipline

Do not make feature work directly on the stable/default production branch. Recovery changes should use a dedicated branch and preserve the last-known-good reconstruction path until a replacement has passed the same gates.

Each change should have one principal purpose: provider/runtime, States, downloads/player, UI, security, build/CI or documentation. Avoid mixing unrelated refactors with a P0 bug fix.

## Before coding

1. Reproduce or define the behavior with evidence.
2. Identify whether the change belongs to InSave product code, upstream engine behavior or Recovery build tooling.
3. Add/adjust a regression gate before broad refactoring when practical.
4. Confirm no user data must be deleted/reset to apply the fix.

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
- provider/status/repository contract test;
- lint/static checks for touched code;
- no new compiler warning without explicit justification.

Additional for downloader/runtime changes:

- real Android E2E public media conversion;
- Provider A failure fallback path where relevant;
- independent batch jobs;
- packaged native runtime validation.

Additional for States:

- WhatsApp + Business fixture coverage;
- Images + Videos;
- >6 items;
- scroll/search/filter;
- permission denied/fallback behavior.

Additional for navigation/UI:

- Back behavior;
- process death/configuration change where state is important;
- accessibility/content descriptions;
- screenshot evidence only as supplemental proof.

## Commit conventions

Use clear scoped messages, for example:

- `fix(insave): ...`
- `feat(statuses): ...`
- `refactor(providers): ...`
- `test(android): ...`
- `security(runtime): ...`
- `docs(insave): ...`
- `ci(insave): ...`

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

## Release changes

Any source change after a candidate has been signed/hashed invalidates the previous QA sign-off. Regenerate the APK, SHA-256 and test evidence.

Never ship or label an APK as a newer version merely by renaming the file.

## Documentation requirements

Update the relevant document when changing:

- architecture/provider ordering -> `ARCHITECTURE.md`;
- permissions/security/signing -> `SECURITY-PRIVACY.md`;
- release gates -> `QA-RELEASE.md`;
- production hardening priorities -> `ROADMAP-HARDENING.md`;
- candidate behavior -> release notes.

## Definition of done

A task is complete when implementation, automated evidence, documentation and rollback/migration considerations agree. A green compile without behavioral evidence is not sufficient for P0 functionality.
