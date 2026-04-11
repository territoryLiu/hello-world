# Travel Style Samples Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build four directly viewable travel-guide style sample pages plus an index page under `sample/` so the user can compare visual directions.

**Architecture:** Create one shared sample data model and one shared base stylesheet for layout helpers, then layer four style-specific theme files and four HTML pages on top. Each page will contain a desktop preview block and a mobile preview block so the user can compare both reading modes without running the full trip pipeline.

**Tech Stack:** Static HTML, CSS, minimal vanilla JavaScript, existing repository file structure.

---

### Task 1: Scaffold Sample Directory

**Files:**
- Create: `sample/travel-style-samples/index.html`
- Create: `sample/travel-style-samples/assets/shared.css`
- Create: `sample/travel-style-samples/assets/sample-data.js`

- [ ] Step 1: Create the static sample directory structure
- [ ] Step 2: Add shared layout styles for preview shells, grids, cards, and typography helpers
- [ ] Step 3: Add one shared data file with route, clothing, attractions, food, tips, and sources sample content

### Task 2: Build Four Style Pages

**Files:**
- Create: `sample/travel-style-samples/style-a-editorial.html`
- Create: `sample/travel-style-samples/style-b-destination.html`
- Create: `sample/travel-style-samples/style-c-hotel.html`
- Create: `sample/travel-style-samples/style-d-bento.html`
- Create: `sample/travel-style-samples/assets/style-a.css`
- Create: `sample/travel-style-samples/assets/style-b.css`
- Create: `sample/travel-style-samples/assets/style-c.css`
- Create: `sample/travel-style-samples/assets/style-d.css`

- [ ] Step 1: Build style A as black-and-white editorial magazine direction
- [ ] Step 2: Build style B as destination poster and travel-feature direction
- [ ] Step 3: Build style C as soft luxury hotel-journal direction
- [ ] Step 4: Build style D as modern information-design and bento direction

### Task 3: Add Navigation And Shared Preview Composition

**Files:**
- Modify: `sample/travel-style-samples/index.html`
- Modify: `sample/travel-style-samples/style-a-editorial.html`
- Modify: `sample/travel-style-samples/style-b-destination.html`
- Modify: `sample/travel-style-samples/style-c-hotel.html`
- Modify: `sample/travel-style-samples/style-d-bento.html`

- [ ] Step 1: Add a shared index page with cards linking to the four sample pages
- [ ] Step 2: Ensure each sample page has back navigation and labels for desktop and mobile previews
- [ ] Step 3: Keep the content skeleton consistent so visual comparison is fair

### Task 4: Verify Static Output

**Files:**
- Test: `sample/travel-style-samples/index.html`
- Test: `sample/travel-style-samples/style-a-editorial.html`
- Test: `sample/travel-style-samples/style-b-destination.html`
- Test: `sample/travel-style-samples/style-c-hotel.html`
- Test: `sample/travel-style-samples/style-d-bento.html`

- [ ] Step 1: Check file existence and link targets
- [ ] Step 2: Open the pages through local static verification if needed
- [ ] Step 3: Confirm all pages are self-contained and readable without backend services
