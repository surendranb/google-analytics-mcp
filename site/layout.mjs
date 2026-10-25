// Page shell for ga4mcp.com. One layout, no framework.
import { readFileSync } from "node:fs";

const SITE = "https://ga4mcp.com";
const VERSION = readFileSync(new URL("../pyproject.toml", import.meta.url), "utf8")
  .match(/^version\s*=\s*"([^"]+)"/m)[1];
const UPDATED = "2026-10-25";

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

export const TOP_NAV = [
  { label: "Install", href: "/setup/" },
  { label: "Skills", href: "/skills/" },
  { label: "Clients", href: "/ga4-mcp-for-every-harness/" },
  { label: "Plugins", href: "/ga4-plugins/" },
  { label: "GitHub", href: "https://github.com/surendranb/google-analytics-mcp", gh: true },
];

export function page({ slug, title, description, body, sidebar = null, active = "", full = false, type = "TechArticle" }) {
  const canonical = slug === "/" ? `${SITE}/` : `${SITE}${slug}`;
  if (description && description.length > 158) {
    const cut = description.slice(0, 155);
    description = cut.slice(0, cut.lastIndexOf(" ")).replace(/[,.;:]$/, "") + "…";
  }
  const h = esc(slug);
  const ld = JSON.stringify({
    "@context": "https://schema.org",
    "@type": type,
    name: title,
    description,
    url: canonical,
    ...(type === "SoftwareApplication"
      ? {
          applicationCategory: "DeveloperApplication",
          operatingSystem: "macOS, Linux, Windows",
          softwareVersion: VERSION,
          license: "https://opensource.org/licenses/MIT",
          offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
        }
      : { isPartOf: { "@type": "WebSite", name: "GA4 MCP", url: SITE }, dateModified: UPDATED }),
  });

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}">
<link rel="canonical" href="${canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="GA4 MCP">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${canonical}">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#fef6e4">
<link rel="icon" href="/assets/logo.png" type="image/png">
<link rel="stylesheet" href="/assets/site.css">
<script type="application/ld+json">${ld}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap top__in">
    <a class="brand" href="/"><span class="brand__mark">GA</span>GA4 MCP<span class="brand__ver">v${VERSION}</span></a>
    <nav class="top__nav" aria-label="Primary">
      ${TOP_NAV.map((n) => `<a href="${n.href}"${n.gh ? ' class="gh" rel="noopener"' : ""}${active === n.href ? ' class="is-active"' : ""}>${n.label}</a>`).join("\n      ")}
    </nav>
  </div>
</header>
<div class="wrap">
  <div class="frame${full ? " frame--full" : ""}">
    ${sidebar ? `<aside class="side">${sidebar}</aside>` : ""}
    <main id="main">
${body}
    </main>
  </div>
</div>
<footer class="foot">
  <div class="wrap foot__in">
    <div>MIT licensed. Built by <a href="https://builditwithai.xyz" rel="noopener">Surendran B</a>. Not affiliated with Google.</div>
    <div class="foot__links">
      <a href="https://github.com/surendranb/google-analytics-mcp" rel="noopener">GitHub</a>
      <a href="https://pypi.org/project/google-analytics-mcp/" rel="noopener">PyPI</a>
      <a href="https://www.npmjs.com/package/@surendranb/google-analytics-mcp" rel="noopener">npm</a>
      <a href="/llms.txt">llms.txt</a>
      <a href="/privacy/">Privacy</a>
      <a href="/terms/">Terms</a>
    </div>
  </div>
</footer>
<script>
document.querySelectorAll('.cb__copy').forEach(function(b){
  b.addEventListener('click',function(){
    var c=b.parentElement.nextElementSibling.innerText;
    navigator.clipboard.writeText(c).then(function(){var o=b.textContent;b.textContent='Copied';setTimeout(function(){b.textContent=o},1200)})
  })
})
</script>
</body>
</html>
`;
}

export function sidebarFor(groups, current) {
  return groups
    .map(
      (g) => `<div class="side__group"><p class="side__h">${esc(g.title)}</p><ul>${g.items
        .map((i) => `<li><a href="${i.href}"${i.href === current ? ' class="is-active" aria-current="page"' : ""}>${esc(i.label)}</a></li>`)
        .join("")}</ul></div>`
    )
    .join("\n");
}

export { SITE, VERSION, UPDATED, esc };
