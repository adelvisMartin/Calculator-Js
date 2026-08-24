# Security Policy

## Supported line

Security work currently targets the maintained InSave `0.18.x` Recovery/QA
line and later descendants that explicitly state they are supported. Older
Recovery builds are historical evidence and should not be assumed secure.

## Reporting a vulnerability

Do **not** publish exploit details, credentials, cookies, PO tokens, signed media
URLs, personal paths or other sensitive evidence in a public GitHub issue.

For a suspected security vulnerability:

1. contact the repository owner privately through an available GitHub private
   security-reporting channel when enabled;
2. if private reporting is unavailable, open a minimal public issue that states
   only that a private security report is needed — do not include exploit
   details or secrets;
3. include the affected InSave version/commit, Android version, reproduction
   conditions and impact once a private channel is established.

## What counts as security-sensitive

Examples include:

- credential, cookie, token or signed-URL disclosure;
- unsafe WebView or JavaScript bridge behavior;
- command/shell injection;
- path traversal or arbitrary file overwrite;
- unintended private-network access/SSRF;
- malicious media/input causing code execution or privilege escalation;
- release-signing or update-channel compromise;
- dependency/supply-chain substitution;
- exported Android components exposing privileged behavior;
- unexpected collection/transmission of user data.

## Response expectations

Security reports are triaged by severity and reproducibility. A fix is not
considered complete until the relevant regression gate is added or updated and
a replacement artifact is rebuilt from the corrected source.

No exact response-time SLA is promised for this public QA project.

## Security architecture references

- `docs/SECURITY-PRIVACY.md`
- `docs/THREAT-MODEL-V0180.md`
- `docs/SUPPLY-CHAIN-V0180.md`
- `docs/QA-RELEASE.md`

## Secrets policy

Repository history, CI logs, screenshots, issue attachments and test fixtures
must never contain real API keys, passwords, authentication cookies, session
secrets or private signing material. If a secret is committed, deleting the
file is not sufficient: rotate/revoke the credential and treat Git history as
compromised.
