# GA4 MCP Setup Error: GA4_PROPERTY_ID or Credentials

> Fix GA4 MCP setup failures: GA4_PROPERTY_ID unset, 401 invalid authentication, and a credentials path that does not resolve. Env block and verification.

Canonical URL: https://ga4mcp.com/setup/



Setup fails in four ways, and each has a different fix. Find your error in the first table, or work down the page from the install.

| Error you see | What is wrong | Fix |
|---|---|---|
| `InitError` / `GA4_PROPERTY_ID environment variable not set` | The property ID is missing, or it sits outside the server's `env` block | [Step 2](#step-2-connect-it-to-your-property) |
| `401 invalid authentication` or `ADCExpired` | Credentials were presented and Google rejected them: expired `gcloud` session, or a deleted or rotated key | [Credentials](#when-credentials-are-rejected) |
| `403` / `IAMError` | The account authenticated but has no Viewer role on that property | [Permissions guide](/iam/) |
| `400` invalid dimension or metric | The field name is a UA name or a guess | [Query shapes](/schema/) |

Everything below assumes a Google Analytics 4 property and an AI client that speaks MCP.

## What you need first

Three things, and only the first one is usually wrong.

**A GA4 property ID.** It is a number like `123456789`. You find it in Analytics under **Admin → Property details**. It is not the `G-XXXXXXXXXX` measurement ID, and it is not the numeric stream ID. Pasting the measurement ID is the single most common setup failure.

**A Google Cloud project** with the Analytics Data API enabled.

**Credentials,** picked in the next section. Either a service-account JSON key or the local `gcloud` login works.

## Step 1 — Install the server

Three routes. Pick one.

The installer is the one that also writes your client entry:

```bash
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash
```

It detects your client, checks for `uv`, installs the package, and writes the MCP server entry. It covers Claude Desktop, Claude Code, Cursor, VS Code with Cline or Roo Code, Continue.dev, OpenCode, Windsurf, Zed and Google Antigravity.

If you would rather not run a script, use a runtime directly:

```bash
uvx google-analytics-mcp
```

```bash
npx -y @surendranb/google-analytics-mcp
```

Both are the same server. `uvx` is faster to start after the first run; `npx` needs Node already installed.

> **Note:** the installer writes the entry, not the credentials. You still set the two values in Step 2.

## Step 2 — Connect it to your property

The server reads two environment variables. Both belong inside the client's server entry, not in your shell profile, unless you launch the client from a shell that has them.

```bash
export GA4_PROPERTY_ID="123456789"
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/service-account.json"
```

The credentials path must be absolute. A relative path resolves against whatever directory the client happens to start in, which is not the one you expect. The server checks this at boot: a path that does not exist, or one still holding the `/ABSOLUTE/PATH/TO` placeholder from a copied snippet, fails with the path quoted back to you.

**If you use a service account,** create it in the Google Cloud console under **IAM & Admin → Service Accounts**, then **Keys → Add key → JSON**. That key file is what the path points at. The service account also has to be added to the GA4 property itself — that is a separate step and it is where most people stop. The [permissions guide](/iam/) walks through it.

**If you use `gcloud` instead,** run this once and skip the key file entirely:

```bash
gcloud auth application-default login
```

Then omit `GOOGLE_APPLICATION_CREDENTIALS`. The server picks up application default credentials.

> **Tip:** the property ID is numeric and has no prefix. If yours starts with `G-`, you have the measurement ID, and every query will fail with a permissions error that has nothing to do with permissions.

## When credentials are rejected

A `401 invalid authentication` is not a missing file. The file was read, sent to Google, and refused. Three causes, in order of frequency:

**The `gcloud` session expired.** Application default credentials carry a refresh token that stops working after re-authentication events. Run `gcloud auth application-default login` again and retry — no config edit, no client restart.

**The key was deleted or rotated.** A service-account key is a static file, so a 401 from a key path means that key ID was removed in the Cloud console. Download a new key and point `GOOGLE_APPLICATION_CREDENTIALS` at it. This is the failure mode that recurs, which is the argument for preferring a key over ADC on a long-lived machine.

**The file is not a service-account key.** An OAuth client secret JSON or a downloaded `credentials.json` from another Google product loads as JSON and authenticates as nothing. The key must contain `"type": "service_account"`.

The same 401 shows up as `503` when it arrives mid-session rather than at boot. Both mean the credential expired rather than the permission being missing, so treat them the same way.

## Step 3 — Verify it actually works

Open your client and ask this exact question:

```text
List my GA4 properties.
```

You have succeeded when the agent calls `list_properties` and returns rows. An empty list is not a setup failure — it means the credentials work and the account reads no properties, which is a [permissions](/iam/) problem.

Then ask one question that exercises the analysis layer:

```text
Why did organic sessions drop in the last 7 days?
```

A working install loads the `traffic-diagnosis` skill, calls `get_ga4_data`, and answers with a `totals` block rather than a summary of daily rows.

## When it fails

| What you see | What it means | Where to go |
|---|---|---|
| `InitError` on startup | One or both environment variables are missing or outside the server's `env` block | [Setup errors](#step-2-connect-it-to-your-property) |
| `401` or `invalid_grant` | The credential was rejected, not the permission | [When credentials are rejected](#when-credentials-are-rejected) |
| `IAMError` or `403` | The service account is valid but was never added to the property | [Permissions guide](/iam/) |
| `ADCExpired` or `503` | The `gcloud` login expired | Run `gcloud auth application-default login` again |
| `400` invalid dimension or metric | The field name is a UA name or a guess | [Query shapes](/schema/) and `search_schema` |

The server also carries these fix paths inside the package, so an agent can resolve most of them without a browser:

```text
get_troubleshooting_guide(topic="setup" | "iam" | "schema")
```

## Or let the agent fix it

If the client supports prompts, `setup_ga4_access` collects the missing value and reconnects without a restart. That is usually faster than editing config by hand.

## Five prompts that fix a broken install

Paste one into the client whose config you are editing — [Claude](/ga4-mcp-for-claude/), [Cursor](/ga4-mcp-for-cursor/), [VS Code](/ga4-mcp-for-vscode/), or any of the [17 clients](/ga4-mcp-for-every-harness/). Each is written to make the agent read its own bundled guide instead of guessing.

1. **Missing property ID**
   ```text
   My GA4 MCP server failed to start with GA4_PROPERTY_ID unset. Call get_troubleshooting_guide(topic="setup"), then tell me the exact env block to add and which number is the property ID.
   ```
2. **Collect and reconnect in-session**
   ```text
   Run setup_ga4_access. Ask me for whichever value is missing, validate it against Google, and confirm the property is readable without a client restart.
   ```
3. **401 invalid authentication**
   ```text
   The server returns 401 invalid authentication. Determine whether my credentials are an expired gcloud ADC session or a service-account key that was deleted, then give me the one command or console step that replaces it.
   ```
4. **Placeholder or relative credentials path**
   ```text
   Check my GOOGLE_APPLICATION_CREDENTIALS value. Tell me whether it is absolute, whether the file exists, and whether it contains "type": "service_account" — quote the path back before suggesting a change.
   ```
5. **Confirm the install end to end**
   ```text
   Call list_properties and show me the raw result. Then run one get_ga4_data query for sessions over the last 7 days and show the totals block, so I can see the full path works.
   ```

## Next

Read [your client's guide](/ga4-mcp-for-every-harness/) for the exact config shape it expects, since four of the eleven clients use a different key than the rest. Then read the [skills index](/skills/) to see what the agent can do once it is connected, or browse [prompts](/google-analytics-ai-prompts/) for 35 tested templates.
