#!/usr/bin/env node
// Fails the deploy when the freshly built docs/ does not carry the repo's own title and version.
import { readFileSync, existsSync } from "node:fs";

const fail = (m) => {
  console.error(`::error::${m}`);
  process.exit(1);
};

const version = readFileSync("pyproject.toml", "utf8").match(/^version = "(.+)"/m)?.[1];
if (!version) fail("pyproject.toml has no version line");

const srcTitle = readFileSync("site/content/index.md", "utf8").match(/^title: "(.+)"/m)?.[1];
if (!srcTitle) fail("site/content/index.md has no title line");

if (!existsSync("docs/index.html")) fail("docs/index.html was not built");

const unesc = (s) =>
  s.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'");

const html = readFileSync("docs/index.html", "utf8");
const builtTitle = html.match(/<title>([^<]*)<\/title>/)?.[1];
if (!builtTitle) fail("docs/index.html has no <title>");
if (unesc(builtTitle) !== srcTitle)
  fail(`built title does not match the repo title\n  source: ${srcTitle}\n  built:  ${unesc(builtTitle)}`);

const checked = [];
for (const f of ["docs/index.html", "docs/llms.txt"]) {
  if (!existsSync(f)) fail(`${f} missing from build output`);
  if (!readFileSync(f, "utf8").includes(`v${version}`) && !readFileSync(f, "utf8").includes(version))
    fail(`${f} does not mention release version ${version}`);
  if (readFileSync(f, "utf8").includes("v2.11.9")) fail(`${f} still carries the stale 2.11.9 build`);
  checked.push(f);
}

console.log(`built release ok: title=${srcTitle} version=${version} files=${checked.join(",")}`);
