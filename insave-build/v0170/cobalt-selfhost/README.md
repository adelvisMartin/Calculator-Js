# InSave optional resolver API

This is **Provider C**, an emergency/self-hosted fallback. InSave must keep working locally through Provider A (NewPipe/PO-token) and Provider B (yt-dlp) when this server is absent.

Upstream: https://github.com/imputnet/cobalt

## Endpoints used by InSave

- `GET /` — health/version/services check.
- `POST /` — resolve a public media URL. InSave sends JSON with `downloadMode=audio`, `audioFormat=mp3`, `audioBitrate=320`, `youtubeBetterAudio=true` for the music fallback.
- Cobalt may return `redirect`, `tunnel`, `local-processing`, `picker` or `error`. InSave currently accepts direct/tunnel media and keeps final MP3 conversion local.

## Deployment

1. Copy `keys.example.json` to `keys.json`.
2. Generate a new UUIDv4 for the key. Never commit the real key.
3. Replace `API_URL` in `docker-compose.yml` with the public HTTPS endpoint served by your reverse proxy.
4. Start with `docker compose up -d`.
5. Store the endpoint and API key in InSave configuration/secure storage; never hard-code them in source.

Cobalt recommends self-hosting for reliable integrations. The public hosted API must not be treated as an InSave dependency.

## Security requirements

- HTTPS for internet-facing instances.
- `API_AUTH_REQUIRED=1`.
- API key stored outside Git/source control.
- Rate limit at the reverse proxy as a second layer.
- Do not log the Authorization header or signed media URLs.
- Rotate a key immediately if exposed.

## Why this is not the primary engine

A server introduces availability, bandwidth and privacy dependencies. The recovery contract therefore requires local Android E2E success first. Provider C exists to reduce outage risk when an upstream platform changes faster than an APK can be released.
