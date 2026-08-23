# ADR 0001: Promote Green Recovery Output to Canonical InSave Source

- Status: Accepted for v0.18 hardening
- Date: 2026-08-23

## Context
Recovery successfully restored InSave by applying deterministic overlays to a pinned YTDLnis commit. That approach is excellent for rollback and historical reproducibility but poor as the permanent sole source of truth: string/AST-adjacent patch anchors create coupling to upstream file shape and make ordinary product refactoring difficult.

A wholesale rewrite would introduce substantially more risk because the extraction/runtime layer already works across Python, yt-dlp, FFmpeg, NewPipe and Android storage behaviors.

## Decision
Keep the reconstruction recipe, but after the full v0.18 automated quality gate is green, materialize its generated Android tree as `canonical-source/` in the InSave branch.

Promotion is allowed only from a green workflow. The promoted tree excludes upstream `.git`, Gradle caches and build outputs and includes `UPSTREAM_LOCK.json` with:
- pinned upstream repository/commit;
- InSave overlay commit;
- yt-dlp version and SHA-256;
- generated canonical tree SHA-256;
- quality workflow run ID.

A second workflow must build `canonical-source/` directly. Until that direct build passes, architecture remains below the 9/10 target.

## Consequences
Positive:
- normal InSave changes become ordinary source commits instead of patch scripts;
- code review becomes understandable at product-source level;
- modularization can happen incrementally;
- Recovery still provides reproducibility and rollback;
- upstream upgrades can be performed as explicit merge/rebase work rather than invisible runtime replacement.

Costs:
- temporary duplication between canonical source and reconstruction recipe;
- upstream upgrades require a reconciliation procedure;
- repository size increases because the Android source is materialized.

## Rejected alternatives
### Continue patch-only forever
Rejected because maintainability and architecture cannot reach the target while product ownership is encoded mainly as replay scripts.

### Rewrite InSave from scratch
Rejected because it would discard a maintained, proven extraction/runtime base and greatly increase regression risk.

### Fork upstream and immediately refactor everything
Rejected for v0.18 because it combines ownership migration, module redesign and functional changes in one uncontrolled step.
