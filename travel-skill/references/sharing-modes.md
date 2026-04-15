# Sharing Modes

- `engineered-site`: maintainable guide project for later updates
- `single-html`: single-file share version with inline CSS, JS, and data
- `zip-bundle`: transfer package containing share pages, notes, and summary
- `static-url`: optional publish target when deployment conditions exist

## Output Layout

- `guides/<slug>/desktop/editorial/index.html`
- `guides/<slug>/mobile/editorial/index.html`
- `guides/<slug>/assets/base.css`
- `guides/<slug>/assets/guide-content.js`
- `guides/<slug>/assets/render-guide.js`
- `guides/<slug>/notes/sources.md`

## Share Deliverables

- `portal.html`: navigation entry for the share package
- `recommended.html`: lighter single-file recommended guide
- `share.html`: single-file comprehensive guide
- `package.zip`: archive bundle for transfer and backup

## Canonical Ordering

Section ordering and layer structure are defined in `content-schema.md` and the runtime template config.
