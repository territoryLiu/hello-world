# Web Access Research Contract

All online collection must run through `web-access`.

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

`Use web-access to collect travel evidence for this task.`

The run must keep `site_query`, preserve raw links, and record whether the site was reached successfully.
