# Web Access Research Contract

All online collection must run through travel-skill built-in online research.

## Required task fields

- `site_query`
- `collection_method`
- `must_capture_fields`
- `evidence_level`

## Required persisted fields

- raw url
- site
- checked_at
- collection_method
- page title
- summary
- comment_highlights
- transcript
- timeline
- shot_candidates
- facts

## Research run prompt shape

Start each concrete site task with:

`Use travel-skill built-in online research to collect travel evidence for this task.`

The run must keep `site_query`, preserve raw links, and record `coverage_status` plus `failure_reason` whenever collection is incomplete.
