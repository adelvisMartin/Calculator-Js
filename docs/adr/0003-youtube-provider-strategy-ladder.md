# ADR 0003: Bounded YouTube Provider Strategy Ladder

- Status: Accepted
- Date: 2026-08-23

## Context
YouTube extraction behavior changes frequently and can challenge individual videos/sessions differently. v0.17.2 proved fresh dynamic per-video PO generation but a fixed second public QA video could still receive a bot challenge. Treating every failure as identical either creates brittle tests or encourages uncontrolled fallback behavior.

## Decision
Keep Provider A/B/C, but make Provider B itself a bounded strategy ladder with explicit failure classification.

1. Provider A — maintained NewPipe path when suitable.
2. Provider B1 — local yt-dlp, `mweb`, fresh per-video PO token.
3. Provider B2 — local yt-dlp, `web_embedded`, only after recoverable bot/403/no-format/transient failure.
4. Provider B3 — local yt-dlp, `android_vr`, same recoverable-failure restriction.
5. Provider C — optional explicitly configured self-hosted endpoint, last.

A B2/B3 request clears mweb client/token arguments rather than reusing token material bound to a different strategy.

## Non-recoverable classes
Cancellation, private content, members-only/auth-required content, age/auth failures and genuinely unavailable/removed content do not silently enter the anonymous fallback ladder.

## QA decision
Use a small public-video candidate pool for runtime tests. The gate still requires real media outputs; it does not accept a source-contract-only PASS. One Provider B test needs at least one real MP3 from the candidate pool, and batch testing requires two distinct successful real MP3 outputs from independent jobs.

## Security/observability
Provider/client and failure class may be logged. PO tokens, visitor data, cookies, API keys and signed URL token parameters are redacted.

## Consequences
- resilience improves without infinite retry behavior;
- private/auth content is handled honestly;
- a single challenged test asset no longer invalidates the whole app;
- runtime path is more complex, so request-contract and real-output tests are mandatory.
