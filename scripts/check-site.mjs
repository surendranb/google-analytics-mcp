#!/usr/bin/env node
// Verifies the built site: links, headings, metadata, stale copy, word counts.
import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const DOCS = process.env.DOCS_DIR || new URL("../docs", import.meta.url).pathname;
const problems = [];
const warn = [];
const rows = [];

function walk(dir) {
  const out = [];
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) out.push(...walk(p));
    else if (e.name.endsWith(".html")) out.push(p);
  }
  return out;
}

const files = walk(DOCS);
const titles = new Map();
const descs = new Map();

const BANNED = [
  ["v2.11.4", "stale version label"],
  ["2.11.5", "stale version label"],
  ["2026-10-09", "stale verification date"],
  ["Proof strip", "internal QA artefact"],
  ["Breadcrumb", "internal QA artefact"],
  ["verified 2026", "internal QA artefact"],
  ["verified today", "internal QA artefact"],
  ["Instruct the user", "agent-voice copy"],
  ["DO NOT GUESS", "agent-voice copy"],
  ["Tell the user", "agent-voice copy"],
  ["the user must", "agent-voice copy"],
  ["seamlessly", "banned word"],
  ["bridges the gap", "banned phrase"],
  ["incredibly", "banned word"],
  ["leverage", "banned word"],
  ["utilize", "banned word"],
  ["robust", "banned word"],
  ["comprehensive", "banned word"],
  ["streamline", "banned word"],
  ["seamless", "banned word"],
];

for (const f of files) {
  const html = readFileSync(f, "utf8");
  const rel = "/" + relative(DOCS, f).replace(/(^|\/)index\.html$/, "").replace(/index\.html$/, "");
  const url = rel === "/" ? "/" : rel;

  const title = (html.match(/<title>([^<]*)<\/title>/) || [])[1] || "";
  const desc = (html.match(/<meta name="description" content="([^"]*)"/) || [])[1] || "";
  const canon = (html.match(/<link rel="canonical" href="([^"]*)"/) || [])[1] || "";
  const h1s = [...html.matchAll(/<h1[^>]*>([\s\S]*?)<\/h1>/g)].map((m) => m[1].replace(/<[^>]+>/g, "").trim());
  const text = html
    .replace(/<script[\s\S]*?<\/script>/g, " ")
    .replace(/<style[\s\S]*?<\/style>/g, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&[a-z]+;/g, " ")
    .split(/\s+/)
    .filter(Boolean);
  const words = text.length;

  if (!title) problems.push(`${url}: missing <title>`);
  if (!desc) problems.push(`${url}: missing meta description`);
  if (!canon) problems.push(`${url}: missing canonical`);
  else if (!canon.startsWith("https://ga4mcp.com")) problems.push(`${url}: canonical not absolute — ${canon}`);
  if (h1s.length !== 1) problems.push(`${url}: ${h1s.length} h1 elements`);
  if (title.length > 62) warn.push(`${url}: title ${title.length} chars (${title})`);
  if (desc.length > 165) warn.push(`${url}: description ${desc.length} chars`);
  // A thin page is the signature of a client-rendered shell: 200, plausible
  // byte count, nothing a human can read. Fail, do not warn.
  if (words < 120 && !url.includes("404")) problems.push(`${url}: only ${words} words of visible text — client-rendered shell?`);

  // Placeholder strings that mean the page never resolved.
  for (const ph of ["Loading GA4 MCP Docs", 'id="app">Loading', "Loading..."]) {
    if (html.includes(ph)) problems.push(`${url}: placeholder text "${ph}" — page never resolved`);
  }

  // A page must carry its own text in the HTML. If it only holds a script and
  // a mount point, a fetch can never prove it works.
  const bodyText = html.replace(/<script[\s\S]*?<\/script>/g, "").replace(/<[^>]+>/g, " ").split(/\s+/).filter(Boolean).length;
  if (bodyText < 80 && !url.includes("404")) problems.push(`${url}: ${bodyText} words outside <script> — content depends on the client`);

  if (titles.has(title)) problems.push(`${url}: duplicate title with ${titles.get(title)}`);
  titles.set(title, url);
  if (descs.has(desc) && desc) problems.push(`${url}: duplicate description with ${descs.get(desc)}`);
  descs.set(desc, url);

  for (const [needle, why] of BANNED) {
    if (html.includes(needle)) problems.push(`${url}: ${why} — "${needle}"`);
  }

  // internal links resolve
  for (const m of html.matchAll(/href="(\/[^"#?]*)"/g)) {
    const href = m[1];
    if (href.startsWith("//")) continue;
    const target = href.endsWith("/") ? join(DOCS, href, "index.html") : join(DOCS, href);
    const alt = join(DOCS, href, "index.html");
    if (!existsSync(target) && !existsSync(alt)) problems.push(`${url}: broken link ${href}`);
  }

  rows.push({ url, title, words });
}

// raw files that must exist
for (const f of ["robots.txt", "sitemap.xml", "llms.txt", "llms-full.txt", "404.html", "data/tools.json", "data/skills.json", "_redirects", "assets/site.css"]) {
  if (!existsSync(join(DOCS, f))) problems.push(`missing artefact: ${f}`);
}

// sitemap matches pages on disk
const sitemap = readFileSync(join(DOCS, "sitemap.xml"), "utf8");
const norm = (u) => (u.replace("https://ga4mcp.com", "").replace(/\/$/, "") || "/");
const locs = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => norm(m[1]));
const onDisk = rows.map((r) => norm(r.url)).filter((u) => u !== "/404.html" && u !== "/404");
for (const u of onDisk) if (!locs.includes(u)) problems.push(`sitemap missing ${u}`);
for (const u of locs) if (!onDisk.includes(u)) problems.push(`sitemap lists unknown ${u}`);

// machine files parse
try { JSON.parse(readFileSync(join(DOCS, "data/tools.json"), "utf8")); } catch { problems.push("tools.json is not valid JSON"); }
try { JSON.parse(readFileSync(join(DOCS, "data/skills.json"), "utf8")); } catch { problems.push("skills.json is not valid JSON"); }

rows.sort((a, b) => a.words - b.words);
console.log(`pages: ${rows.length}`);
console.log(`thinnest: ${rows.slice(0, 3).map((r) => `${r.url} ${r.words}w`).join(", ")}`);
console.log(`median words: ${rows[Math.floor(rows.length / 2)].words}`);
console.log(`\nPROBLEMS (${problems.length})`);
for (const p of [...new Set(problems)]) console.log("  ✗ " + p);
if (warn.length) {
  console.log(`\nWARNINGS (${warn.length})`);
  for (const w of warn.slice(0, 15)) console.log("  · " + w);
}
process.exit(problems.length ? 1 : 0);
