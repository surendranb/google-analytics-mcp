// Content negotiation + agent telemetry for ga4mcp.com.
//
//   Accept: text/markdown  -> the page's markdown twin (/setup/ -> /setup/index.md)
//   /llms.txt, /llms-full.txt, *.md, /data/*.json -> GA4 agent_asset_hit
//   non-browser HTML reads on content pages       -> GA4 agent_asset_hit
//
// Delivery first: every failure path (no twin, telemetry down, header mutation
// refused) falls through to the normal HTML response. Nothing here can 500 a page.
//
// Types are structural rather than imported from https://edge.netlify.com so the
// handler can be exercised in plain Node (site/tools/test-negotiate.mjs).

const GA_ID = "G-RX65PWDDEQ";
const ORIGIN = "https://ga4mcp.com";

type Headers = { get(name: string): string | null };
type Request = { url: string; headers: Headers };
type Context = {
  request: Request;
  next(): Promise<Response>;
  waitUntil?(promise: Promise<unknown>): void;
  ip?: string;
  geo?: { country?: { code?: string }; city?: string };
};

export function wantsMarkdown(accept: string | null): boolean {
  return !!accept && /text\/markdown/i.test(accept);
}

export function twinFor(pathname: string): string | null {
  if (pathname === "/") return "/index.md";
  if (pathname.endsWith("/") && !pathname.startsWith("/data/")) return pathname + "index.md";
  if (!pathname.includes(".") && !pathname.endsWith("/")) return pathname + "/index.md";
  return null;
}

export function classifyClient(ua: string): string {
  const s = (ua || "").toLowerCase();
  if (s.includes("curl") || s.includes("httpie") || s.includes("wget")) return "cli";
  if (/python|requests|urllib|aiohttp|httpx|node-fetch|axios|undici|go-http-client/.test(s)) return "script";
  if (/claude|anthropic|gpt|openai|oai-searchbot|perplexity|cursor|langchain|llama|agent|llm/.test(s)) return "agent";
  if (/bot|crawl|spider/.test(s)) return "crawler";
  if (/mozilla|chrome|safari|firefox|edg\//.test(s)) return "browser";
  return "other";
}

export function detectAgentFamily(ua: string): string {
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

function hash(value: string): string {
  let h = 0;
  for (let i = 0; i < value.length; i++) {
    h = ((h << 5) - h) + value.charCodeAt(i);
    h |= 0;
  }
  return String(Math.abs(h));
}

export async function sendGaHit(request: Request, context: Context, pathname: string, fileType: string,
                                fetchImpl: typeof fetch = fetch): Promise<void> {
  try {
    const headers = request.headers;
    const ua = headers.get("user-agent") || "unknown";
    const accept = headers.get("accept") || "*/*";
    const referer = headers.get("referer") || "";
    const ip = context.ip || headers.get("x-nf-client-connection-ip") || "anonymous";
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
      "ep.country_code": context.geo?.country?.code || "unknown",
      "ep.city": context.geo?.city || "unknown",
      "ep.accept_type": accept.slice(0, 100),
      dl: `${ORIGIN}${pathname}`,
      dr: referer,
    });
    await fetchImpl("https://www.google-analytics.com/g/collect?" + params.toString(), {
      method: "POST",
      headers: { "user-agent": ua, "x-forwarded-for": ip },
    });
  } catch {
    // Telemetry must never degrade delivery.
  }
}

function markdownResponse(body: string | null, htmlPath: string): Response {
  const headers = new Headers({
    "content-type": "text/markdown; charset=utf-8",
    "x-robots-tag": "noindex",
    link: `<${ORIGIN}${htmlPath}>; rel="canonical"`,
    vary: "Accept",
  });
  return new Response(body, { status: 200, headers });
}

export default async function handler(request: Request, context: Context): Promise<Response> {
  let url: URL;
  try {
    url = new URL(request.url);
  } catch {
    return context.next();
  }
  const pathname = url.pathname;
  const accept = request.headers.get("accept");

  // Internal twin fetch (below) re-enters this function. Pass it straight through:
  // one hop, no double telemetry, no recursion.
  if (request.headers.get("x-ga4mcp-internal")) {
    return context.next();
  }

  try {
    // 1. Content negotiation: serve the twin when the client asks for markdown.
    if (wantsMarkdown(accept)) {
      const twin = twinFor(pathname);
      if (twin) {
        const twinResponse = await fetch(`${url.origin}${twin}`, {
          headers: { "x-ga4mcp-internal": "1", accept: "text/markdown" },
        });
        if (twinResponse.ok) {
          const body = await twinResponse.text();
          if (body.trim().length > 0) {
            if (context.waitUntil) {
              context.waitUntil(sendGaHit(request, context, twin, "markdown"));
            }
            return markdownResponse(body, pathname);
          }
        }
      }
    }

    // 2. Track the machine surfaces, whatever the Accept header says.
    let fileType: string | null = null;
    if (pathname === "/llms.txt" || pathname === "/llms-full.txt") fileType = "llms.txt";
    else if (pathname.endsWith(".md")) fileType = "markdown";
    else if (pathname.startsWith("/data/") && pathname.endsWith(".json")) fileType = "json";
    else if (pathname === "/sitemap.xml" || pathname === "/robots.txt") fileType = "discovery";

    // 3. Agents do not run gtag, so their HTML reads would otherwise be invisible.
    //    Browsers are skipped; gtag covers them.
    if (!fileType && !pathname.startsWith("/assets/") && !pathname.includes(".")
        && classifyClient(request.headers.get("user-agent") || "") !== "browser") {
      fileType = "html";
    }

    if (fileType && context.waitUntil) {
      context.waitUntil(sendGaHit(request, context, pathname, fileType));
    }
  } catch {
    // fall through to normal delivery
  }

  const response = await context.next();
  try {
    response.headers.set("Vary", "Accept");
  } catch {
    // Some runtimes hand back immutable headers; delivery still wins.
  }
  return response;
}
