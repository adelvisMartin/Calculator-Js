# Legal and Distribution Model

> This document is an engineering/compliance guide, not legal advice. For a commercial launch, trademark registration, paid licensing program or jurisdiction-specific enforcement, obtain advice from qualified counsel.

## 1. Why InSave cannot simply use a “no one may use this code” license

The current Recovery/Heavy Android application is reconstructed over YTDLnis, whose pinned upstream revision is distributed under GNU GPL v3.0. The InSave overlay modifies and combines with that GPL-covered Android work.

Because of that inheritance, the project should not place a proprietary “no copying / no modification / non-commercial only” restriction over the GPL-covered combined software. Doing so would conflict with the rights already granted by the upstream license.

For the software, the correct protection strategy is therefore **copyleft compliance**, not pretending the code is proprietary:

- redistributed GPL-covered modifications must preserve the applicable license;
- corresponding source obligations remain applicable when object code is conveyed;
- copyright and modification notices must be preserved;
- a third party cannot take the GPL-covered combined work and lawfully make it closed-source merely by changing the package name.

## 2. What can still be protected strongly

GPL software rights do not automatically grant trademark rights. InSave can separately protect the parts that identify the official product:

- the **InSave** product name as a source identifier;
- the official InSave logo and launcher icon;
- original brand artwork and trade dress;
- statements that a build is “official”, “certified”, “supported” or “released by InSave”.

That boundary is documented in `TRADEMARKS.md` and `BRAND-ASSETS-LICENSE.md`.

Practical result: someone may exercise GPL rights in the software, but a redistributed modified fork should **rename and rebrand** itself rather than impersonating the official InSave application.

## 3. License map

| Material | Policy |
| --- | --- |
| GPL-covered Android source/overlays forming the combined work | GPL-3.0-only, subject to upstream/third-party notices |
| Pinned YTDLnis upstream | GPL-3.0 at the pinned upstream revision |
| InSave name/logo/launcher/original brand art | Reserved brand/trademark rights; see brand policy |
| Third-party runtimes and dependencies | Their original licenses; see `THIRD_PARTY_NOTICES.md` and SBOM |
| External service names/logos | Property of their respective owners; factual references only |

If a specific file contains an explicit third-party notice, that notice takes priority for that file/component.

## 4. Official vs unofficial builds

An **official InSave build** should be tied to all of the following:

1. a documented source commit;
2. a documented version code/name;
3. reproducible CI/build evidence;
4. a published SHA-256 digest;
5. an official signing key once production signing is enabled;
6. the official InSave brand assets;
7. release notes and a known distribution channel.

A third-party build that changes source, signing, package identity, runtime payload or behavior must not be presented as an official InSave release.

## 5. Public repository does not mean public secrets

The repository may be public, but the following must never be committed:

- production/private signing keys or keystores;
- passwords;
- API secrets;
- real authentication cookies;
- session/visitor/PO tokens captured from users;
- private user files;
- paid-service credentials;
- internal service credentials or database connection strings.

Use CI secret stores and environment-backed configuration for any future secret material.

## 6. Third-party compliance

Before distributing a Heavy APK, review the exact packaged forms of:

- YTDLnis-derived Android code;
- yt-dlp;
- aria2;
- QuickJS;
- FFmpeg;
- Android/JVM dependencies from Gradle/Maven;
- any future Cobalt/self-hosted integration or other runtime.

Do not infer the license of a compiled binary solely from a project homepage. For example, FFmpeg licensing depends on the build configuration and optional external libraries.

The generated SBOM is the starting point for the release inventory, not the final legal review by itself.

## 7. GPL corresponding-source release rule

If the project conveys an APK containing GPL-covered object code, the release process must ensure the applicable corresponding source is available in a GPL-compliant way. The safest project practice is:

- tag the exact source/overlay commit used for the APK;
- keep the reconstruction scripts needed to reproduce the covered work;
- retain the pinned upstream revision;
- publish the source location next to the APK/release notes;
- keep required license and copyright notices accessible.

## 8. Brand enforcement rule for forks

A redistributed fork should:

- use a different app name;
- replace the InSave launcher icon/logo;
- clearly identify itself as unofficial;
- use a different package/application identifier where practical;
- retain GPL/third-party legal notices;
- avoid confusing users into believing it is maintained or signed by InSave.

This is the principal mechanism for protecting official identity while respecting GPL software rights.

## 9. Commercial options later

If InSave later needs a commercial/proprietary licensing model for new code, the architecture and copyright provenance must be reviewed first. A proprietary relicense of a GPL-derived combined work is not something the project owner can unilaterally perform unless the necessary rights from all relevant copyright holders are available.

A future commercial strategy can instead focus on legally separable assets/services such as:

- official branding/trademark licenses;
- hosted infrastructure or support services;
- separately authored backend/control-plane software that does not become a GPL derivative;
- premium operational services;
- separately licensed original modules where copyright ownership and dependency boundaries genuinely permit it.

Do not advertise proprietary relicensing until that provenance review is complete.

## 10. Release legal checklist

Before an official public release:

- [ ] exact source commit/tag recorded;
- [ ] GPL notice and source availability documented;
- [ ] SBOM generated from the candidate;
- [ ] third-party license inventory reviewed;
- [ ] FFmpeg packaged-binary licensing reviewed;
- [ ] official signing identity documented;
- [ ] SHA-256 published;
- [ ] brand assets match the official release;
- [ ] privacy/permissions reviewed for the distribution channel;
- [ ] release notes distinguish QA / Stable / Production-ready correctly;
- [ ] no secrets or sensitive logs in release artifacts.
