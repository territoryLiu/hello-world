# Travel-Skill Research Enhancement Design

**Date:** 2026-04-15
**Status:** Draft for review
**Scope:** Phase 1 research-depth enhancement for `travel-skill`

## Goal

Strengthen `travel-skill` so that a domestic free-travel request produces a trustworthy, heavy-sampling research dossier before guide composition. Phase 1 focuses on wider source coverage, deeper evidence extraction, explicit failure accounting, reusable knowledge persistence, and a research-report HTML artifact.

## Problem Statement

The current `travel-skill` already has a usable skeleton for request normalization, research task generation, video research JSON, knowledge persistence, coverage validation, rendering, and verification. The weak point is not the existence of the pipeline, but the depth and reliability of the research chain:

- source coverage is not strict enough
- page body, comments, and video evidence are not consistently complete
- failures are not surfaced as first-class structured outputs
- destination knowledge is not thick enough for later reuse
- output HTML is still too close to a guide artifact and not strong enough as a research dossier

For Phase 1, the system should optimize for research completeness rather than final guide polish.

## Product Boundary

This phase remains inside `travel-skill`. It does not create a new generic research engine.

In scope:

- domestic city / scenic-spot free travel
- heavy sampling by default
- dual time layers:
  - recent status
  - last-year same-period experience
- source coverage across:
  - official sources
  - Xiaohongshu
  - Douyin
  - Bilibili
  - Dianping / Meituan
- page-first collection with video fallback where applicable
- reusable structured research storage
- research-report HTML as the primary rendered output

Out of scope for Phase 1:

- generalized non-travel research
- international travel and visa/FX flows
- advanced route recommendation intelligence
- major visual redesign of the final guide
- account systems or service deployment

## Success Criteria

Phase 1 is successful when a travel request can reliably produce a research dossier with all of the following properties:

1. Each required source has explicit `coverage_status`.
2. Heavy-sampling plans are generated per source instead of ad-hoc collection.
3. Xiaohongshu, Douyin, Bilibili, Dianping, and Meituan evidence is normalized into structured JSON.
4. Video-based sources can fall back to `yt-dlp + ffmpeg + whisper + image analysis` when page extraction is insufficient.
5. Recent and last-year same-period evidence are persisted separately.
6. Failures, missing fields, and retry paths are stored rather than hidden.
7. The primary HTML artifact is a research report that exposes coverage, evidence, gaps, and source traceability.

## User Decisions Captured

The following decisions were confirmed during brainstorming:

- prioritize improving research completeness before improving guide polish
- keep the work inside `travel-skill`, not a new general project
- default trip category is domestic city / scenic-spot free travel
- default sampling depth is heavy
- default time strategy is dual-layer:
  - latest status
  - last-year same-period
- conflicting recent vs historical evidence should be shown side by side
- default source failure policy is:
  - retry same mode
  - degrade or fallback where supported
  - record and continue
- primary first-phase output is a research dossier / research report, not a polished end-user guide

## Recommended Approach

Use a research-pipeline enhancement strategy rather than a full rewrite.

Why this approach:

- `travel-skill` already has reusable scripts and output paths
- the current bottleneck is evidence quality, not the absence of a pipeline
- enhancing the research middle layer preserves existing guide-generation assets
- it allows later guide-quality improvements without discarding the Phase 1 work

Alternatives considered:

1. Spec-only tightening
   - Low risk, but insufficient improvement in real evidence coverage
2. Full research-core rebuild
   - High ceiling, but too expensive and too disruptive for Phase 1

## Architecture

Phase 1 keeps the existing `travel-skill` flow and strengthens the research middle layer with seven stages:

1. `request-normalize`
2. `research-plan`
3. `source-collection`
4. `fallback-and-retry`
5. `normalize-and-evidence-pack`
6. `knowledge-merge`
7. `research-report-render`

The high-level intent is:

- normalize the travel request into structured research inputs
- create a heavy-sampling plan per platform and time layer
- collect per-source evidence with source-specific strategies
- retry and degrade before marking a source as failed
- normalize all evidence into a common schema
- merge evidence into reusable destination knowledge by topic
- render a research dossier that surfaces quality and gaps

## Research Flow

### 1. Request Normalize

Normalize the request into stable fields such as:

- departure city
- destinations
- date range
- traveler profile
- budget
- trip focus
- whether dual time-layer research is required

This prevents downstream collection code from depending on free-form text.

### 2. Research Plan

Generate a heavy-sampling plan that specifies:

- official-source tasks by topic
- Xiaohongshu search buckets and target sample counts
- Douyin / Bilibili video buckets and target sample counts
- Dianping / Meituan area and category buckets
- which topics require recent evidence
- which topics also require last-year same-period evidence

### 3. Source Collection

Collect each platform independently with dedicated logic:

- official sources: opening rules, ticketing, weather, transport, notices
- Xiaohongshu: post body, comments, image candidates, time-layer tags
- Douyin / Bilibili: page extraction first, video fallback if evidence is insufficient
- Dianping / Meituan: store metadata, near-term reviews, queue patterns, pitfalls

### 4. Fallback and Retry

Use a uniform three-step policy:

1. retry in the same mode using different extraction tactics
2. degrade or fall back where supported
3. record failure and continue with the remaining sources

### 5. Normalize and Evidence Pack

Normalize all collected data into a common schema with source type, collection mode, coverage, missing fields, and time layer.

### 6. Knowledge Merge

Merge source evidence into reusable destination knowledge files grouped by topic.

### 7. Research Report Render

Render a research-report HTML that exposes source coverage, evidence quality, dual-time-layer findings, and gaps.

## Required Source Coverage

The first phase requires coverage across the following source groups.

### Official Sources

Required topics:

- weather:
  - recent weather
  - last-year same-period climate reference
  - `checked_at`
- scenic spots:
  - opening status
  - operating hours
  - price
  - reservation rule
  - official notice link
- transport:
  - rail / flight path options
  - duration
  - price range
  - latest searchable date
- notices:
  - closures
  - limits
  - construction
  - special night events / performances if relevant

### Xiaohongshu

Heavy-sampling requirements:

- target sample: `20+` posts
- each post should capture:
  - title
  - body
  - author
  - publish time
  - engagement level
  - source URL
- comment layer is mandatory
- comments should be summarized into fixed themes:
  - queueing
  - transport
  - clothing
  - photo spots
  - pitfalls
- extract image candidates
- assign `recent` or `last_year_same_period`

### Douyin / Bilibili

Heavy-sampling requirements per platform:

- target sample: `10+` videos
- page layer:
  - title
  - intro / page text
  - author
  - publish time
  - source URL
  - comment summary
  - cover
- transcript layer:
  - timestamped `transcript_segments`
- visual layer:
  - `8-12` keyframe candidates
  - visual descriptions
- structure layer:
  - timeline segmentation
  - topic tagging
  - time-layer tagging
- spoken content and visual content must remain separate

### Dianping / Meituan

Heavy-sampling requirements per platform:

- target sample: `15+` venues or candidates
- venue layer:
  - store name
  - address
  - per-capita range
  - recommended dishes
  - operating status
- review layer:
  - near-term review summary
  - queueing pattern
  - environment / service / taste themes
- risk layer:
  - pitfalls
  - suitable crowd / scenario
- time-layer tagging

## Coverage Status Model

All source groups must use hard coverage states:

- `complete`
- `partial`
- `failed`

The status must be derived from explicit rules rather than subjective summary text.

### Coverage Rules

Official sources:

- `complete` when relevant required fields reach 80%+
- `partial` when some pages are present but key time-sensitive fields are missing
- `failed` when authoritative sources are not obtained

Xiaohongshu:

- `complete` when sample target is met, 70%+ of posts have body plus comment summary, and theme grouping is present
- `partial` when body exists but comments or time-layering are weak
- `failed` when stable extraction is not achieved

Douyin / Bilibili:

- `complete` when sample target is met, 70%+ have page info, 50%+ have transcript or reliable subtitles, and 50%+ have keyframes plus visual summaries
- `partial` when only page-level evidence exists
- `failed` when page evidence is weak and video fallback does not produce usable assets

Dianping / Meituan:

- `complete` when sample target is met, 70%+ of venues have base fields, and 50%+ have near-term review and queue summaries
- `partial` when venue basics exist without enough review evidence
- `failed` when extraction cannot reliably access the necessary fields

## Failure Accounting

Failures must never be hidden in prose only. Each failed or partial source should include:

- `coverage_status`
- `failure_reason`
- `failure_detail`
- `missing_fields`
- `attempt_log`

Recommended `failure_reason` enum:

- `login_required`
- `anti_bot_blocked`
- `page_unreachable`
- `content_removed`
- `comment_not_loaded`
- `insufficient_sample_size`
- `video_download_failed`
- `audio_transcription_failed`
- `keyframe_extraction_failed`
- `schema_validation_failed`
- `time_layer_not_determined`

## Data Model

All normalized outputs should converge on a common structure with fields such as:

- `source_type`
- `collector_mode`
- `coverage_status`
- `failure_reason`
- `failure_detail`
- `checked_at`
- `time_layer`
- `evidence_refs`
- `knowledge_points`
- `missing_fields`

Video-origin records additionally require:

- `transcript_segments`
- `visual_segments`
- `media_artifacts`

The research dossier must be able to trace major claims back to source evidence.

## Storage Layout

The design keeps using `travel-data/` and thickens the research layer:

```text
travel-data/
  places/<place-slug>/
    raw/
      official/
      xiaohongshu/
      douyin/
      bilibili/
      dianping/
      meituan/
    normalized/
      official.json
      xiaohongshu.json
      douyin.json
      bilibili.json
      dianping.json
      meituan.json
    knowledge/
      recent.json
      last-year-same-period.json
      merged-topics.json
    media/
      page-images/
      video-covers/
      video-keyframes/
      audio/
      transcripts/
    coverage/
      site-coverage.json
      failure-log.json
  trips/<trip-slug>/
    request/
    plan/
    snapshots/
    notes/
  guides/<trip-slug>/
    research-report.html
    recommended.html
    share.html
```

Key storage rules:

- raw and summarized data must remain separate
- recent and last-year layers must be stored separately
- page images, video covers, and keyframes must not be mixed together without type labels

## HTML Research Report

The first-phase HTML artifact should be a research dossier, not a final consumer guide.

Recommended section order:

1. report header
2. coverage overview
3. quick findings
4. themed research blocks
5. evidence cards
6. media section
7. gaps and failures
8. source appendix

### Themed Research Blocks

Use fixed topic groups:

- seasonal scenery
- clothing and weather feel
- opening / reservation rules
- transport and transfers
- queues and crowd pattern
- photo spots and time windows
- dining and business areas
- pitfalls and common mistakes

Each topic should show:

- latest status
- last-year same-period experience
- conflicts between them
- confidence / evidence density hints

### Evidence Cards

Use one shared evidence-card abstraction across platforms.

Common fields:

- title
- source platform
- time layer
- author / publisher
- publish time
- 1-3 key takeaways
- evidence summary
- media thumbnail if available
- source link
- credibility hint
- gap flag if incomplete

Platform-specific extensions:

- Xiaohongshu:
  - high-frequency comments
  - correction / supplement / pitfall summary
- video:
  - transcript summary
  - timeline snippet
  - keyframe count
  - whether fallback was triggered
- Dianping / Meituan:
  - store name
  - per-capita range
  - queue impression
  - recommended dishes
- official:
  - institution
  - notice type
  - effective date

## Validation Strategy

Phase 1 must verify research quality, not just file existence.

### 1. Structure Validation

Check presence of:

- platform-level normalized JSON
- `site-coverage.json`
- `failure-log.json`
- `merged-topics.json`
- `research-report.html`

### 2. Field Validation

Check required fields such as:

- `coverage_status`
- `checked_at`
- `time_layer`
- `knowledge_points`
- `missing_fields`
- for video records:
  - `transcript_segments`
  - `visual_segments`

### 3. Sample Validation

Check heavy-sampling targets:

- Xiaohongshu `20+`
- Douyin `10+`
- Bilibili `10+`
- Dianping `15+`
- Meituan `15+`

When targets are missed, the source must degrade to `partial` or `failed`.

### 4. Render Validation

Check the HTML renders the required dossier sections:

- coverage overview
- dual time-layer comparison
- gaps and failures
- evidence cards
- source appendix

## Implementation Priorities

Recommended sequence:

1. define schema and coverage rules
2. upgrade research-plan generation for heavy sampling and dual time layers
3. strengthen collection and video fallback
4. persist merged knowledge
5. render research-report HTML
6. tighten validation

Recommended script focus based on the current skill layout:

- `scripts/build_web_research_runs.py`
- `scripts/build_video_research_json.py`
- `scripts/extract_video_assets.py`
- `scripts/extract_structured_facts.py`
- `scripts/persist_research_knowledge.py`
- `scripts/validate_site_coverage.py`
- `scripts/render_trip_site.py`
- `scripts/verify_trip.py`

## Risks and Constraints

- Xiaohongshu, Douyin, Dianping, and Meituan are anti-bot-sensitive and may require login-state-dependent browser access
- the video fallback chain depends on local availability of `yt-dlp`, `ffmpeg`, and a transcription stack
- heavy sampling increases runtime and collection cost
- last-year same-period evidence may often remain weaker than recent evidence
- Phase 1 improves dossier trustworthiness first; it does not fully solve route intelligence

## Open Technical Follow-Ons

These are expected future improvements, not blockers for Phase 1:

- stronger route recommendation based on research evidence
- more polished final guide rendering
- richer media ranking for report display
- broader trip classes beyond domestic free travel

## Environment Notes

- Current workspace is not a Git repository, so this spec cannot be committed here unless moved into a repo first.
- The user indicated `C:\Users\Lenovo\.conda\envs\stock-analyzer` can be used for Python execution.
- Earlier local checks showed that `yt-dlp`, `whisper`, and `ffmpeg` are not yet available in the current environment/PATH and will need setup during implementation.
