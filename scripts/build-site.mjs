#!/usr/bin/env node
// Builds ga4mcp.com from site/content + skills/*/SKILL.md. Zero dependencies.
import { readFileSync, writeFileSync, mkdirSync, readdirSync, rmSync, existsSync, copyFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { createHash } from "node:crypto";
import { page, sidebarFor, SITE, VERSION, UPDATED, esc } from "../site/layout.mjs";

const ROOT = new URL("..", import.meta.url).pathname;
const OUT = join(ROOT, "docs");

/* ---------------- markdown ---------------- */

const inline = (s) => {
  const codes = [];
  let t = esc(s).replace(/`([^`]+)`/g, (_, c) => `\u0000${codes.push(c) - 1}\u0000`);
  t = t.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_, txt, url) => `<a href="${url}">${txt}</a>`);
  t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  t = t.replace(/(^|[\s(])\*([^*\n]+)\*/g, "$1<em>$2</em>");
  t = t.replace(/\u0000(\d+)\u0000/g, (_, i) => `<code>${codes[i]}</code>`);
  return t;
};

const codeBlock = (lang, code) =>
  `<div class="cb">${lang ? `<div class="cb__bar"><span class="cb__lang">${esc(lang)}</span><button class="cb__copy" type="button">Copy</button></div>` : `<div class="cb__bar"><span class="cb__lang">shell</span><button class="cb__copy" type="button">Copy</button></div>`}<pre><code>${esc(code)}</code></pre></div>`;

function md(src) {
  const lines = src.replace(/\r\n/g, "\n").split("\n");
  const out = [];
  let i = 0;

  const flushList = (buf, ordered) => {
    if (!buf.length) return "";
    const tag = ordered ? "ol" : "ul";
    return `<${tag}>${buf.map((x) => `<li>${inline(x)}</li>`).join("")}</${tag}>`;
  };

  while (i < lines.length) {
    const line = lines[i];

    // raw HTML block: a line starting with "<" is emitted verbatim until a blank line
    if (/^\s*</.test(line)) {
      const buf = [];
      while (i < lines.length && !/^\s*$/.test(lines[i])) buf.push(lines[i++]);
      out.push(buf.join("\n"));
      continue;
    }

    if (/^```/.test(line)) {
      const lang = line.slice(3).trim();
      const buf = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i])) buf.push(lines[i++]);
      i++;
      out.push(codeBlock(lang, buf.join("\n")));
      continue;
    }

    if (/^#{1,4}\s/.test(line)) {
      const lvl = line.match(/^#+/)[0].length;
      out.push(`<h${lvl}>${inline(line.replace(/^#+\s*/, ""))}</h${lvl}>`);
      i++;
      continue;
    }

    if (/^\s*$/.test(line)) { i++; continue; }

    if (/^(\*\s*){3,}$|^(-\s*){3,}$/.test(line)) { out.push("<hr>"); i++; continue; }

    if (/^>\s?/.test(line)) {
      const buf = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) buf.push(lines[i++].replace(/^>\s?/, ""));
      const first = buf[0] || "";
      const m = first.match(/^\*\*(Note|Tip|Warning|Heads up)[^*]*\*\*/i);
      if (m) {
        const label = m[1];
        buf[0] = first.replace(/^\*\*[^*]+\*\*\s*/, "");
        out.push(`<div class="note${label.toLowerCase() === "tip" ? " note--teal" : ""}"><span class="note__label">${esc(label)}</span><p>${buf.map(inline).join(" ")}</p></div>`);
      } else {
        out.push(`<blockquote>${buf.map((b) => `<p>${inline(b)}</p>`).join("")}</blockquote>`);
      }
      continue;
    }

    if (/^\|/.test(line) && /^\|[\s:|-]+\|?\s*$/.test(lines[i + 1] || "")) {
      const cells = (r) => r.split("|").slice(1, -1).map((c) => c.trim());
      const head = cells(lines[i]);
      i += 2;
      const rows = [];
      while (i < lines.length && /^\|/.test(lines[i])) rows.push(cells(lines[i++]));
      out.push(
        `<div class="tw"><table><thead><tr>${head.map((h) => `<th>${inline(h)}</th>`).join("")}</tr></thead><tbody>${rows
          .map((r) => `<tr>${r.map((c) => `<td>${inline(c)}</td>`).join("")}</tr>`)
          .join("")}</tbody></table></div>`
      );
      continue;
    }

    if (/^[-*]\s+/.test(line)) {
      const buf = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i])) buf.push(lines[i++].replace(/^[-*]\s+/, ""));
      out.push(flushList(buf, false));
      continue;
    }

    if (/^\d+\.\s+/.test(line)) {
      const buf = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) buf.push(lines[i++].replace(/^\d+\.\s+/, ""));
      out.push(flushList(buf, true));
      continue;
    }

    const buf = [];
    while (i < lines.length && !/^\s*$/.test(lines[i]) && !/^(```|#|>|\||[-*]\s|\d+\.\s)/.test(lines[i])) {
      buf.push(lines[i++]);
    }
    const text = buf.join(" ");
    out.push(`<p${/^<p class="lede"/.test("") ? "" : ""}>${inline(text)}</p>`);
  }
  return out.join("\n").replace(/<p>([^<]*<\/p>)?<\/p>/g, "");
}

function parseFrontmatter(raw) {
  const m = raw.match(/^---\n([\s\S]*?)\n---\n?/);
  if (!m) return { data: {}, body: raw };
  const data = {};
  for (const line of m[1].split("\n")) {
    const kv = line.match(/^([\w-]+):\s*(.*)$/);
    if (!kv) continue;
    let v = kv[2].trim();
    if (/^".*"$/.test(v)) v = v.slice(1, -1);
    data[kv[1]] = v;
  }
  return { data, body: raw.slice(m[0].length) };
}

/* ---------------- content ---------------- */

const stripH1 = (body) => body.replace(/^#\s+.+\n+/, "");

function loadContent() {
  const dir = join(ROOT, "site/content");
  return readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .map((f) => {
      const { data, body } = parseFrontmatter(readFileSync(join(dir, f), "utf8"));
      const slug = data.slug || `/${f.replace(/\.md$/, "")}/`;
      const h1 = (body.match(/^#\s+(.+)$/m) || [])[1] || data.title;
      return {
        slug,
        title: data.title || h1,
        nav: data.nav || data.title || h1,
        description: data.description || "",
        group: data.group || "start",
        order: Number(data.order || 50),
        full: data.full === "true",
        hero: data.hero === "true",
        html: md(stripH1(body)),
        raw: stripH1(body),
        titleTag: data.titleTag || data.title || h1,
      };
    });
}

function loadSkills() {
  const dir = join(ROOT, "skills");
  const seen = new Map();
  const out = [];
  for (const d of readdirSync(dir, { withFileTypes: true })) {
    if (!d.isDirectory() || !existsSync(join(dir, d.name, "SKILL.md"))) continue;
    const raw = readFileSync(join(dir, d.name, "SKILL.md"), "utf8");
    const { data, body } = parseFrontmatter(raw);
    const key = createHash("sha1").update(body).digest("hex");
    if (seen.has(key)) {
      const kept = seen.get(key);
      // prefer the directory whose name matches the declared skill name
      if (data.name === d.name && kept.name !== data.name) {
        out.splice(out.indexOf(kept), 1);
        seen.set(key, { name: d.name });
      } else {
        console.warn(`duplicate skill dropped: ${d.name} (identical to ${kept.name})`);
        continue;
      }
    } else {
      seen.set(key, { name: d.name });
    }
    const h1 = (body.match(/^#\s+(.+)$/m) || [])[1] || d.name;
    out.push({
      slug: `/skills/${d.name}/`,
      name: d.name,
      title: h1,
      description: data.description || "",
      html: md(stripH1(body)),
      raw: stripH1(body),
    });
  }
  return out.sort((a, b) => a.name.localeCompare(b.name));
}

const pages = loadContent();
const skills = loadSkills();

const GROUPS = [
  { key: "start", title: "Start" },
  { key: "skills", title: "Skills" },
  { key: "clients", title: "Clients" },
  { key: "plugins", title: "Plugins" },
  { key: "legal", title: "Legal" },
];

const skillIndex = pages.find((p) => p.slug === "/skills/");
const byGroup = (k) => pages.filter((p) => p.group === k).sort((a, b) => a.order - b.order);

const sidebarGroups = [
  { title: "Start", items: byGroup("start").map((p) => ({ href: p.slug, label: p.nav })) },
  { title: "Skills", items: [{ href: "/skills/", label: "All skills" }, ...skills.map((s) => ({ href: s.slug, label: s.title }))], onlyIn: "skills" },
  { title: "Clients", items: byGroup("clients").map((p) => ({ href: p.slug, label: p.nav })) },
  { title: "Plugins", items: byGroup("plugins").map((p) => ({ href: p.slug, label: p.nav })) },
  { title: "Legal", items: byGroup("legal").map((p) => ({ href: p.slug, label: p.nav })) },
];

/* ---------------- generated blocks ---------------- */

const SKILL_GROUPS = [
  { title: "Set it up", keys: ["gcp-setup", "service-account-setup"] },
  { title: "Diagnose a change", keys: ["traffic-diagnosis", "content-performance", "bot-traffic-detection", "geo-device-segmentation", "channel-acquisition"] },
  { title: "Measure a channel", keys: ["ecommerce-analysis", "attribution-scope", "ai-referral-analysis", "custom-dimensions"] },
  { title: "Get the query right", keys: ["common-metric-names", "filter-structures", "compatible-combinations", "date-ranges", "ga4-limitations", "ua-to-ga4"] },
];

function skillsBlock() {
  const byKey = Object.fromEntries(skills.map((s) => [s.name, s]));
  const used = new Set();
  const sections = SKILL_GROUPS.map((g) => {
    const rows = g.keys.map((k) => byKey[k]).filter(Boolean);
    rows.forEach((r) => used.add(r.name));
    if (!rows.length) return "";
    return `<h3>${esc(g.title)}</h3>\n<div class="tw"><table><tbody>${rows
      .map((s) => `<tr><td><a href="${s.slug}">${esc(s.title)}</a></td><td>${esc(s.description.replace(/^"|"$/g, ""))}</td></tr>`)
      .join("")}</tbody></table></div>`;
  });
  const rest = skills.filter((s) => !used.has(s.name));
  if (rest.length) {
    sections.push(
      `<h3>More</h3>\n<div class="tw"><table><tbody>${rest
        .map((s) => `<tr><td><a href="${s.slug}">${esc(s.title)}</a></td><td>${esc(s.description.replace(/^"|"$/g, ""))}</td></tr>`)
        .join("")}</tbody></table></div>`
    );
  }
  return sections.join("\n");
}

function clientsBlock() {
  const rows = byGroup("clients")
    .filter((p) => p.slug !== "/ga4-mcp-for-every-harness/")
    .map((p) => {
      const d = p.description;
      return `<tr><td><a href="${p.slug}">${esc(p.nav)}</a></td><td>${esc(d)}</td></tr>`;
    });
  return `<div class="tw"><table><thead><tr><th>Client</th><th>What the page covers</th></tr></thead><tbody>${rows.join("")}</tbody></table></div>`;
}

function pluginsBlock() {
  const rows = byGroup("plugins")
    .filter((p) => p.slug !== "/ga4-plugins/")
    .map((p) => `<tr><td><a href="${p.slug}">${esc(p.nav)}</a></td><td>${esc(p.description)}</td></tr>`);
  return `<div class="tw"><table><thead><tr><th>Bundle</th><th>What the page covers</th></tr></thead><tbody>${rows.join("")}</tbody></table></div>`;
}

function expand(html) {
  return html
    .replace("<!--SKILLS-->", skillsBlock())
    .replace("<!--CLIENTS-->", clientsBlock())
    .replace("<!--PLUGINS-->", pluginsBlock());
}



function emit(path, html) {
  const f = join(OUT, path);
  mkdirSync(dirname(f), { recursive: true });
  writeFileSync(f, html);
}

// keep only generated artefacts; drop the old docsify + hand-written twins
const KEEP = new Set(["assets", ".netlify", ".wrangler"]);
for (const e of readdirSync(OUT, { withFileTypes: true })) {
  if (KEEP.has(e.name)) continue;
  rmSync(join(OUT, e.name), { recursive: true, force: true });
}
mkdirSync(join(OUT, "assets"), { recursive: true });
copyFileSync(join(ROOT, "site/site.css"), join(OUT, "assets/site.css"));
if (existsSync(join(ROOT, "docs/assets/logo.png"))) { /* kept */ }

const htmlEscape = (s) => esc(s);

for (const p of pages) {
  const isFull = p.full || p.slug === "/";
  const body = expand(isFull ? p.html : `<div class="prose">${p.html}</div>`);
  emit(
    p.slug === "/" ? "index.html" : `${p.slug.replace(/^\/|\/$/g, "")}/index.html`,
    page({
      slug: p.slug,
      title: p.titleTag,
      description: p.description,
      body,
      sidebar: isFull ? null : sidebarFor(sidebarGroups.filter((g) => !g.onlyIn || g.onlyIn === p.group), p.slug),
      full: isFull,
      active: p.slug.startsWith("/setup") ? "/setup/" : p.slug.startsWith("/skills") ? "/skills/" : p.slug.startsWith("/ga4-mcp-for-") ? "/ga4-mcp-for-every-harness/" : p.slug.startsWith("/ga4-plugin") ? "/ga4-plugins/" : "",
      type: p.slug === "/" ? "SoftwareApplication" : "TechArticle",
    })
  );
}

for (const s of skills) {
  emit(
    `${s.slug.replace(/^\/|\/$/g, "")}/index.html`,
    page({
      slug: s.slug,
      title: `${s.title} — GA4 MCP skill`,
      description: s.description,
      body: `<div class="prose"><p class="eyebrow">Agent skill</p><h1>${esc(s.title)}</h1>${s.html}</div>`,
      sidebar: sidebarFor(sidebarGroups, s.slug),
      active: "/skills/",
    })
  );
}

// 404
emit(
  "404.html",
  page({
    slug: "/404/",
    title: "Page not found — GA4 MCP",
    description: "That page does not exist.",
    full: true,
    body: `<div class="nf"><p class="eyebrow">404</p><h1>That page does not exist.</h1><p>The GA4 MCP server has one install page, twelve client guides, and seventeen skills. Pick a door.</p><p><a class="btn btn--primary" href="/">Start here</a> <a class="btn btn--ghost" href="/setup/">Install</a></p></div>`,
  })
);

// sitemap
const urls = [...pages.map((p) => p.slug), ...skills.map((s) => s.slug)];
writeFileSync(
  join(OUT, "sitemap.xml"),
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls
    .map((u) => `  <url><loc>${htmlEscape(SITE + u)}</loc><lastmod>${UPDATED}</lastmod></url>`)
    .join("\n")}\n</urlset>\n`
);

writeFileSync(join(OUT, "robots.txt"), `User-agent: *\nAllow: /\n\nSitemap: ${SITE}/sitemap.xml\n`);

// Redirects: keep every URL the old site published, and the www + installer rules.
const GONE = [
  "ga4-plugin-for-harness", // never a valid manifest; OpenClaw registers servers via `openclaw mcp add`
];
const KEPT = pages.filter((p) => p.slug !== "/").map((p) => p.slug.replace(/^\/|\/$/g, ""));
const redirects = [
  "https://www.ga4mcp.com/*    https://ga4mcp.com/:splat    301!",
  "/install    https://ga4.builditwithai.xyz/?src=install  302",
  ...GONE.map((g) => `/${g}/*    /ga4-mcp-for-every-harness/    301!`),
  ...GONE.map((g) => `/${g}    /ga4-mcp-for-every-harness/    301!`),
  ...KEPT.flatMap((k) => [`/${k}.md    /${k}/    301!`, `/${k}/index.md    /${k}/    301!`]),
  "/index.md    /    301!",
  "/README.md    /    301!",
  ...skills.flatMap((s) => [`${s.slug}index.md    ${s.slug}    301!`]),
];
writeFileSync(join(OUT, "_redirects"), redirects.join("\n") + "\n");

// data files
mkdirSync(join(OUT, "data"), { recursive: true });
writeFileSync(
  join(OUT, "data/skills.json"),
  JSON.stringify({ generated: UPDATED, version: VERSION, count: skills.length, skills: skills.map((s) => ({ slug: s.name, title: s.title, description: s.description, url: `${SITE}${s.slug}` })) }, null, 2)
);
copyFileSync(join(ROOT, "site/data/tools.json"), join(OUT, "data/tools.json"));

// llms.txt
const tools = JSON.parse(readFileSync(join(ROOT, "site/data/tools.json"), "utf8"));
writeFileSync(
  join(OUT, "llms.txt"),
  `# GA4 MCP Server

> Model Context Protocol server for Google Analytics 4. Read-only reporting, schema discovery, and ${skills.length} analytical skills that load on demand. MIT, local stdio, v${VERSION}.

Docs: ${SITE}
Repo: https://github.com/surendranb/google-analytics-mcp
Not affiliated with Google.

## Install
- \`curl -fsSL ${SITE.replace("ga4mcp.com", "ga4.builditwithai.xyz")}/install | bash\`
- \`uvx google-analytics-mcp\`
- \`npx -y @surendranb/google-analytics-mcp\`

Requires \`GA4_PROPERTY_ID\` and \`GOOGLE_APPLICATION_CREDENTIALS\`.

## Tools (${tools.count})
${tools.tools.map((t) => `- \`${t.name}\`: ${t.summary || t.description}`).join("\n")}

## Skills (${skills.length})
${skills.map((s) => `- [${s.title}](${SITE}${s.slug}): ${s.description}`).join("\n")}

## Pages
${pages.map((p) => `- ${SITE}${p.slug} — ${p.title}`).join("\n")}
`
);

// llms-full.txt
writeFileSync(
  join(OUT, "llms-full.txt"),
  [
    `# GA4 MCP Server — full text`,
    `Version ${VERSION}, updated ${UPDATED}. ${SITE}`,
    "",
    ...pages.map((p) => `\n\n# ${p.title}\nURL: ${SITE}${p.slug}\n\n${p.raw}`),
    ...skills.map((s) => `\n\n# ${s.title} (skill: ${s.name})\nURL: ${SITE}${s.slug}\n\n${s.raw}`),
  ].join("\n")
);

console.log(`built ${pages.length} pages, ${skills.length} skills, ${urls.length} urls`);
