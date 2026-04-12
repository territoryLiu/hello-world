---
name: travel-skill
description: Use when producing a shareable travel guide that needs intake, multi-source web research, human review, layered guide composition, desktop/mobile rendering, single-file export, ZIP packaging, and final verification.
---

# Travel Skill

## Purpose

Turn one trip request into a reusable travel research run plus shareable guide deliverables.

Default outputs:
- desktop guide
- mobile guide
- `portal.html`
- `recommended.html`
- `share.html`
- ZIP package
- verification report

Default share format is `single-file HTML` plus ZIP packaging.

## Required Skill Coordination

- Use `web-access` for all online collection.
- Use `frontend-design` when shaping the final reading experience.
- Use `ui-ux-pro-max` when finalizing mobile or desktop reading structure and readability.
- Use `theme-factory` when a themed visual variant is requested.
- Use `playwright-skill` or the repo render checker before claiming completion.
- Use `verification-before-completion` before claiming the guide is complete.

## Execution Order

1. `intake`
2. `research-plan`
3. `research-run`
4. `review-gate`
5. `compose`
6. `render`
7. `package-share`
8. `verify`

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
- For trips over `600km`, also provide `flight + rail` and `pure rail` options.
- When direct transport is weak, add a transfer-city option and note whether half-day or one-day stopover play is suitable.
- When future schedules are not yet on sale, use the nearest searchable schedule, keep the checked date, and give price ranges.
- When future rail tickets are not yet on sale, explicitly show the latest searchable date, example train numbers, checked date context, and a reminder to re-check once formal sale opens.

## Rendering Rules

- Desktop and mobile must contain the same facts.
- Mobile can paginate for readability.
- Generate all five style variants when requested: `classic`, `minimalist`, `original`, `vintage`, `zen`.
- Single-file sharing is the default share target.
- ZIP is the default archive target.

## Python Execution Policy

- Prefer an existing conda environment when available.
- Current preferred environment: `py313`.
- Browser verification environment: `paper2any` when Playwright is needed.
- If a dependency is missing, install it with the Tsinghua mirror:
  - `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <package>`
