# Travel Planning Playbook Redesign

Date: 2026-04-10
Status: Approved for planning
Owner: Codex

## Objective

Rewrite `travel-planning-playbook.md` into a reusable execution manual for travel-guide HTML work. The playbook should define how to gather trip requirements, research sources, generate multiple itinerary options, structure output content, and deliver both desktop and mobile HTML guides with a separate image-placement plan.

This redesign also establishes the rules that will govern the next implementation phase for the Jilin / Yanji / Changbai Mountain project.

## Scope

In scope:

- Redesign the playbook into an execution-oriented manual
- Define fixed intake questions before any itinerary work starts
- Define research order and source priorities
- Define itinerary-option generation rules
- Define required HTML content order
- Define module schemas for attractions, food, seasonality, clothing, packing, and transport
- Define desktop/mobile dual-output requirements
- Define image-placement planning rules
- Define tone and wording rules
- Define final delivery checklist
- Define the target file structure for the Jilin project

Out of scope in this design doc:

- Implementing the rewritten playbook itself
- Rebuilding the Jilin HTML files
- Finalizing live travel data or source lists
- Downloading or embedding actual images

## User Requirements Captured

The user approved the following core direction:

- Update `travel-planning-playbook.md` first, then use it to guide the Jilin guide work
- Keep the travel-guide page result-oriented and practical
- Put the daily itinerary near the front of the HTML
- Provide multiple itinerary options and clearly mark the most recommended one
- Produce both desktop and mobile versions in separate folders
- Mobile version should be paginated for easier reading, with content matching the desktop version
- Build an image-placement plan first instead of directly embedding images
- Sources may include official sites, public web pages, Xiaohongshu, Douyin, Bilibili, comments, and video moments
- Tone should be warm, restrained, direct, and service-oriented
- Avoid backstage-writing language and awkward, overly forceful wording

## Current Project Context

Observed repository context:

- `travel-planning-playbook.md` already contains useful writing rules, but it is closer to a style guide than an execution manual
- `吉林延吉长白山trip.html` is the current reference guide and contains content, structure, and wording patterns that need revision
- The existing guide includes banned phrasing the user explicitly wants removed
- Recent repository history shows prior trip-guide work and a previous design spec, which indicates this redesign is an evolution of an existing workflow rather than a greenfield document

Known trip input for the upcoming implementation:

- Route: Nanjing -> Changchun / Yanji / Changbai Mountain
- Dates: 2026-04-30 to 2026-05-05
- Group: 4 adults, around 28 years old, two men and two women
- Departure city: Nanjing
- Pace: willing to accept early starts
- Accommodation baseline: Hanting preferred, standard room budget 150-450 CNY per room
- Budget: estimate first, not fixed upfront
- Deliverable: desktop HTML, mobile HTML, source notes, image-placement plan

## Proposed Redesign

### 1. Playbook Role

The new playbook should become a task manual, not a loose collection of writing advice.

It should answer:

- What information must be confirmed before research starts
- In what order research should happen
- How itinerary options should be assembled
- What sections the final HTML must include
- What rules keep desktop and mobile outputs aligned
- How to collect image opportunities without prematurely embedding assets

### 2. Playbook Structure

The rewritten `travel-planning-playbook.md` should use the following top-level structure:

1. Goal and applicability
2. Required intake before execution
3. Research workflow and source priority
4. Itinerary-option generation rules
5. HTML structure requirements
6. Attraction module requirements
7. Food recommendation module requirements
8. Seasonality, clothing, and packing requirements
9. Transport module requirements
10. Image-placement planning requirements
11. Tone and wording requirements
12. Final delivery checklist
13. Reusable execution template

This ordering is intentional. It moves from input collection, to research, to synthesis, to output structure, to final review.

## Detailed Design

### Goal and Applicability

This section should define the playbook as the standard workflow for creating travel-guide HTML pages. It should state that the primary deliverable is an actionable guide that can be used directly, not an essay about how the guide was created.

Required rule:

- The body copy delivers decisions and usable information only; it does not describe the authoring process, search process, or layout process.

### Required Intake Before Execution

This section should define the fixed pre-execution intake checklist. Each field should include what it is and why it matters.

Required intake fields:

- Departure city or cities
- Travel date range
- Trip duration if not obvious from dates
- Number of travelers
- Approximate age range
- Whether children are included
- Whether older adults are included
- Rooming or gender split when relevant
- Budget range or preferred estimation mode
- Accommodation preference
- Preferred travel pace
- Whether early starts are acceptable
- Whether late returns are acceptable
- Preference weighting: food, photo spots, scenic coverage, leisure, hiking, shopping
- Whether desktop and mobile outputs are both required
- Whether an image-placement plan is required

This section should make it easy to reuse the workflow with future destinations.

### Research Workflow and Source Priority

This section should convert the current general advice into a strict execution order.

Recommended research phases:

1. Official destination and attraction sources
2. Transport sources
3. Weather and historical climate references
4. Ticket, reservation, and operating-hour checks
5. Food recommendation sources with menu-level detail
6. Social-platform experience signals
7. Cross-checking and source consolidation

Rules by phase:

- Official sources are the primary basis for ticketing, reservations, business hours, and transport policies
- Transport research must cover flights, rail, long-distance road transport, local transit, rideshare/taxi, and self-drive where relevant
- Historical weather and seasonal patterns should support clothing guidance
- Food research should prioritize public restaurant pages and consumer platforms that expose recommended dishes and address details
- Xiaohongshu, Douyin, and Bilibili should be used to extract repeated real-world observations from body text, comments, audio, captions, and video moments
- Social-platform findings should be summarized as high-frequency conclusions, not copied as platform-native narration
- Sources should be consolidated at the end rather than repeatedly interrupting the main body

### Itinerary-Option Generation Rules

This section should standardize how route choices are produced.

Minimum output:

- One most recommended option
- At least two additional options

Typical option set:

- Most recommended plan
- Easier or lighter-paced plan
- More complete scenic-coverage plan
- Optional weather backup or budget-leaning version when relevant

Required fields for each option:

- Option name
- Who it suits
- Total duration
- Core highlights
- Day-by-day arrangement
- Main transport chain
- Accommodation arrangement
- Estimated cost level
- Recommendation level
- Execution notes

The recommended option should always appear first and explicitly explain why it best matches the confirmed traveler profile.

### HTML Structure Requirements

This section should become a hard output rule for all future travel HTML work.

Required section order:

1. Title
2. Day-by-day overview
3. Most recommended itinerary
4. Additional itinerary options
5. Attraction guide
6. Tickets, pricing, and reservation timing
7. Food recommendations and restaurant library
8. Best season and current-month view
9. Current-month clothing and packing
10. Origin-to-destination transport guide
11. Information sources

Key rule:

- The front of the page should quickly show how each day is arranged before the reader enters the deeper attraction and food library.

### Attraction Module Requirements

Each attraction entry should be normalized into a reusable field set.

Required fields:

- Attraction name
- Short description
- Recommended day or placement in itinerary
- Suggested visit duration
- Ticket or pricing information
- Reservation method
- Reservation timing
- Operating hours
- What can usually be seen in the current month
- Practical reminder

This structure supports both city attractions and scenic-area entries.

### Food Recommendation Module Requirements

This section should emphasize breadth and decision usefulness.

Each restaurant entry should include:

- Restaurant name
- Address
- City or district
- Cuisine style
- Recommended dishes
- Per-person spending reference
- Best meal slot
- Who it suits
- Short note

Rules:

- Major stopover cities should have larger restaurant pools
- Recommended dishes should be sourced primarily from public restaurant/consumer platforms such as Meituan or Dianping when available
- Social-platform content can be used to add atmosphere, peak-time advice, and recurring dish mentions

### Seasonality, Clothing, and Packing Requirements

This section should be split into "best time to go" and "what to prepare for the current trip window."

Required fields:

- Best months
- What is strongest in the current month
- What is limited or less likely in the current month
- City clothing guidance
- Scenic-area clothing guidance
- Essential items

This section should make climate differences between urban areas and mountain/scenic areas explicit.

### Transport Module Requirements

This section should prevent shallow transport advice.

Transport modes to cover as applicable:

- Flight
- High-speed rail or rail
- Long-distance coach or bus
- Local bus
- Metro
- Self-drive
- Taxi or rideshare

Required fields per transport option:

- Origin
- Destination
- Estimated duration
- Estimated price
- Best use case
- Recommendation priority
- Reminder

Time-sensitive rule:

- All schedule-based information should indicate the date through which it was checked, and holiday transport uncertainty should be clearly marked.

### Image-Placement Planning Requirements

This section should define how to prepare visual guidance before embedding any image.

Required fields per image slot:

- Image slot ID
- Page location
- Suggested subject or scene
- Recommended source type
- If video-based, what kind of moment or timestamp to capture
- Why this image belongs in that position

Allowed source types may include:

- Official tourism pages
- Public attraction pages
- Xiaohongshu posts and comments
- Douyin videos and comments
- Bilibili videos and comments
- Public media or city guides

### Tone and Wording Requirements

This section should consolidate the user's style guidance into enforceable writing rules.

Required tone characteristics:

- Warm
- Restrained
- Direct
- Helpful
- Result-oriented

Required expression rules:

- Prefer wording such as "more suitable," "more practical," "more time-saving," and "worth noting"
- Use reminder-style phrasing rather than lecture-style phrasing
- Keep a light service tone without foregrounding the writer
- Avoid describing the creative process, revision process, or curation process inside body copy
- Avoid awkward or overly forceful judgment phrases
- Avoid stacking negative commands; prefer constructive guidance

### Final Delivery Checklist

The playbook should end with a checklist that confirms:

- Intake questions are complete
- Multiple itinerary options exist
- The most recommended option is clearly marked
- Day-by-day arrangement appears near the front
- Attractions include pricing and reservation information
- Food entries include address, cuisine, and recommended dishes
- Best season and current-month conditions are present
- Clothing and essential-item guidance are present
- Transport modes, times, and prices are covered
- Sources are consolidated at the end
- Desktop and mobile outputs are both prepared when required
- Image-placement planning is prepared when required

### Reusable Execution Template

The playbook should end with a reusable execution template that future runs can follow quickly. This should be compact enough to use as a working skeleton but specific enough that major fields cannot be skipped.

## Output and File Layout for the Jilin Project

After the playbook rewrite is implemented, the Jilin trip project should use this structure:

- `trips/jilin-yanji-changbaishan/desktop/index.html`
- `trips/jilin-yanji-changbaishan/mobile/index.html`
- `trips/jilin-yanji-changbaishan/notes/sources.md`
- `trips/jilin-yanji-changbaishan/notes/image-plan.md`

Rules for these outputs:

- Desktop and mobile versions must carry the same factual content
- Mobile presentation should use shorter paginated reading units
- Image planning should remain separate from the HTML until source selection is finished
- Source notes should remain easier to audit than the final HTML body

## Risks and Design Constraints

### Risk 1: Playbook becomes too broad

If the rewrite tries to cover every possible travel edge case, it may stop being usable. The design should remain biased toward practical HTML travel-guide production rather than becoming a general tourism research encyclopedia.

Response:

- Keep the playbook optimized for destination-guide page production
- Use reusable schemas instead of exhaustive prose

### Risk 2: Mobile and desktop drift apart

If the playbook does not explicitly define content parity, the two outputs may diverge.

Response:

- Add a hard requirement that content stays consistent across both outputs
- Limit differences to layout, pagination, and interaction pattern

### Risk 3: Social content overwhelms official facts

Social platforms are valuable for real-world signals but weak for rules and pricing.

Response:

- Preserve official-source priority for reservations, pricing, and operating information
- Use social content mainly for high-frequency experience signals, imagery ideas, timing advice, and practical reminders

### Risk 4: Tone rules become vague

If style guidance remains abstract, implementation may regress into the same wording the user already rejected.

Response:

- Write explicit acceptable and unacceptable phrasing rules
- Tie wording rules directly to body-copy use, not just to general tone labels

## Testing and Validation Strategy

This is a documentation redesign, so validation should focus on completeness and future usability.

Validation criteria:

- Every future trip guide can start with the intake section without inventing new intake logic
- The research workflow can be executed step by step without ambiguity
- The output structure makes "day-by-day first" unavoidable
- Dual-format delivery rules are explicit
- Image-placement planning can be executed without mixing source notes into the main HTML
- Tone rules are concrete enough to reject banned phrasing during implementation

## Implementation Readiness

Once this design is accepted and the spec is reviewed, the next phase should:

1. Rewrite `travel-planning-playbook.md`
2. Preserve only the still-useful parts of the current playbook
3. Remove style-only repetition that no longer serves execution
4. Convert the Jilin HTML work into a second phase governed by the rewritten playbook

## Open Decisions Resolved

These decisions are considered resolved for planning:

- The playbook update comes before the Jilin HTML rebuild
- The playbook should be reusable beyond this one destination
- The final travel guide should include multiple options and mark the recommended one
- Day-by-day arrangements must appear near the front
- Desktop and mobile outputs should be separate but content-matched
- Image planning should be a separate artifact first

