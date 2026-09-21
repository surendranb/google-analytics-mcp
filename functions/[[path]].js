// Content negotiation & server-side GA4 telemetry for ga4mcp.com on Cloudflare Pages.
//
// Ported from the Netlify edge function (netlify/edge-functions/negotiate.ts) to the
// Pages Functions shape proven on free-inference:
//   Accept: text/markdown                          -> the page's markdown twin (/setup/ -> /setup/index.md)
//   /llms.txt, /llms-full.txt, *.md, /data/*.json  -> GA4 agent_asset_hit
//   non-browser HTML reads                         -> GA4 agent_asset_hit
//
// Delivery first: every failure path (no twin, telemetry down) falls through to the
// normal static response. Nothing here can break a page.

const GA_ID = "G-RX65PWDDEQ";
const ORIGIN = "https://ga4mcp.com";

function wantsMarkdown(accept) {
  return !!accept && /text\/markdown/i.test(accept);
}

function twinFor(pathname) {
  if (pathname === "/") return "/index.md";
  if (pathname.endsWith("/") && !pathname.startsWith("/data/")) return pathname + "index.md";
  if (!pathname.includes(".") && !pathname.endsWith("/")) return pathname + "/index.md";
  return null;
}

function classifyClient(ua) {
  const s = (ua || "").toLowerCase();
  if (s.includes("curl") || s.includes("httpie") || s.includes("wget")) return "cli";
  if (/python|requests|urllib|aiohttp|httpx|node-fetch|axios|undici|go-http-client/.test(s)) return "script";
  if (/claude|anthropic|gpt|openai|oai-searchbot|perplexity|cursor|langchain|llama|agent|llm/.test(s)) return "agent";
  if (/bot|crawl|spider/.test(s)) return "crawler";
  if (/mozilla|chrome|safari|firefox|edg\//.test(s)) return "browser";
  return "other";
}

function detectAgentFamily(ua) {
  const s = (ua || "").toLowerCase();
  if (s.includes("claude") || s.includes("anthropic")) return "Claude / Anthropic";
  if (/chatgpt|gptbot|openai|oai-searchbot/.test(s)) return "ChatGPT / OpenAI";
  if (s.includes("perplexity")) return "Perplexity";
  if (s.includes("cursor")) return "Cursor";
  if (/google-extended|gemini|googlebot/.test(s)) return "Google";
  if (s.includes("langchain")) return "LangChain";
  if (s.includes("llamaindex")) return "LlamaIndex";
  if (/python|requests|httpx|urllib|aiohttp/.test(s)) return "Python Script";
  if (s.includes("curl")) return "cURL";
  if (s.includes("httpie")) return "HTTPie";
  if (s.includes("wget")) return "Wget";
  if (/node-fetch|axios|undici|go-http-client/.test(s)) return "Backend HTTP Client";
  if (/bingbot|duckduckbot|yandex|slurp|applebot/.test(s)) return "Search Crawler";
  if (/mozilla|chrome|safari|firefox/.test(s)) return "Browser";
  return "Custom / Unnamed Client";
}

function hash(value) {
  let h = 0;
  for (let i = 0; i < value.length; i++) {
    h = ((h << 5) - h) + value.charCodeAt(i);
    h |= 0;
  }
  return String(Math.abs(h));
}

async function sendGaHit(req, pathname, fileType) {
  try {
    const ua = req.headers.get("user-agent") || "unknown";
    const accept = req.headers.get("accept") || "*/*";
    const referer = req.headers.get("referer") || "";
    const ip = req.headers.get("cf-connecting-ip") || "anonymous";
    const cf = req.cf || {};
    const params = new URLSearchParams({
      v: "2",
      tid: GA_ID,
      cid: hash(ip + ua),
      en: "agent_asset_hit",
      uip: ip,
      ua,
      "ep.path": pathname,
      "ep.file_type": fileType,
      "ep.agent_name": detectAgentFamily(ua),
      "ep.client_type": classifyClient(ua),
      "ep.user_agent": ua.slice(0, 100),
      "ep.country_code": req.headers.get("cf-ipcountry") || cf.country || "unknown",
      "ep.city": cf.city || "unknown",
      "ep.asn_org": String(cf.asOrganization || "unknown").slice(0, 100),
      "ep.accept_type": accept.slice(0, 100),
      dl: ORIGIN + pathname,
      dr: referer,
    });
    await fetch("https://www.google-analytics.com/g/collect?" + params.toString(), {
      method: "POST",
      headers: { "user-agent": ua, "x-forwarded-for": ip },
    });
  } catch (e) {
    // Telemetry must never degrade delivery.
  }
}

export async function onRequest(context) {
  const req = context.request;
  let url;
  try {
    url = new URL(req.url);
  } catch (e) {
    return context.next();
  }
  const pathname = url.pathname;
  const accept = req.headers.get("accept");

  try {
    // 1. Content negotiation: serve the markdown twin when the client asks for it.
    if (wantsMarkdown(accept)) {
      const twin = twinFor(pathname);
      if (twin) {
        const twinRes = await context.env.ASSETS.fetch(new URL(twin, req.url));
        if (twinRes.ok) {
          const body = await twinRes.text();
          if (body.trim().length > 0) {
            if (context.waitUntil) {
              context.waitUntil(sendGaHit(req, twin, "markdown"));
            }
            return new Response(body, {
              status: 200,
              headers: {
                "content-type": "text/markdown; charset=utf-8",
                "x-robots-tag": "noindex",
                "link": `<${ORIGIN}${pathname}>; rel="canonical"`,
                "vary": "Accept",
              },
            });
          }
        }
        // No twin for this path (e.g. /privacy/): fall through to the HTML page.
      }
    }

    // 2. Track the machine surfaces, whatever the Accept header says.
    let fileType = null;
    if (pathname === "/llms.txt" || pathname === "/llms-full.txt") fileType = "llms.txt";
    else if (pathname.endsWith(".md")) fileType = "markdown";
    else if (pathname.startsWith("/data/") && pathname.endsWith(".json")) fileType = "json";
    else if (pathname === "/sitemap.xml" || pathname === "/robots.txt") fileType = "discovery";

    // 3. Agents do not run gtag, so their HTML reads would otherwise be invisible.
    //    Browsers are skipped; gtag covers them.
    if (!fileType && !pathname.startsWith("/assets/") && !pathname.includes(".")
        && classifyClient(req.headers.get("user-agent") || "") !== "browser") {
      fileType = "html";
    }

    if (fileType && context.waitUntil) {
      context.waitUntil(sendGaHit(req, pathname, fileType));
    }
  } catch (e) {
    // fall through to normal delivery
  }

  const res = await context.next();
  try {
    res.headers.set("Vary", "Accept");
  } catch (e) {
    // Some responses hand back immutable headers; delivery still wins.
  }
  return res;
}
