(function () {
  const data = window.travelStyleSampleData;
  if (!data) return;

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderCard(card) {
    return `
      <article class="story-card">
        <div class="story-card-head"><h4>${escapeHtml(card.title)}</h4></div>
        <p class="story-summary">${escapeHtml(card.summary)}</p>
        <ul class="story-points">${card.points.map((point) => `<li>${escapeHtml(point)}</li>`).join("")}</ul>
      </article>
    `;
  }

  function renderSection(section) {
    return `
      <section class="guide-section" id="${escapeHtml(section.id)}">
        <div class="guide-section-head">
          <p class="section-index">${escapeHtml(section.title)}</p>
          <h3>${escapeHtml(section.title)}</h3>
          <p class="section-intro">${escapeHtml(section.intro)}</p>
        </div>
        <div class="section-card-grid">${section.cards.map(renderCard).join("")}</div>
      </section>
    `;
  }

  function renderDesktop() {
    return `
      <div class="guide-root guide-desktop">
        <header class="guide-hero">
          <div class="guide-hero-copy">
            <p class="guide-kicker">${escapeHtml(data.meta.subtitle)}</p>
            <h2>${escapeHtml(data.meta.title)}</h2>
            <p class="guide-hero-summary">${escapeHtml(data.meta.summary)}</p>
            <div class="hero-meta-row">
              <span>桌面端示意</span>
              <span>${escapeHtml(data.meta.accent)}</span>
            </div>
          </div>
          <aside class="guide-hero-panel">
            <p class="hero-panel-label">阅读重点</p>
            <ul class="hero-highlights">${data.highlights.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          </aside>
        </header>
        <nav class="guide-nav">${data.sections.map((section) => `<a href="#${escapeHtml(section.id)}">${escapeHtml(section.title)}</a>`).join("")}</nav>
        <div class="guide-sections">${data.sections.map(renderSection).join("")}</div>
      </div>
    `;
  }

  function renderMobile() {
    return `
      <div class="guide-root guide-mobile">
        <header class="mobile-hero">
          <p class="guide-kicker">${escapeHtml(data.meta.subtitle)}</p>
          <h2>${escapeHtml(data.meta.title)}</h2>
          <p class="guide-hero-summary">${escapeHtml(data.meta.summary)}</p>
        </header>
        <div class="mobile-quick-grid">
          ${data.highlights.slice(0, 4).map((item, index) => `<article class="quick-card quick-card-${index + 1}"><p>${escapeHtml(item)}</p></article>`).join("")}
        </div>
        <div class="mobile-sections">
          ${data.sections.map((section) => `
            <section class="mobile-section">
              <div class="guide-section-head">
                <p class="section-index">${escapeHtml(section.title)}</p>
                <h3>${escapeHtml(section.title)}</h3>
                <p class="section-intro">${escapeHtml(section.intro)}</p>
              </div>
              <div class="mobile-card-stack">${section.cards.map(renderCard).join("")}</div>
            </section>
          `).join("")}
        </div>
      </div>
    `;
  }

  document.querySelectorAll('[data-preview="desktop"]').forEach((node) => {
    node.innerHTML = renderDesktop();
  });

  document.querySelectorAll('[data-preview="mobile"]').forEach((node) => {
    node.innerHTML = renderMobile();
  });
})();
