---
name: travel-skill
description: Use when producing a shareable travel guide that needs intake, multi-source web research, human review, layered guide composition, desktop/mobile rendering, single-file export, ZIP packaging, and final verification.
---

# Travel Skill

## Purpose

Turn one trip request into a reusable travel research run plus shareable guide deliverables.

Default outputs:
- gate report for blocked vs ready intake
- desktop guide
- mobile guide
- `portal.html`
- `recommended.html`
- `share.html`
- ZIP package
- verification report

Default share format is `single-file HTML` plus ZIP packaging.

## Canonical References

- Schema: `references/content-schema.md`
- Sharing modes: `references/sharing-modes.md`
- Research contract: `references/web-access-research-contract.md`
- Source priority: `references/source-priority.md`
- Review checklist: `references/research-checklists.md`

## Output Layout

- Reusable destination knowledge is written under `travel-data/places/`.
- Reusable city-to-city transport is written under `travel-data/corridors/`.
- Trip-scoped request, planning, and snapshots are written under `travel-data/trips/<trip-slug>/`.
- Final guide artifacts are written under `travel-data/guides/<trip-slug>/`.
- Video parsing is required for publishable video media. If keyframes or clickable source links are missing, the media is downgraded to `text citation only`.

## Required Skill Coordination

- Use `web-access` for all online collection.
- Use `frontend-design` when shaping the final reading experience.
- Use `ui-ux-pro-max` when finalizing mobile or desktop reading structure and readability.
- Use `theme-factory` when a themed visual variant is requested.
- Use `playwright-skill` or the repo render checker before claiming completion.
- Use `verification-before-completion` before claiming the guide is complete.

## Execution Order

1. `intake-gate`
2. `research-plan`
3. `research-run`
4. `review-gate`
5. `planning`
6. `localize`
7. `compose`
8. `render`
9. `package-share`
10. `verify`

## Intake Gate Rules

- Run a request gate before any research work.
- Missing `title`, `departure_city`, `destinations`, `date_range`, `travelers`, or `budget` must block the trip.
- Blocked requests must emit follow-up questions instead of entering research or render steps.
- `sample_reference` can exist for internal review but must not leak into published guide metadata.

## Guide Contract

The guide model has three layers:
- `daily-overview`
- `recommended`
- `comprehensive`

Section order for `recommended` and `comprehensive`:
1. `recommended_route`
2. `route_options`
3. `clothing_guide`
4. `attractions`
5. `transport_details`
6. `food_by_city`
7. `tips`
8. `sources`

Section order for `daily-overview`:
1. `days`
2. `wearing`
3. `transport`
4. `alerts`
5. `sources`

## Research Rules

- Prefer official and platform-first sources for transport, weather, tickets, reservation rules, opening status, and notices.
- Use social and local-life platforms to enrich experience details, food choices, queue patterns, photo spots, and practical tips.
- `research-run` must use `web-access` with concrete site coverage, not abstract `social` only.
- Required social and local-life sites include `xiaohongshu`, `douyin`, `bilibili`, `meituan`, and `dianping` when the topic matrix calls for them.
- For `xiaohongshu`, `douyin`, and `bilibili`, capture page body plus comment highlights, comment status, and sample size.
- For `douyin` and `bilibili`, also capture transcript, timeline, and screenshot candidates when the page is video-based.
- If a required field cannot be collected, mark it as failed and record the failure reason instead of pretending the site was covered.
- Keep `checked_at` on time-sensitive facts.
- Store research in reusable JSON so later trips can extend the same destination knowledge base.
- Persist reusable place knowledge under `travel-data/places/<place-slug>/` with raw web research, structured facts, media raw, and site coverage files.

## Transport Defaults

- Always include a high-speed-rail-first route when feasible.
- For trips over `1000km`, also provide `flight + rail` and `pure rail` options.
- When direct transport is weak, add a transfer-city option and note whether half-day or one-day stopover play is suitable.
- When future schedules are not yet on sale, use the nearest searchable schedule, keep the checked date, and give price ranges.
- When future rail tickets are not yet on sale, explicitly show the latest searchable date, example train numbers, checked date context, and a reminder to re-check once formal sale opens.

## Planning Rules

- Planning is day-by-day first, not transport-card first.
- `route_main.days` and every `route_options[].days` must be independently authored, not shallow copies.
- `recommended.route_options` in the published guide should prefer planning output and only fall back to transport-derived cards when planning is absent.
- Add a localization pass before compose so guide正文优先使用 `text_zh`.

## Rendering Rules

- Desktop and mobile must contain the same facts.
- Mobile can paginate for readability.
- Publish exactly five guide templates: `route-first`, `decision-first`, `destination-first`, `transport-first`, `lifestyle-first`.
- Default render behavior must emit all five templates for both desktop and mobile.
- Single-file sharing is the default share target.
- ZIP is the default archive target.
- Never render sample-reference chips, search-query traces, or `text-citation-only` fake media blocks into publish pages.

## Verification Rules

- Verification must check both desktop and mobile template completeness.
- Verification must confirm `notes/sources.md` and `notes/sources.html` are present.
- Browser-aware verification should exist even when unit-test mode downgrades it to `warn`.
- Do not claim completion until render, package, and verify outputs are freshly checked.

## Python Execution Policy

- Prefer an existing conda environment when available.
- Current preferred environment: `py313`.
- Browser verification environment: `travel` when Playwright is needed.
- If a dependency is missing, install it with the Tsinghua mirror:
  - `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <package>`
