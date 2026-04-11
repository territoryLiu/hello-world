# Sharing Modes

- `engineered-site`: 可维护工程目录，用于后续更新。
- `single-html`: 单文件分享版，CSS/JS/数据内联，可离线打开。
- `zip-bundle`: 打包分发，至少包含 HTML、来源说明和摘要。
- `static-url`: 可选部署结果；无部署条件时不作为默认交付承诺。

## Output Layout

- `trips/<slug>/desktop/<layer>/index.html`
- `trips/<slug>/mobile/<layer>/index.html`
- `trips/<slug>/assets/base.css`
- `trips/<slug>/assets/guide-content.js`
- `trips/<slug>/assets/render-guide.js`
- `trips/<slug>/notes/sources.md`
- `trips/<slug>/notes/image-plan.md`

## Ordered Sections

- `overview`
- `recommended`
- `options`
- `attractions`
- `food`
- `season`
- `packing`
- `transport`
- `sources`
