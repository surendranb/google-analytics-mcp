// Logic tests for netlify/edge-functions/negotiate.ts — no Deno, no Netlify account.
//
//   node site/tools/test-negotiate.mjs
//
// Node 22.6+ strips the TypeScript types on import; the handler's pure helpers
// and its request/response flow are exercised against a stubbed context, so the
// two things that matter get checked: markdown negotiation returns the twin with
// the right headers, and every failure path still delivers HTML.

import assert from "node:assert/strict";

const mod = await import("../../netlify/edge-functions/negotiate.ts");
const handler = mod.default;

const HTML = "<!doctype html><html><body><h1>Setup</h1></body></html>";
const MARKDOWN = "---\ntitle: Setup\n---\n\n# Setup\n\nbody\n";

function makeRequest(path, headers = {}) {
  return { url: `https://ga4mcp.com${path}`, headers: new Headers(headers) };
}

function makeContext(request, { twinExists = true, hits = [] } = {}) {
  return {
    request,
    ip: "203.0.113.9",
    geo: { country: { code: "IN" }, city: "Chennai" },
    waitUntil: (promise) => hits.push(promise),
    next: async () => new Response(HTML, { status: 200, headers: { "content-type": "text/html" } }),
    __hits: hits,
    __twinExists: twinExists,
  };
}

// The handler reaches for the twin through global fetch; stub it per test.
function stubFetch({ twinExists = true, telemetry = "ok", calls = [] } = {}) {
  globalThis.fetch = async (url, init = {}) => {
    calls.push({ url: String(url), init });
    if (String(url).includes("google-analytics.com")) {
      if (telemetry === "throw") throw new Error("GA4 unreachable");
      return new Response(null, { status: 204 });
    }
    if (String(url).includes("x-ga4mcp-internal") || init.headers?.["x-ga4mcp-internal"]) {
      return twinExists ? new Response(MARKDOWN, { status: 200 }) : new Response("not found", { status: 404 });
    }
    return new Response(MARKDOWN, { status: 200 });
  };
  return calls;
}

const results = [];
async function check(name, fn) {
  try {
    await fn();
    results.push(`ok   ${name}`);
  } catch (error) {
    results.push(`FAIL ${name}: ${error.message}`);
    process.exitCode = 1;
  }
}

await check("helpers: twinFor maps content URLs and refuses files", () => {
  assert.equal(mod.twinFor("/"), "/index.md");
  assert.equal(mod.twinFor("/setup/"), "/setup/index.md");
  assert.equal(mod.twinFor("/skills/traffic-diagnosis/"), "/skills/traffic-diagnosis/index.md");
  assert.equal(mod.twinFor("/setup"), "/setup/index.md");
  assert.equal(mod.twinFor("/index.md"), null);
  assert.equal(mod.twinFor("/data/tools.json"), null);
  assert.equal(mod.twinFor("/privacy/"), "/privacy/index.md");
});

await check("helpers: client + agent classification", () => {
  assert.equal(mod.classifyClient("claude-ai/1.0"), "agent");
  assert.equal(mod.classifyClient("Mozilla/5.0 (Macintosh) Chrome/140"), "browser");
  assert.equal(mod.classifyClient("curl/8.7.1"), "cli");
  assert.equal(mod.classifyClient("GPTBot/1.2"), "agent");
  assert.equal(mod.detectAgentFamily("Mozilla/5.0 (compatible; GPTBot/1.2)"), "ChatGPT / OpenAI");
  assert.equal(mod.detectAgentFamily("curl/8.7.1"), "cURL");
});

await check("accept: text/markdown returns the twin with noindex + canonical", async () => {
  stubFetch();
  const request = makeRequest("/setup/", { accept: "text/markdown", "user-agent": "claude-ai/1.0" });
  const response = await handler(request, makeContext(request));
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("content-type"), "text/markdown; charset=utf-8");
  assert.equal(response.headers.get("x-robots-tag"), "noindex");
  assert.equal(response.headers.get("link"), '<https://ga4mcp.com/setup/>; rel="canonical"');
  assert.equal(response.headers.get("vary"), "Accept");
  assert.equal(await response.text(), MARKDOWN);
});

await check("browser reading HTML is passed through with Vary: Accept", async () => {
  stubFetch();
  const request = makeRequest("/setup/", {
    accept: "text/html,application/xhtml+xml", "user-agent": "Mozilla/5.0 (Macintosh) Safari/605",
  });
  const context = makeContext(request);
  const response = await handler(request, context);
  assert.equal(await response.text(), HTML);
  assert.equal(response.headers.get("vary"), "Accept");
  assert.equal(context.__hits.length, 0, "browser hits are gtag's job, not the edge function's");
});

await check("missing twin falls back to HTML even when markdown is asked for", async () => {
  stubFetch({ twinExists: false });
  const request = makeRequest("/privacy/", { accept: "text/markdown", "user-agent": "claude-ai/1.0" });
  const context = makeContext(request, { twinExists: false });
  const response = await handler(request, context);
  assert.equal(await response.text(), HTML);
});

await check("llms.txt and data JSON queue a telemetry hit", async () => {
  stubFetch();
  const request = makeRequest("/llms.txt", { "user-agent": "GPTBot/1.2" });
  const context = makeContext(request);
  await handler(request, context);
  const request2 = makeRequest("/data/tools.json", { "user-agent": "python-requests/2.32" });
  await handler(request2, makeContext(request2, { hits: context.__hits }));
  assert.equal(context.__hits.length, 2);
});

await check("non-browser HTML read is counted, browser is not", async () => {
  stubFetch();
  const agent = makeRequest("/", { "user-agent": "claude-ai/1.0" });
  const ctxAgent = makeContext(agent);
  await handler(agent, ctxAgent);
  assert.equal(ctxAgent.__hits.length, 1);
  const asset = makeRequest("/assets/style.css", { "user-agent": "claude-ai/1.0" });
  const ctxAsset = makeContext(asset);
  await handler(asset, ctxAsset);
  assert.equal(ctxAsset.__hits.length, 0, "static assets are not page reads");
});

await check("telemetry failure never breaks delivery", async () => {
  stubFetch({ telemetry: "throw" });
  const request = makeRequest("/llms.txt", { "user-agent": "curl/8.7.1" });
  const context = makeContext(request);
  const response = await handler(request, context, );
  assert.equal(response.status, 200);
  await Promise.all(context.__hits); // waitUntil promises must swallow their own errors
});

await check("internal twin fetch passes straight through", async () => {
  const calls = stubFetch();
  const request = makeRequest("/setup/index.md", { accept: "text/markdown", "x-ga4mcp-internal": "1" });
  const context = makeContext(request);
  const response = await handler(request, context);
  assert.equal(await response.text(), HTML);
  assert.equal(context.__hits.length, 0);
  assert.equal(calls.length, 0, "no twin lookup and no telemetry for the internal hop");
});

console.log(results.join("\n"));
console.log(process.exitCode ? "\nFAILED" : `\n${results.length} checks passed`);
