## Summary

Describe the problem and the smallest coherent change that solves it.

## Scope

- [ ] Product/UI
- [ ] Provider/runtime
- [ ] WhatsApp statuses
- [ ] Security/privacy
- [ ] Build/CI
- [ ] Documentation/legal
- [ ] Refactor only

## Evidence

- [ ] Relevant unit tests pass
- [ ] Affected build variant compiles
- [ ] Security/static gates pass when applicable
- [ ] Android functional/E2E evidence attached when behavior changed
- [ ] No real credentials/cookies/tokens/private data included
- [ ] APK/checksum regenerated if source changed after a candidate build

## Compatibility

What existing InSave behavior could this change affect? Include rollback/migration notes if relevant.

## Licensing / third-party

- [ ] No new dependency/runtime was added
- [ ] OR new dependency/runtime license and provenance were documented
- [ ] InSave brand assets were not replaced/reused in a way that changes the official branding policy

## Release label

Do not call the change Stable/Production-ready unless the corresponding release gates in `docs/QA-RELEASE.md` are complete.
