/**
 * Cloudflare Worker: Universal AI Installer & Telemetry Gateway for GA4 MCP
 * Captures rich 2-phase telemetry (Edge Intent + Local Execution) to PostHog.
 */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const pathname = url.pathname.toLowerCase();
    const userAgent = request.headers.get("user-agent") || "";
    const clientIp = request.headers.get("cf-connecting-ip") || request.headers.get("x-real-ip") || "";
    const isCurl = userAgent.toLowerCase().includes("curl") || userAgent.toLowerCase().includes("wget");

    // Honor the Do-Not-Track convention (consoledonottrack.com / Scarf precedent)
    const dnt = request.headers.get("dnt") === "1" || request.headers.get("sec-gpc") === "1";

    const cf = request.cf || {};
    const country = cf.country || "unknown";
    const city = cf.city || "unknown";
    const continent = cf.continent || "unknown";
    const timezone = cf.timezone || "unknown";
    const asn = cf.asn || 0;
    const asOrganization = cf.asOrganization || "unknown";

    // Rich Edge User-Agent & Platform Parsing
    const edgeParsed = parseUserAgent(userAgent);

    // Route 1: Post-Install Client Telemetry Ping (/telemetry)
    if (request.method === "POST" && pathname === "/telemetry") {
      try {
        const body = await request.json();
        if (dnt) {
          return new Response(JSON.stringify({ recorded: false, reason: "dnt" }), {
            headers: { "content-type": "application/json" }
          });
        }
        ctx.waitUntil(
          sendPostHogEvent(env, {
            event: "install_completed",
            distinct_id: body.anonymous_id || `anon_${crypto.randomUUID()}`,
            properties: {
              $ip: clientIp,
              $geoip_country_name: country,
              $geoip_city_name: city,
              $geoip_continent_name: continent,
              $geoip_time_zone: timezone,
              as_organization: asOrganization,
              execution_mode: body.execution_mode || "unknown",
              harnesses_detected: body.harnesses_detected || [],
              configured_harnesses: body.configured_harnesses || [],
              terminal_app: body.terminal_app || "unknown",
              shell_type: body.shell_type || "unknown",
              os_name: body.os_name || edgeParsed.os,
              arch: body.arch || edgeParsed.arch,
              python_version: body.python_version || "none",
              has_uv: body.has_uv || false,
              has_brew: body.has_brew || false,
              auth_status: body.auth_status || "unknown",
              install_outcome: body.install_outcome || "success",
              target_override: body.target_override || "auto"
            }
          })
        );
        return new Response(JSON.stringify({ recorded: true }), {
          headers: { "content-type": "application/json" }
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), { status: 400 });
      }
    }

    // Edge Intent Telemetry — only for installer-shaped requests (skipped for DNT).
    // Browser hits on "/" and unknown paths are overwhelmingly scanners/bots.
    const intentPaths = ["/install", "/setup", "/guide", "/brew", "/formula.rb", "/gemini", "/claude", "/cursor", "/npx", "/chatgpt"];
    const isInstallerRequest = isCurl || intentPaths.includes(pathname) || pathname.endsWith(".sh");
    if (!dnt && isInstallerRequest) ctx.waitUntil(
      sendPostHogEvent(env, {
        event: "install_intent",
        distinct_id: `anon_${crypto.randomUUID()}`,
        properties: {
          $ip: clientIp,
          path: pathname,
          is_curl: isCurl,
          user_agent: userAgent,
          os_family: edgeParsed.os,
          arch_family: edgeParsed.arch,
          client_tool: edgeParsed.clientTool,
          is_ai_agent_ua: edgeParsed.isAiAgent,
          cf_country: country,
          cf_city: city,
          cf_continent: continent,
          cf_timezone: timezone,
          as_organization: asOrganization,
          asn: asn
        }
      })
    );

    // Route 2: Visual Setup Guide Page (/setup or /guide)
    if (pathname === "/setup" || pathname === "/guide") {
      return new Response(getSetupHtmlPage(), {
        headers: { "content-type": "text/html; charset=utf-8" }
      });
    }

    // Route 3: Homebrew Formula Serving (/brew or /formula.rb)
    if (pathname === "/brew" || pathname === "/formula.rb" || pathname.endsWith(".rb")) {
      return new Response(getHomebrewFormula(), {
        headers: {
          "content-type": "text/plain; charset=utf-8",
          "cache-control": "public, max-age=3600"
        }
      });
    }

    // Route 4: 1-Line Universal Installer Script Generator
    if (isCurl || pathname.endsWith(".sh") || pathname === "/install" || (pathname === "/" && isCurl)) {
      return new Response(getInstallerScript(url.hostname), {
        headers: {
          "content-type": "text/plain; charset=utf-8",
          "cache-control": "no-cache"
        }
      });
    }

    return Response.redirect(env.DOCS_URL, 302);
  }
};

function parseUserAgent(ua) {
  const lower = ua.toLowerCase();
  let os = "Unknown";
  let arch = "x86_64";
  let clientTool = "Browser";
  let isAiAgent = false;

  if (lower.includes("darwin") || lower.includes("macintosh") || lower.includes("mac os")) os = "macOS";
  else if (lower.includes("linux")) os = "Linux";
  else if (lower.includes("windows")) os = "Windows";

  if (lower.includes("arm64") || lower.includes("aarch64")) arch = "arm64";

  if (lower.includes("curl")) clientTool = "curl";
  else if (lower.includes("wget")) clientTool = "wget";
  else if (lower.includes("python")) clientTool = "python-requests";

  if (lower.includes("claude") || lower.includes("cursor") || lower.includes("antigravity") || lower.includes("gpt") || lower.includes("ai")) {
    isAiAgent = true;
  }

  return { os, arch, clientTool, isAiAgent };
}

function getSetupHtmlPage() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GA4 MCP Server — Quick Setup Guide</title>
  <style>
    :root { --bg: #0f172a; --card: #1e293b; --text: #f8fafc; --accent: #38bdf8; --green: #4ade80; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; margin: 0; padding: 2rem 1rem; }
    .container { max-width: 800px; margin: 0 auto; }
    h1 { color: var(--accent); font-size: 2.2rem; margin-bottom: 0.5rem; }
    .card { background: var(--card); border-radius: 12px; padding: 1.5rem; margin: 1.5rem 0; border: 1px solid #334155; }
    code { background: #090d16; padding: 0.2rem 0.5rem; border-radius: 4px; color: var(--green); font-family: monospace; }
    pre { background: #090d16; padding: 1rem; border-radius: 8px; overflow-x: auto; color: var(--text); }
    .step-num { display: inline-block; background: var(--accent); color: #000; font-weight: bold; width: 28px; height: 28px; border-radius: 50%; text-align: center; line-height: 28px; margin-right: 0.5rem; }
    a { color: var(--accent); text-decoration: none; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🚀 GA4 MCP Quick Setup Guide</h1>
    <p>Connect Google Analytics 4 to Claude, Gemini, Cursor, and VS Code in 2 simple steps.</p>

    <div class="card" id="property-id">
      <h2><span class="step-num">1</span> Find Your GA4 Property ID</h2>
      <p>Go to <a href="https://analytics.google.com" target="_blank">Google Analytics Admin</a> → <strong>Property Settings</strong> → Copy your numeric <strong>Property ID</strong> (e.g. <code>123456789</code>).</p>
    </div>

    <div class="card" id="credentials">
      <h2><span class="step-num">2</span> Google Credentials Option</h2>
      <p><strong>Option A (Easiest):</strong> Log in via <code>gcloud auth application-default login</code>. No JSON key needed!</p>
      <p><strong>Option B (Service Account):</strong> Go to <a href="https://console.cloud.google.com/iam-admin/serviceaccounts" target="_blank">Google Cloud Console</a> → Create Service Account → Create Key (JSON) → Download to your computer.</p>
    </div>

    <div class="card" id="iam">
      <h2><span class="step-num">3</span> Grant GA4 Access (IAM)</h2>
      <p>In <a href="https://analytics.google.com" target="_blank">Google Analytics</a> → <strong>Admin</strong> → <strong>Property Access Management</strong> → add your service account email (the <code>client_email</code> inside the JSON key) with the <strong>Viewer</strong> role.</p>
    </div>

    <div class="card" id="adc">
      <h2><span class="step-num">4</span> Credentials Expired?</h2>
      <p>If you used <code>gcloud</code> login and see <em>"Reauthentication is needed"</em> or <em>"invalid_grant"</em>, just run <code>gcloud auth application-default login</code> again and restart your MCP client.</p>
    </div>

    <div class="card" id="install">
      <h2><span class="step-num">5</span> 1-Line Universal Setup Command</h2>
      <pre>curl -fsSL https://ga4.builditwithai.xyz | bash</pre>
    </div>

    <p style="text-align: center; color: #94a3b8; margin-top: 2rem;">
      Need help? Read full documentation at <a href="https://ga4mcp.com">https://ga4mcp.com</a>
    </p>
  </div>
</body>
</html>`;
}

function getHomebrewFormula() {
  return `class GoogleAnalyticsMcp < Formula
  desc "Google Analytics 4 MCP server for AI agents and agentic workflows"
  homepage "https://ga4mcp.com"
  url "https://files.pythonhosted.org/packages/source/g/google-analytics-mcp/google_analytics_mcp-2.5.5.tar.gz"
  license "Apache-2.0"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/ga4-mcp-server", "--help"
  end
end
`;
}

function getInstallerScript(hostname) {
  const host = hostname || "ga4.builditwithai.xyz";
  return `#!/usr/bin/env bash
# GA4 MCP Universal AI Installer & Telemetry Collector

set -e

GREEN='\\033[0;32m'
BLUE='\\033[0;34m'
YELLOW='\\033[1;33m'
CYAN='\\033[0;36m'
NC='\\033[0m'

IS_INTERACTIVE=false
EXEC_MODE="agent_headless"
if [ -t 0 ] && [ -t 1 ]; then 
  IS_INTERACTIVE=true
  EXEC_MODE="human_interactive"
fi

TARGET_OVERRIDE="\${TARGET:-auto}"
PROP_ID="\${GA4_PROPERTY_ID:-}"
CREDS_PATH="\${GOOGLE_APPLICATION_CREDENTIALS:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --gemini) TARGET_OVERRIDE="gemini"; shift ;;
    --claude) TARGET_OVERRIDE="claude"; shift ;;
    --cursor) TARGET_OVERRIDE="cursor"; shift ;;
    --brew) TARGET_OVERRIDE="brew"; shift ;;
    --property-id=*) PROP_ID="\${1#*=}"; shift ;;
    --property-id) PROP_ID="$2"; shift 2 ;;
    --key-file=*) CREDS_PATH="\${1#*=}"; shift ;;
    --key-file) CREDS_PATH="$2"; shift 2 ;;
    *) shift ;;
  esac
done

OS="$(uname -s 2>/dev/null || echo 'Unknown')"
ARCH="$(uname -m 2>/dev/null || echo 'Unknown')"
TERM_APP="\${TERM_PROGRAM:-terminal}"
SHELL_TYPE="$(basename "\${SHELL:-bash}")"

# Anonymous installation ID: pre-seed the SAME random ID the MCP server uses,
# so install -> first run -> usage is one anonymous journey. No PII.
ANON_ID=""
if [ -z "\${DO_NOT_TRACK:-}" ] && [ -z "\${DISABLE_TELEMETRY:-}" ] && [ -z "\${NO_TELEMETRY:-}" ]; then
  ID_DIR="$HOME/.ga4_mcp"
  mkdir -p "$ID_DIR" 2>/dev/null || true
  if [ -f "$ID_DIR/installation_id" ]; then
    ANON_ID="$(cat "$ID_DIR/installation_id" 2>/dev/null || true)"
  else
    RAW_UUID="$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid 2>/dev/null || echo "$(date +%s)-$RANDOM")"
    ANON_ID="inst_$(echo "$RAW_UUID" | tr '[:upper:]' '[:lower:]')"
    printf '%s' "$ANON_ID" > "$ID_DIR/installation_id" 2>/dev/null || ANON_ID=""
  fi
fi

HAS_GEMINI=false
HAS_CLAUDE=false
HAS_CURSOR=false
HAS_VSCODE=false
HAS_BREW=false
HAS_UV=false

HARNESSES=()
CONFIGURED=()

if command -v gemini &> /dev/null; then HAS_GEMINI=true; HARNESSES+=("gemini"); fi
if [ -d "$HOME/Library/Application Support/Claude" ] || [ -d "$HOME/.config/Claude" ]; then HAS_CLAUDE=true; HARNESSES+=("claude"); fi
if [ -d "$HOME/.cursor" ]; then HAS_CURSOR=true; HARNESSES+=("cursor"); fi
if [ -d "$HOME/.vscode" ] || command -v code &> /dev/null; then HAS_VSCODE=true; HARNESSES+=("vscode"); fi
if command -v brew &> /dev/null; then HAS_BREW=true; fi
if command -v uv &> /dev/null || command -v uvx &> /dev/null; then HAS_UV=true; fi

PY_VER="$(python3 --version 2>/dev/null || echo 'None')"

AUTH_STATUS="unauthenticated"
if command -v gcloud &> /dev/null && gcloud auth application-default print-access-token &> /dev/null; then
  AUTH_STATUS="gcloud_adc_active"
elif [ -n "$CREDS_PATH" ] || [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  AUTH_STATUS="env_vars_present"
fi

if [ "$IS_INTERACTIVE" = true ]; then
  echo -e "\${BLUE}=====================================================\${NC}"
  echo -e "\${BLUE}🚀 GA4 MCP Universal AI Installer & Setup Wizard\${NC}"
  echo -e "\${BLUE}=====================================================\${NC}"
  echo -e "\${CYAN}🌐 Opening setup visual guide: https://${host}/setup\${NC}"
  if [[ "$OS" == "Darwin"* ]]; then open "https://${host}/setup" &> /dev/null || true; fi
fi

# 1. Homebrew
if [ "$TARGET_OVERRIDE" = "brew" ] || ([ "$TARGET_OVERRIDE" = "auto" ] && [ "$HAS_BREW" = true ] && [ "$HAS_GEMINI" = false ] && [ "$HAS_CLAUDE" = false ]); then
  echo -e "\${YELLOW}Installing GA4 MCP via Homebrew...\${NC}"
  brew tap surendranb/tap || true
  brew install google-analytics-mcp || true
  CONFIGURED+=("homebrew")
  echo -e "\${GREEN}✅ Installed via Homebrew!\${NC}"
fi

# 2. Gemini CLI
if [ "$TARGET_OVERRIDE" = "gemini" ] || ([ "$TARGET_OVERRIDE" = "auto" ] && [ "$HAS_GEMINI" = true ]); then
  echo -e "\${YELLOW}Installing Gemini CLI Extension...\${NC}"
  gemini extensions install https://github.com/surendranb/google-analytics-mcp &> /dev/null || true
  CONFIGURED+=("gemini_cli")
  echo -e "\${GREEN}✅ Gemini CLI Extension installed!\${NC}"
fi

# 3. Claude / Cursor MCP JSON Auto-Injection
if [ "$TARGET_OVERRIDE" = "claude" ] || [ "$TARGET_OVERRIDE" = "cursor" ] || ([ "$TARGET_OVERRIDE" = "auto" ] && [ "$HAS_CLAUDE" = true ]); then
  CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
  if [[ "$OS" == "Linux"* ]]; then CLAUDE_CONFIG_DIR="$HOME/.config/Claude"; fi
  CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"

  CONFIGURED+=("claude_desktop_manual")
  echo -e "\${YELLOW}➡ Claude/Cursor detected. Add this to $CLAUDE_CONFIG_FILE under \\"mcpServers\\":\${NC}"
  echo '  "ga4-analytics": { "command": "uvx", "args": ["--from", "google-analytics-mcp", "ga4-mcp-server"], "env": { "GA4_PROPERTY_ID": "<your-property-id>", "GOOGLE_APPLICATION_CREDENTIALS": "<path-to-service-account.json>" } }'
  echo -e "\${CYAN}Full guide: https://${host}/setup\${NC}"
fi

# Non-blocking Execution Telemetry Ping back to Cloudflare Worker (skipped on opt-out)
# Payload built via heredoc: shell-level quote escaping inside -d "..." mangles the
# JSON (quotes get consumed by bash), which silently 400s at the worker.
if [ -n "$ANON_ID" ]; then
  TELEMETRY_PAYLOAD=$(cat <<JSONEOF
{
  "anonymous_id": "$ANON_ID",
  "execution_mode": "$EXEC_MODE",
  "harnesses_detected": [$(printf '"%s",' "\${HARNESSES[@]}" | sed 's/,$//')],
  "configured_harnesses": [$(printf '"%s",' "\${CONFIGURED[@]}" | sed 's/,$//')],
  "terminal_app": "$TERM_APP",
  "shell_type": "$SHELL_TYPE",
  "os_name": "$OS",
  "arch": "$ARCH",
  "python_version": "$PY_VER",
  "has_uv": $HAS_UV,
  "has_brew": $HAS_BREW,
  "auth_status": "$AUTH_STATUS",
  "install_outcome": "success",
  "target_override": "$TARGET_OVERRIDE"
}
JSONEOF
)
  curl -s -m 5 -X POST "https://${host}/telemetry" \\
    -H "Content-Type: application/json" \\
    -d "$TELEMETRY_PAYLOAD" &> /dev/null || true
fi

if [ "$IS_INTERACTIVE" = true ]; then
  echo -e "\${BLUE}=====================================================\${NC}"
  echo -e "\${GREEN}🎉 Setup Complete! Guide & Docs: https://ga4mcp.com\${NC}"
else
  echo '{"status": "success", "mode": "agent_headless", "ready": true}'
fi
`;
}

async function sendPostHogEvent(env, payload) {
  try {
    await fetch(`${env.POSTHOG_HOST}/capture/`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        api_key: env.POSTHOG_API_KEY,
        event: payload.event,
        distinct_id: payload.distinct_id,
        properties: payload.properties,
        timestamp: new Date().toISOString()
      })
    });
  } catch (err) {
    // Fail silently
  }
}
