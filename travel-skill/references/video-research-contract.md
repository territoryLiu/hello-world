# Video Research Contract

- Primary output is structured JSON.
- `collector_mode` must be one of `page-only`, `page+video`, `video-fallback`.
- `coverage_status` must be one of `complete`, `partial`, `failed`.
- `failure_reason` is required whenever status is not `complete`.
- `transcript_segments` require timestamps.
- `visual_segments` must stay separate from transcript text.
- `media_artifacts` must list the actual downloaded or derived files.
