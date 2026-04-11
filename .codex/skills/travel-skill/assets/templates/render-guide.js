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

window.tripGuideRenderer = {
  escapeHtml,
  sanitizeUrl
};
