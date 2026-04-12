# Travel Skill Sample Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `travel-skill` to support latest-searchable-date rail fallback, explicit social-comment capture, reusable place knowledge storage, and five-style output variants aligned with the sample guide density.

**Architecture:** Keep the current intake -> research -> compose -> render pipeline, but widen the data contract at the research layer and widen the output matrix at the render layer. Add one persistence script for reusable place knowledge and update tests first so the new behavior is locked down before implementation.

**Tech Stack:** Python scripts, unittest, HTML template rendering, JSON research artifacts

---

### Task 1: Research Contract Tests

**Files:**
- Modify: `tests/travel_skill/test_intake_research.py`
- Modify: `.codex/skills/travel-skill/scripts/build_research_tasks.py`
- Modify: `.codex/skills/travel-skill/scripts/build_web_research_runs.py`

- [ ] Add failing tests for comment capture fields, latest-searchable-date fallback fields, and absolute sample path handling.
- [ ] Run `python -m unittest discover -s tests/travel_skill -p test_intake_research.py -v` and verify failures are for missing fields or prompt content.
- [ ] Implement minimal research-task and research-run changes.
- [ ] Re-run the same test target until green.

### Task 2: Reusable Knowledge Persistence

**Files:**
- Create: `.codex/skills/travel-skill/scripts/persist_research_knowledge.py`
- Modify: `tests/travel_skill/test_intake_research.py`

- [ ] Add failing tests for writing trip research into `travel-data/places/<place-slug>/`.
- [ ] Run the targeted intake/research tests and verify the persistence test fails first.
- [ ] Implement the persistence script with JSON splitting by place and stable output filenames.
- [ ] Re-run the targeted tests until green.

### Task 3: Guide Density and Transport Fallback

**Files:**
- Modify: `.codex/skills/travel-skill/scripts/build_guide_model.py`
- Modify: `tests/travel_skill/test_compose.py`
- Modify: `tests/fixtures/travel_skill/approved_research.json` if needed

- [ ] Add failing tests for latest-searchable rail copy, denser route cards, grouped food/transport output, and sample reference pass-through.
- [ ] Run `python -m unittest discover -s tests/travel_skill -p test_compose.py -v` and verify failures.
- [ ] Implement the minimal compose changes to honor fallback schedule context and richer content sections.
- [ ] Re-run compose tests until green.

### Task 4: Multi-Style Render Matrix

**Files:**
- Modify: `.codex/skills/travel-skill/scripts/render_trip_site.py`
- Modify: `.codex/skills/travel-skill/scripts/build_portal.py`
- Modify: `.codex/skills/travel-skill/scripts/export_single_html.py`
- Modify: `.codex/skills/travel-skill/scripts/package_trip.py`
- Modify: `tests/travel_skill/test_render_package.py`

- [ ] Add failing render/package tests asserting all five styles are emitted and portal groups links by style.
- [ ] Run `python -m unittest discover -s tests/travel_skill -p test_render_package.py -v` and verify failures.
- [ ] Implement multi-style rendering, style-aware export, and package updates.
- [ ] Re-run render/package tests until green.

### Task 5: Final Verification

**Files:**
- Modify: `.codex/skills/travel-skill/SKILL.md`
- Modify: related scripts/tests touched above

- [ ] Update `SKILL.md` so the documented contract matches the new behavior.
- [ ] Run `python -m unittest discover -s tests/travel_skill -p test_*.py -v`.
- [ ] Review outputs for any encoding or path regressions.
- [ ] Summarize changed behavior, remaining gaps, and verification evidence.
