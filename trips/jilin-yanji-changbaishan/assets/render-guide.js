function byId(id) {
  return document.getElementById(id);
}

function renderList(items) {
  return items.map((item) => `<li>${item}</li>`).join("");
}

function renderCards(items, className = "card-grid") {
  return items.map((item) => `
    <article class="card">
      <h3>${item.title}</h3>
      <p>${item.summary}</p>
      ${item.points ? `<ul>${renderList(item.points)}</ul>` : ""}
    </article>
  `).join("");
}

window.tripGuideRenderer = {
  byId,
  renderList,
  renderCards
};
