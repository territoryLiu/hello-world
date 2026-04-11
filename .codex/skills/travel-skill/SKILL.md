---
name: travel-skill
description: Create travel guides with staged intake, web research, review packets, guide composition, single-file HTML export, ZIP packaging, and verification.
---

# Travel Skill

Run this workflow:
1. `intake`
2. `research-plan`
3. `research-run`
4. `review-gate`
5. `compose`
6. `render`
7. `package-share`
8. `verify`

Always use `web-access` for online collection, use `frontend-design` when rendering the final guide UI, and use `playwright-skill` or the repo render checker before claiming completion.

Default share target is a single-file HTML plus a ZIP bundle.

Python execution policy:
- Prefer an existing conda environment when available.
- Current preferred environment: `py313`.
- Browser verification environment: `paper2any` when Playwright is needed.
- If a dependency is missing, install it with the Tsinghua mirror: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <package>`.
