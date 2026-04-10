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

function renderList(items = []) {
  if (!items.length) {
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

window.tripGuideRenderer = {
  byId,
  renderList,
  renderCards
};
