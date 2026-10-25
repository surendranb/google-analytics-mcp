---
slug: /
title: "GA4 MCP — Google Analytics 4 for any AI client"
description: "Query Google Analytics 4 from your AI agent. Twelve tools, sixteen analytical skills, schema validation before every query. MIT, local, read-only."
full: true
hero: true
group: start
nav: "Overview"
order: 1
---

<section class="hero">
<div class="hero__grid">
<div>
<p class="eyebrow">v2.11.6 · MIT · local stdio · read-only</p>
<h1>Ask GA4 a question. Get the answer an analyst would give.</h1>
<p class="lede">One MCP server for Claude, Cursor, Codex, Gemini CLI and twelve more clients. Twelve tools, sixteen analytical skills, and a schema check that validates every field name against your property before the query runs.</p>
<div class="hero__cta">
<a class="btn btn--primary" href="/setup/">Install in one line</a>
<a class="btn btn--ghost" href="/skills/">See the 16 skills</a>
</div>
</div>
<div class="card">
<p class="card__h">Install</p>
<div class="cb"><div class="cb__bar"><span class="cb__lang">shell</span><button class="cb__copy" type="button">Copy</button></div><pre><code>curl -fsSL "https://ga4.builditwithai.xyz/install" | bash</code></pre></div>
<p style="font-size:.85rem;color:var(--ink-55);margin:.7rem 0 0">Finds your client, writes the entry, checks the credentials.</p>
</div>
</div>
</section>

<div class="stats">
<div class="stat"><div class="stat__n">12</div><div class="stat__l">tools</div></div>
<div class="stat"><div class="stat__n">16</div><div class="stat__l">analytical skills</div></div>
<div class="stat"><div class="stat__n">17</div><div class="stat__l">client guides</div></div>
<div class="stat"><div class="stat__n">0</div><div class="stat__l">writes to your property</div></div>
</div>

<section class="section">
<h2 class="section__h">An agent with a GA4 tool guesses. That is the whole problem.</h2>
<p class="section__sub">Three failures show up every time someone points a general-purpose model at the Analytics Data API.</p>
<div class="grid3">
<div class="feat"><h3>It invents field names</h3><p>Models are trained on Universal Analytics vocabulary. <code>pageviews</code> instead of <code>screenPageViews</code>. The API returns a 400 and the agent retries with another guess.</p></div>
<div class="feat"><h3>It invents a method</h3><p>Ask why traffic dropped and it will produce a plausible five-step analysis that never checks whether the drop was one channel or all of them.</p></div>
<div class="feat"><h3>It does the arithmetic itself</h3><p>Pull seven daily rows, ask for the week, and the model sums them in its head. Rates do not sum. The number is wrong and looks fine.</p></div>
</div>
</section>

<section class="section">
<h2 class="section__h">What this server does about it</h2>
<p class="section__sub">Three mechanisms, all of them inside the tool call. Nothing here depends on the model behaving well.</p>
<div class="grid3">
<div class="feat"><h3>Schema check before the query</h3><p><code>get_ga4_data</code> validates every dimension and metric name against your live property. A wrong name comes back with the reason and the correct spelling, not a 400 and a retry loop.</p></div>
<div class="feat"><h3>Skills loaded on demand</h3><p>Sixteen recipes ship in the package — traffic diagnosis, ecommerce, attribution scope, AI referral split. The agent loads one before it analyzes, so the method is fixed instead of improvised.</p></div>
<div class="feat"><h3>Totals computed by GA4</h3><p>Every multi-row pull returns a <code>totals</code> block that GA4 computed server-side. The model reads the period figure instead of adding up rows and drifting.</p></div>
</div>
</section>

<section class="section">
<h2 class="section__h">What it does when the setup is broken</h2>
<p class="section__sub">Most failures are not analysis failures. They are a missing property ID, an expired token, or a service account that was never added to the property. The server handles all three inside the session.</p>
<div class="grid3">
<div class="feat"><h3>Setup recovery mid-session</h3><p><code>setup_ga4_access</code> collects the missing value and reconnects without a restart. No client config editing, no reinstall.</p></div>
<div class="feat"><h3>Guides bundled offline</h3><p><code>get_troubleshooting_guide</code> serves the setup, IAM and schema fix paths from inside the package. It works with no network and no API access.</p></div>
<div class="feat"><h3>Row guard before the pull</h3><p>Large queries are estimated first and warn above 2,500 rows, so one careless question does not fill the context window with raw rows.</p></div>
</div>
</section>

<section class="section">
<h2 class="section__h">Against Google's own server</h2>
<p class="section__sub">Google ships an official Analytics MCP server, and it is genuinely good. Here is the honest split.</p>
<div class="compare">
<div>
<h4>Google's Analytics MCP</h4>
<ul>
<li>Admin API plus Data API: accounts, properties, Google Ads links, core and funnel reports, realtime.</li>
<li>Hosted remote endpoint at <code>analyticsdata.googleapis.com/mcp/v1</code> — no local install at all.</li>
<li>Apache-2.0, labelled Experimental, maintained by the Analytics organisation.</li>
<li>Best choice when you want zero install and a vendor-maintained toolset.</li>
</ul>
</div>
<div>
<h4>This server</h4>
<ul>
<li>Reporting and metadata, with the analysis layer attached: 16 skills, schema validation, GA4-computed totals, row guard.</li>
<li>Local stdio over your own credentials. Nothing leaves your machine except GA4 API calls.</li>
<li>MIT, one maintainer, and a fix path for the three errors that actually stop people.</li>
<li>Best choice when the agent has to reason about the numbers, not just fetch them.</li>
</ul>
</div>
</div>
</section>

<section class="section">
<h2 class="section__h">Sixteen skills, loaded only when needed</h2>
<p class="section__sub">Each one is a short playbook with the exact dimensions, metrics and interpretation rules for one job. The agent calls <code>search_skills</code>, gets one back, and follows it.</p>
<div class="tw"><table><thead><tr><th>Skill</th><th>What it settles</th></tr></thead><tbody>
<tr><td><a href="/skills/traffic-diagnosis/">Traffic diagnosis</a></td><td>Whether a change is real, and which channel moved first</td></tr>
<tr><td><a href="/skills/ecommerce-analysis/">Ecommerce</a></td><td>Revenue, conversion rate, AOV and funnel drop-off</td></tr>
<tr><td><a href="/skills/ai-referral-analysis/">AI referrals</a></td><td>Splitting ChatGPT, Claude, Perplexity and Gemini traffic from organic</td></tr>
<tr><td><a href="/skills/attribution-scope/">Attribution scope</a></td><td>Why session, event and user numbers never match</td></tr>
<tr><td><a href="/skills/common-metric-names/">Metric names</a></td><td>The GA4 name for the UA name the model guessed</td></tr>
<tr><td><a href="/skills/">All sixteen</a></td><td>Including filters, date ranges, custom dimensions, bot traffic</td></tr>
</tbody></table></div>
</section>

<section class="section">
<h2 class="section__h">Your client is on the list</h2>
<p class="section__sub">The installer writes the entry for eight of them. Codex, Gemini CLI, Goose and Kiro take one config block each, quoted from that vendor's own documentation.</p>
<div class="grid3">
<div class="feat"><h3>Auto-configured</h3><p>Claude Desktop and Code, Cursor, VS Code (Cline, Roo Code), Continue.dev, OpenCode, Devin Desktop (formerly Windsurf), Zed, Google Antigravity.</p></div>
<div class="feat"><h3>One block, copied from the vendor</h3><p>Codex writes TOML, Goose writes YAML, Gemini CLI and Kiro write JSON. Each guide shows the exact shape that client expects.</p></div>
<div class="feat"><h3>Start here</h3><p><a href="/ga4-mcp-for-every-harness/">The client hub</a> has every guide, or go straight to <a href="/ga4-mcp-for-claude/">Claude</a> or <a href="/ga4-mcp-for-cursor/">Cursor</a>.</p></div>
</div>
</section>

<section class="section">
<h2 class="section__h">Install</h2>
<ol class="steps">
<li><h3>Run the installer</h3><div class="cb"><div class="cb__bar"><span class="cb__lang">shell</span><button class="cb__copy" type="button">Copy</button></div><pre><code>curl -fsSL "https://ga4.builditwithai.xyz/install" | bash</code></pre></div><p>It detects your client, checks for <code>uv</code>, and writes the server entry. Restart the client afterwards.</p></li>
<li><h3>Give it two values</h3><div class="cb"><div class="cb__bar"><span class="cb__lang">shell</span><button class="cb__copy" type="button">Copy</button></div><pre><code>export GA4_PROPERTY_ID="123456789"
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/key.json"</code></pre></div><p>Both live inside the client's server entry. The property ID is the numeric one from Admin, Property details — not the <code>G-</code> measurement ID.</p></li>
<li><h3>Ask a question that needs a real answer</h3><div class="cb"><div class="cb__bar"><span class="cb__lang">text</span><button class="cb__copy" type="button">Copy</button></div><pre><code>Why did organic sessions drop in the last 7 days?</code></pre></div><p>You have succeeded when the agent loads the <code>traffic-diagnosis</code> skill and calls <code>get_ga4_data</code> without a setup error. <a href="/setup/">Full setup guide</a>.</p></li>
</ol>
</section>

<section class="section">
<h2 class="section__h">The parts people get stuck on</h2>
<div class="grid3">
<div class="feat"><h3><a href="/iam/">The 403 that is not a bug</a></h3><p>The service account is valid but was never added to the property. Nine steps in the Analytics UI, with the exact role.</p></div>
<div class="feat"><h3><a href="/schema/">The filter shape</a></h3><p><code>dimension_filter</code> follows the Data API v1beta schema, not SQL. Working templates for string, list, numeric and AND/OR groups.</p></div>
<div class="feat"><h3><a href="/setup/">The property ID</a></h3><p>Most setup failures are the measurement ID pasted where the property ID belongs. One paragraph explains the difference.</p></div>
</div>
</section>
