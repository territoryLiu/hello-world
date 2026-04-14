# Travel Skill Editorial HTML Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `travel-skill` independently define a high-end travel editorial HTML design baseline without requiring explicit `frontend-design`, while preserving the existing travel guide content order.

**Architecture:** This change is documentation-first. Rewrite `.codex/skills/travel-skill/SKILL.md` so the skill itself owns HTML design guidance, add three focused design reference documents under the skill's `references/` directory, and downgrade the existing fixed multi-template approach from default behavior to deprecated legacy assets. Do not touch render scripts or HTML templates in this plan.

**Tech Stack:** Markdown, PowerShell, git, ripgrep

---

### Task 1: Rewrite `travel-skill` core contract

**Files:**
- Modify: `.codex/skills/travel-skill/SKILL.md`
- Test: `.codex/skills/travel-skill/SKILL.md`

- [ ] **Step 1: Back up the current skill text for diff review**

Run:

```powershell
Get-Content '.codex\skills\travel-skill\SKILL.md' -Encoding UTF8
```

Expected: current `Required Skill Coordination`, `Rendering Rules`, and `Default outputs` sections still reflect the old external-design and five-template behavior.

- [ ] **Step 2: Rewrite the default outputs and coordination sections**

Apply a patch that updates `.codex/skills/travel-skill/SKILL.md` so it removes the explicit `frontend-design` dependency and replaces it with internal design ownership. The edited content should include text equivalent to:

```md
Default outputs:
- gate report for blocked vs ready intake
- desktop guide
- mobile guide
- `portal.html`
- `recommended.html`
- `share.html`
- ZIP package
- verification report

Default reading experience is a single editorial-style HTML guide family with desktop and mobile variants.
```

And:

```md
## Required Skill Coordination

- Use built-in online research for all online collection.
- `travel-skill` itself owns the final HTML reading experience and must apply its editorial design baseline during render decisions.
- Use `ui-ux-pro-max` only when refining structure or readability beyond the baseline.
- Use `theme-factory` when a themed visual variant is explicitly requested.
- Use `playwright-skill` or the repo render checker before claiming completion.
- Use `verification-before-completion` before claiming the guide is complete.
```

- [ ] **Step 3: Rewrite rendering and verification rules**

Apply a patch that replaces the existing five-template render requirement with the new default. The edited section should include text equivalent to:

```md
## Rendering Rules

- Desktop and mobile must contain the same facts.
- Mobile can paginate for readability.
- Default HTML output must follow the skill's editorial design baseline.
- The published guide must preserve the section order defined in `Guide Contract`.
- Existing fixed multi-template assets are legacy artifacts and are not the default publication target.
- Single-file sharing is the default share target.
- ZIP is the default archive target.
- Never render sample-reference chips, search-query traces, or `text-citation-only` fake media blocks into publish pages.
```

And the verification section should include:

```md
- Verification must check both desktop and mobile guide completeness.
- Verification must confirm `notes/sources.md` and `notes/sources.html` are present.
- Verification must confirm the rendered guide preserves section order and does not regress into a legacy template-card layout.
- Browser-aware verification should exist even when unit-test mode downgrades it to `warn`.
- Do not claim completion until render, package, and verify outputs are freshly checked.
```

- [ ] **Step 4: Add editorial baseline references to canonical references**

Apply a patch so `## Canonical References` includes the new reference files:

```md
- HTML design baseline: `references/html-design-baseline.md`
- HTML visual rules: `references/html-visual-rules.md`
- HTML anti-patterns: `references/html-anti-patterns.md`
```

- [ ] **Step 5: Run targeted verification on the rewritten skill**

Run:

```powershell
rg -n "frontend-design|Publish exactly five guide templates|Default render behavior must emit all five templates" '.codex\skills\travel-skill\SKILL.md'
```

Expected: no matches.

Then run:

```powershell
rg -n "editorial|legacy artifacts|section order defined in `Guide Contract`" '.codex\skills\travel-skill\SKILL.md'
```

Expected: matches confirming the new baseline and legacy-template downgrade language exist.

- [ ] **Step 6: Commit**

Run:

```powershell
git add -- '.codex/skills/travel-skill/SKILL.md'
git commit -m "docs: 重写 travel-skill 的杂志式 HTML 基线"
```

Expected: one commit recording the main skill contract rewrite.

### Task 2: Add editorial HTML reference documents

**Files:**
- Create: `.codex/skills/travel-skill/references/html-design-baseline.md`
- Create: `.codex/skills/travel-skill/references/html-visual-rules.md`
- Create: `.codex/skills/travel-skill/references/html-anti-patterns.md`
- Test: `.codex/skills/travel-skill/references/html-design-baseline.md`
- Test: `.codex/skills/travel-skill/references/html-visual-rules.md`
- Test: `.codex/skills/travel-skill/references/html-anti-patterns.md`

- [ ] **Step 1: Create the baseline design reference**

Create `.codex/skills/travel-skill/references/html-design-baseline.md` with content covering:

```md
# HTML Design Baseline

## Default Positioning
- High-end travel editorial
- Print-like pacing
- Immersive but restrained

## Layout Principles
- Strong title hierarchy
- Generous whitespace
- Image-led storytelling instead of card-first composition
- Clear entry / body / exit rhythm for each section

## Color and Type
- Avoid generic SaaS palettes
- Prefer refined, destination-sensitive neutrals with limited accents
- Use expressive display typography paired with readable body typography

## Content Integrity
- Visual treatment may enrich a section
- Section order must still follow the guide contract
```

- [ ] **Step 2: Create the visual rules reference**

Create `.codex/skills/travel-skill/references/html-visual-rules.md` with concrete rules for how travel-guide sections should look. The file should explicitly cover:

```md
# HTML Visual Rules

## Page Rhythm
- Cover / lead
- section intro
- main content body
- restrained source treatment

## Section-Specific Rules
- `recommended_route`: hero summary + narrative timeline
- `route_options`: comparison layout focused on trade-offs
- `clothing_guide`: layered wear guidance, not e-commerce cards
- `attractions`: sequence and experience framing, not waterfall cards
- `transport_details`: scannable operational hierarchy
- `food_by_city`: lifestyle treatment under the same visual system
- `tips`: side-notes, warning blocks, field notes
- `sources`: compact and trustworthy

## Responsive Rule
- Desktop and mobile must share the same facts
- Mobile may split long reading flows into sections without changing order
```

- [ ] **Step 3: Create the anti-pattern reference**

Create `.codex/skills/travel-skill/references/html-anti-patterns.md` with content equivalent to:

```md
# HTML Anti-Patterns

Do not ship pages that look like:
- generic dashboard grids
- SaaS landing pages
- purple-gradient AI marketing sites
- all-card layouts with identical chrome
- over-labeled tag clouds
- icon-heavy blocks unrelated to travel reading

Do not:
- wrap every section in the same bordered card
- place a feature-grid immediately after the hero
- flatten narrative sections into interchangeable modules
- use motion or decoration that distracts from route decisions
```

- [ ] **Step 4: Verify the new references exist and are readable**

Run:

```powershell
Get-Content '.codex\skills\travel-skill\references\html-design-baseline.md' -Encoding UTF8
Get-Content '.codex\skills\travel-skill\references\html-visual-rules.md' -Encoding UTF8
Get-Content '.codex\skills\travel-skill\references\html-anti-patterns.md' -Encoding UTF8
```

Expected: all three files load successfully and contain explicit baseline, section-specific rules, and anti-patterns.

- [ ] **Step 5: Verify the references are wired into the skill**

Run:

```powershell
rg -n "html-design-baseline|html-visual-rules|html-anti-patterns" '.codex\skills\travel-skill\SKILL.md'
```

Expected: three matches in the canonical references section.

- [ ] **Step 6: Commit**

Run:

```powershell
git add -- '.codex/skills/travel-skill/references/html-design-baseline.md' '.codex/skills/travel-skill/references/html-visual-rules.md' '.codex/skills/travel-skill/references/html-anti-patterns.md' '.codex/skills/travel-skill/SKILL.md'
git commit -m "docs: 为 travel-skill 增加 HTML 设计参考"
```

Expected: one commit recording the new internal design references.

### Task 3: Mark legacy templates as non-default assets

**Files:**
- Modify: `.codex/skills/travel-skill/SKILL.md`
- Test: `.codex/skills/travel-skill/SKILL.md`

- [ ] **Step 1: Add explicit legacy-asset wording**

Apply a patch to `.codex/skills/travel-skill/SKILL.md` so the rendering section or a dedicated note states:

```md
## Legacy Template Status

- Assets under `assets/templates/` may remain for compatibility, but they do not define the skill's default publication style.
- New guide work should treat them as migration-era assets unless a later implementation plan explicitly revives them.
```

- [ ] **Step 2: Verify the wording does not promise template deletion**

Run:

```powershell
rg -n "delete|remove|must emit all five templates|exactly five guide templates" '.codex\skills\travel-skill\SKILL.md'
```

Expected: no language implying template deletion or five-template publication remains.

- [ ] **Step 3: Verify assets still exist untouched**

Run:

```powershell
Get-ChildItem '.codex\skills\travel-skill\assets\templates' | Select-Object Name
```

Expected: the existing template files are still present; this confirms the plan only downgraded them in documentation.

- [ ] **Step 4: Commit**

Run:

```powershell
git add -- '.codex/skills/travel-skill/SKILL.md'
git commit -m "docs: 标注 travel-skill 旧模板为遗留资产"
```

Expected: one commit recording the legacy-template downgrade note.

### Task 4: Final doc verification and handoff

**Files:**
- Modify: `docs/superpowers/specs/2026-04-14-travel-skill-editorial-html-design.md`
- Test: `.codex/skills/travel-skill/SKILL.md`
- Test: `.codex/skills/travel-skill/references/html-design-baseline.md`
- Test: `.codex/skills/travel-skill/references/html-visual-rules.md`
- Test: `.codex/skills/travel-skill/references/html-anti-patterns.md`

- [ ] **Step 1: Update the spec status from `draft` to `approved-for-implementation`**

Apply a patch to `docs/superpowers/specs/2026-04-14-travel-skill-editorial-html-design.md`:

```md
状态：approved-for-implementation
```

- [ ] **Step 2: Run a full documentation consistency check**

Run:

```powershell
rg -n "frontend-design|five guide templates|all five templates" '.codex\skills\travel-skill' 'docs\superpowers\specs\2026-04-14-travel-skill-editorial-html-design.md'
```

Expected: no matches in the skill documentation that contradict the new direction.

Then run:

```powershell
rg -n "editorial|legacy|anti-pattern|section order" '.codex\skills\travel-skill' 'docs\superpowers\specs\2026-04-14-travel-skill-editorial-html-design.md'
```

Expected: matches across the skill and spec confirming the new baseline, the preserved order constraint, and the legacy-template downgrade.

- [ ] **Step 3: Capture final git state**

Run:

```powershell
git status --short
```

Expected: only intended documentation changes remain staged or committed; no accidental script or template edits.

- [ ] **Step 4: Commit**

Run:

```powershell
git add -- 'docs/superpowers/specs/2026-04-14-travel-skill-editorial-html-design.md' '.codex/skills/travel-skill/SKILL.md' '.codex/skills/travel-skill/references/html-design-baseline.md' '.codex/skills/travel-skill/references/html-visual-rules.md' '.codex/skills/travel-skill/references/html-anti-patterns.md'
git commit -m "docs: 完成 travel-skill 杂志式 HTML 文档重构"
```

Expected: final documentation handoff commit if any documentation-only delta remains.

## Self-Review

### Spec coverage

- Spec section 2 goals map to Task 1 and Task 2.
- Spec section 4 design principles map to Task 1 and Task 2.
- Spec section 6 target structure maps to Task 1, Task 2, and Task 3.
- Spec section 7 design baseline maps to Task 2.
- Spec section 8 render/verify rewrite direction maps to Task 1 and Task 3.
- Spec section 11 acceptance criteria map across Task 1 to Task 4.

No uncovered spec section remains for this documentation-only phase.

### Placeholder scan

- No `TODO`, `TBD`, or “implement later” placeholders remain.
- Every modification target uses exact paths.
- Every verification step includes explicit commands and expected outcomes.

### Type consistency

- New reference names are consistent across all tasks:
  - `html-design-baseline.md`
  - `html-visual-rules.md`
  - `html-anti-patterns.md`
- The retained content-order contract is always referred to as `Guide Contract`.

