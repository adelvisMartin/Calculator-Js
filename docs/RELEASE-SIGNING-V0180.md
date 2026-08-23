# InSave v0.18 Release Signing

## Problem corrected
The inherited upstream build used a signing configuration named `debug` for the release build. That is acceptable for upstream development convenience but not for an InSave production artifact.

v0.18 removes the release reference to `signingConfigs.debug`.

## Production signing inputs
The release configuration can consume these protected environment variables:
- `INSAVE_KEYSTORE_PATH`;
- `INSAVE_KEYSTORE_PASSWORD`;
- `INSAVE_KEY_ALIAS`;
- `INSAVE_KEY_PASSWORD`.

The dedicated `insaveRelease` signing configuration is created only when all four values are present.

## Rules
1. Never create a “production” key just to make CI green.
2. Never commit `.jks`, `.keystore`, password or private-key content.
3. QA artifacts must be labelled QA when they use debug signing or remain unsigned release builds.
4. The final production pipeline should obtain secrets from the repository/environment secret store and restrict access to protected release workflow/environment.
5. For Play distribution, use the proper upload key/Play App Signing process when the application is enrolled.
6. Record certificate fingerprint for the production release process after a real key exists; do not invent a fingerprint in documentation.

## Current automation proof
The static security gate checks that:
- the release block contains no `signingConfigs.debug`;
- external signing variables exist;
- the dedicated release signing config exists.

This verifies the **architecture of signing**, not possession of a production private key.

## Production artifact gate
A production-distributable artifact remains blocked until actual protected signing credentials are supplied. This external credential dependency is not considered an application-code failure and must not be “solved” by committing a new private key.
