const HTML_ESCAPES = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;"
};

function escapeHtml(value) {
  if (value == null) {
    return "";
  }
  return String(value).replace(/[&<>"']/g, (char) => HTML_ESCAPES[char] || char);
}

function byId(id) {
  return document.getElementById(id);
}

function renderList(items) {
  if (!Array.isArray(items) || items.length === 0) {
    return "";
  }
  return items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderCards(items = []) {
  if (!Array.isArray(items) || items.length === 0) {
    return "";
  }

  return items
    .map((item) => {
      const points = Array.isArray(item.points) && item.points.length
        ? `<ul>${renderList(item.points)}</ul>`
        : "";

      return `
        <article class="card">
          <h3>${escapeHtml(item.title)}</h3>
          <p>${escapeHtml(item.summary)}</p>
          ${points}
        </article>
      `;
    })
    .join("");
}

function renderSources(groups = []) {
  if (!Array.isArray(groups) || groups.length === 0) {
    return "";
  }

  return groups
    .map((group) => {
      const title = group && group.title ? escapeHtml(group.title) : "未命名信源";
      const summary = group && group.summary ? `<p>${escapeHtml(group.summary)}</p>` : "";

      const entries = group && Array.isArray(group.entries) && group.entries.length
        ? `
          <ul class="source-entries">
            ${group.entries
              .map((entry) => {
                const label = entry && (entry.title || entry.url) ? escapeHtml(entry.title || entry.url) : "链接";
                const href = entry && entry.url ? escapeHtml(entry.url) : "";
                const link = href
                  ? `<a href="${href}" target="_blank" rel="noreferrer noopener">${label}</a>`
                  : `<span>${label}</span>`;
                const checkedAt = entry && entry.checkedAt ? escapeHtml(entry.checkedAt) : "";
                const checked = checkedAt ? `<span class="source-checked">核对：${checkedAt}</span>` : "";
                return `<li>${link}${checked}</li>`;
              })
              .join("")}
          </ul>
        `
        : "";

      return `
        <article class="card">
          <h3>${title}</h3>
          ${summary}
          ${entries}
        </article>
      `;
    })
    .join("");
}

function renderSection(title, items, options = {}) {
  const safeTitle = escapeHtml(title || "");
  const lead = options && options.lead ? `<p>${escapeHtml(options.lead)}</p>` : "";
  const kind = options && options.kind ? String(options.kind) : "";

  const inner = kind === "sources" ? renderSources(items) : renderCards(items);

  return `
    <header class="mobile-head">
      <h2>${safeTitle}</h2>
      ${lead}
    </header>
    <div class="card-grid">${inner}</div>
  `;
}

const tripGuideRenderer = {
  byId,
  renderList,
  renderCards,
  renderSources,
  renderSection
};

if (typeof window !== "undefined") {
  window.tripGuideRenderer = tripGuideRenderer;
}
