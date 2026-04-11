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

function renderList(items) {
  if (!Array.isArray(items) || items.length === 0) {
    return "";
  }
  return items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function sanitizeUrl(value) {
  if (!value) {
    return "";
  }

  try {
    const parsed = new URL(String(value), "https://travel-skill.local");
    const protocol = parsed.protocol.toLowerCase();
    if (protocol === "http:" || protocol === "https:") {
      return String(value);
    }
  } catch (error) {
    return "";
  }

  return "";
}

function renderContentCard(item) {
  if (!item || typeof item !== "object") {
    return "";
  }
  const badge = item.is_placeholder ? '<span class="is-placeholder">待补充</span>' : "";
  const points = Array.isArray(item.points) && item.points.length
    ? `<ul class="card-points">${renderList(item.points)}</ul>`
    : "";
  const extraClass = item.is_placeholder ? " card-placeholder" : "";
  return `
    <article class="card${extraClass}">
      <div class="card-header">
        <h3>${escapeHtml(item.title || "内容条目")}</h3>
        ${badge}
      </div>
      <p class="card-summary">${escapeHtml(item.summary || "")}</p>
      ${points}
    </article>
  `;
}

function renderSourceCard(source) {
  if (!source || typeof source !== "object") {
    return "";
  }
  const href = sanitizeUrl(source.url);
  const safeHref = href ? escapeHtml(href) : "";
  const checkedAt = source.checked_at ? `<span class="source-badge">核对 ${escapeHtml(source.checked_at)}</span>` : "";
  const title = escapeHtml(source.title || "待补充来源");
  const type = escapeHtml(source.type || "unknown");
  const rawUrl = source.url && !href ? `<p class="source-meta">原始链接：${escapeHtml(source.url)}</p>` : "";
  const url = safeHref ? `<a class="source-url" href="${safeHref}" target="_blank" rel="noreferrer noopener">${safeHref}</a>` : '<span class="empty-text">暂无链接</span>';
  return `
    <article class="source-card">
      <div class="source-header">
        <h3>${title}</h3>
        ${checkedAt}
      </div>
      <p class="source-meta">来源类型：${type}</p>
      ${rawUrl}
      <p>${url}</p>
    </article>
  `;
}

const tripGuideRenderer = {
  escapeHtml,
  renderList,
  sanitizeUrl,
  renderContentCard,
  renderSourceCard
};

if (typeof window !== "undefined") {
  window.tripGuideRenderer = tripGuideRenderer;
}
