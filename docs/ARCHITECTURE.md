# InSave Architecture

## 1. Current Recovery architecture

The v0.17.x Recovery line is reconstructed from a pinned maintained Android downloader engine and then transformed with InSave-specific patches. This architecture exists to recover a known-good functional baseline quickly and reproducibly.

### Runtime stack

- Android/Kotlin application, minSdk 24, target/compile SDK 36.
- Local extraction runtime based on NewPipe/BotGuard and youtubedl-android/yt-dlp.
- Embedded Python, QuickJS, FFmpeg/FFprobe and aria2c runtime payloads.
- Room for persistent application/download data.
- WorkManager/background worker infrastructure.
- RecyclerView/Views plus existing Compose dependencies from upstream.

### Provider chain

`Download request -> provider policy -> A/NewPipe -> B/local yt-dlp -> C/optional self-hosted Cobalt`

Each provider must return one of a stable set of results rather than throw provider-specific exceptions directly into the UI:

- Success(media descriptor / download job)
- Unsupported
- Unavailable
- AuthenticationRequired
- TokenChallenge
- NetworkFailure
- RateLimited
- ExtractorFailure
- ConversionFailure
- StorageFailure
- Cancelled

Provider C is optional and must never be an undeclared public service dependency.

### Current weaknesses

The build relies on Python scripts that search and replace source text in the pinned engine. This creates anchor fragility, difficult code ownership, hard-to-review semantic changes and a high upgrade cost. Recovery scripts are therefore a migration bridge, not the intended permanent architecture.

## 2. Target scalable architecture

InSave should become an owned multi-module Android application. The upstream extraction project becomes an implementation dependency/reference rather than the source tree that defines the product.

### Suggested module graph

```text
:app
  -> :feature:home
  -> :feature:statuses
  -> :feature:downloads
  -> :feature:player
  -> :feature:followers
  -> :feature:settings

features
  -> :domain (only for reusable/complex use cases)
  -> :data:*
  -> :core:*

data
  -> :provider:*
  -> :runtime:*
  -> :core:*

providers
  -> :core:model
  -> :core:network
  -> :core:security

runtime
  -> native/runtime packaging only
```

### Core modules

`core:model` owns immutable cross-module models: MediaCandidate, DownloadRequest, DownloadJob, DownloadResult, StatusItem, ProviderFailure and user-visible error codes.

`core:ui` owns product theming, typography, spacing, components, loading/error/empty states and accessibility conventions.

`core:network` owns OkHttp configuration, TLS policy, domain validation, timeouts, retry primitives and redacted diagnostics.

`core:security` owns intent validation, sensitive-value redaction, runtime payload verification and secure preference helpers.

`core:storage` owns MediaStore/SAF/shared-storage abstractions so a Play flavor and a Recovery/sideload flavor can share the same product use cases.

`core:testing` owns fakes, fixtures, provider contract tests, status fixtures and device QA helpers.

### Feature modules

Each feature exposes a small API and contains its own screen state and navigation contract. Features must not know concrete extraction providers.

`feature:home` handles search/paste, search results, audio/video mode and batch selection.

`feature:statuses` handles source/filter/search/preview/save UX. It consumes a StatusRepository rather than direct filesystem APIs.

`feature:downloads` handles queue/history/retry/cancel state.

`feature:player` owns local audio/video playback.

`feature:settings` owns user preferences and advanced diagnostics.

## 3. Recommended layering

### UI layer

Use ViewModels with Unidirectional Data Flow. The UI renders immutable `UiState` and sends intents/actions. UI code should not implement extraction, storage or provider routing.

### Domain layer

Use only where logic is shared or complex. Candidate use cases:

- SearchMediaUseCase
- ResolveMediaUseCase
- QueueDownloadUseCase
- QueuePlaylistUseCase
- ScanStatusesUseCase
- SaveStatusUseCase
- RetryDownloadUseCase

### Data layer

Repositories are the only normal entry point to data sources. Suggested repositories:

- SearchRepository
- DownloadRepository
- StatusRepository
- LibraryRepository
- SettingsRepository
- DiagnosticsRepository

Room should be the source of truth for durable download state. Status media can use a short-lived scan cache as its source of truth because the underlying WhatsApp storage is external and ephemeral.

## 4. Provider architecture

Define a provider-neutral interface:

```kotlin
interface MediaProvider {
    val id: ProviderId
    suspend fun search(query: String, limit: Int): ProviderResult<List<MediaCandidate>>
    suspend fun resolve(request: ResolveRequest): ProviderResult<ResolvedMedia>
    suspend fun healthCheck(): ProviderHealth
}
```

A `ProviderRouter` owns ordering and fallback. It must not be implemented inside a Fragment/Activity.

Routing rules:

1. respect explicit feature capability;
2. use Provider A for the cheap/fast path when applicable;
3. fall through to Provider B after typed failure;
4. use Provider C only if configured and policy allows;
5. never retry indefinitely;
6. preserve one job per selected media item;
7. record redacted diagnostics for each attempt.

Add a lightweight circuit breaker so repeated failures of one provider do not add long delays to every job during a known outage.

## 5. Download job architecture

A DownloadJob should be immutable after queueing except for status/progress/error fields. Persist jobs before execution.

Recommended lifecycle:

`QUEUED -> RESOLVING -> DOWNLOADING -> POST_PROCESSING -> VERIFYING -> COMPLETED`

Terminal states:

`COMPLETED | FAILED | CANCELLED`

Retries create a new attempt record or increment a bounded attempt counter without changing the original media identity.

Use WorkManager unique work keyed by job UUID. Resume behavior must be idempotent: restarting the app cannot duplicate successful files or convert the same temporary file twice.

## 6. Playlist architecture

A playlist is a grouping construct, not a single download transaction. Persist:

- playlist/source ID;
- ordered candidate IDs;
- per-item selection;
- per-item job ID;
- aggregate progress calculated from jobs.

The UI can select all/invert/clear, but the queue receives independent immutable jobs. Cap batch size at the documented Recovery policy to protect memory/network/runtime behavior.

## 7. Status architecture

`StatusDataSource` implementations:

- `DirectStatusDataSource` for approved Recovery/sideload shared-storage access;
- `SafStatusDataSource` for user-selected trees;
- future `MediaStoreStatusDataSource` where viable.

`StatusRepository` merges/deduplicates sources and caches the last scan. Search/filter operations should run over the cached immutable list instead of rescanning the filesystem for each keystroke.

No UI class should own raw `/sdcard/...` paths.

## 8. Storage/distribution flavors

Recommended flavors:

- `recoverySideload`: COMPLETE functionality, broad automatic status access where explicitly enabled, Universal QA APK allowed.
- `productionSideload`: production signing, ABI-specific delivery, broad access only if product/privacy policy approves.
- `play`: privacy-minimized storage APIs and AAB distribution.

Feature capability is injected by flavor rather than scattered `Build.VERSION`/permission branches.

## 9. Security boundaries

Trust boundaries include:

- incoming ACTION_VIEW/deep-link/search intents;
- clipboard content;
- user-configurable URLs/endpoints;
- provider/network responses;
- downloaded runtime update payloads;
- filesystem names/paths;
- archive extraction;
- media metadata passed to FFmpeg.

Validate at each boundary, convert external values into typed internal models and never concatenate untrusted values into shell commands.

## 10. Migration plan from Recovery patches

1. Freeze the Recovery reconstruction scripts as the LKG reference.
2. Create an owned `insave-android` repository/fork at the exact known-good upstream commit.
3. Materialize Recovery patches as normal Kotlin/Gradle commits.
4. Add provider interfaces and characterization tests before refactoring behavior.
5. Split status, provider and runtime boundaries first; avoid a big-bang rewrite.
6. Move UI state into ViewModels/UDF while preserving screenshots and behavior.
7. Introduce modules incrementally when boundaries are stable.
8. Replace grep-based release checks with tests against public interfaces/artifact metadata.
9. Keep the old Recovery branch available until the new source produces byte/functionally equivalent accepted behavior.

This migration minimizes regression risk while giving InSave genuine ownership, scalability and reviewability.
