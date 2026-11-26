#!/usr/bin/env node
// Fails the run when the live site does not serve the release we just built.
// A green workflow that shipped nothing is the failure this guards against.
import { readFileSync } from "node:fs";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const fail = (m) => {
  console.error(`::error::${m}`);
  process.exit(1);
};

const version = readFileSync("pyproject.toml", "utf8").match(/^version = "(.+)"/m)?.[1];
if (!version) fail("pyproject.toml has no version line");

const srcTitle = readFileSync("site/content/index.md", "utf8").match(/^title: "(.+)"/m)?.[1];
if (!srcTitle) fail("site/content/index.md has no title line");

const unesc = (s) =>
  s.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'");

const urls = ["https://ga4mcp.com/", "https://www.ga4mcp.com/"];
if (process.env.DEPLOY_URL) urls.unshift(`${process.env.DEPLOY_URL}/`);

const result = {};
let ok = false;
for (let attempt = 1; attempt <= 12 && !ok; attempt++) {
  ok = true;
  for (const base of urls) {
    try {
      const res = await fetch(`${base}?deploy-check=${version}-${attempt}`, { headers: { "cache-control": "no-cache" } });
      const body = await res.text();
      const title = unesc(body.match(/<title>([^<]*)<\/title>/)?.[1] || "");
      result[base] = { status: res.status, title, hasVersion: body.includes(`v${version}`) };
      if (res.status !== 200 || title !== srcTitle || !body.includes(`v${version}`)) ok = false;
    } catch (e) {
      result[base] = { error: String(e.message || e) };
      ok = false;
    }
  }
  if (!ok) await sleep(5000);
}

console.log(JSON.stringify(result, null, 2));
if (!ok) fail(`live site does not serve release v${version} with title "${srcTitle}" after 12 attempts`);
console.log(`live ok: v${version} on ${urls.join(", ")}`);
