# GA4 403 Permission Denied: Service Account Viewer Fix

> Fix 403 The caller does not have permission and IAMError on GA4. Add the service account as Viewer in Property access management, then check the property ID.

Canonical URL: https://ga4mcp.com/iam/



A 403 on a GA4 query means the credentials worked. The request reached Google, and Google said no:

```text
IAM Error: The service account does not have Viewer access to the GA4 property
```

Nothing is wrong with your JSON key, your file path, or your token. The account authenticated and has no role on that property. Adding the role takes nine clicks, below. If the error instead reads `401 invalid authentication`, the problem is the credential and not the permission — go to [setup](/setup/#when-credentials-are-rejected).

## The nine steps

You need the `client_email` value from your service-account JSON key. It looks like `my-agent@my-project.iam.gserviceaccount.com`. Open the key file in any text editor and copy that field — not `client_id`, not the private key. If you authenticate with `gcloud` instead of a key, the grantee is the Google account you signed in with, and its address is the one to paste.

1. Open [analytics.google.com](https://analytics.google.com).
2. Select the property whose ID matches your `GA4_PROPERTY_ID`.
3. Click **Admin**, the gear at the bottom left.
4. In the **Property** column, click **Property access management**.
5. Click the blue **+** at the top right, then **Add users**.
6. Paste the `client_email` into the email field.
7. Leave **Notify new users by email** switched off. It is a robot address and the mail bounces.
8. Under **Direct roles**, tick **Viewer**. Do not tick Administrator.
9. Click **Add**.

Retry the query. It works immediately — there is no propagation delay on property access.

## When Viewer is not enough

The server is read-only, so Viewer covers every tool it ships. Two situations need more:

- You are querying **real-time reports** on a property where the service account was added to an account rather than a property. Add it at the property level instead.
- You are using `list_properties` across several properties. The service account needs access to each one it should see. It returns only what it can read, and an empty list means zero properties, not a broken install.

> **Note:** these steps change a permission on a live Google property. If you are not the property owner, someone who is has to do this. There is no API path around it and no workaround that keeps Viewer off.

## Still failing after the add

Work through these in order. Each one has a distinct error message.

**`PERMISSION_DENIED` with a property ID in the message.** The property ID in your config is not the one you granted access to. Compare the two numbers digit by digit. This is common when someone has both a GA4 and an old UA property with similar names.

**`API has not been used in project ... before or it is disabled`.** The Analytics Data API is off. Enable it in the Google Cloud console under **APIs & Services → Library**.

**`invalid_grant` or `ADCExpired`.** Your `gcloud` session expired. Run `gcloud auth application-default login` again. If you use a JSON key, this error means the key was deleted or rotated.

**`The caller does not have permission` on `list_properties`.** The service account has no access at the account level. This is expected and harmless if the property-level grant above is in place.

## Which account to grant

The server names the grantee in the boot error, because the right email depends on how you authenticated. A service-account key produces `the service account you@project.iam.gserviceaccount.com`. Application default credentials produce `the Google account you authenticated with via gcloud`. Grant the one that appears in the message — granting the other is the usual reason a second attempt still returns 403.

If the message quotes a property ID you do not recognise, stop: you are about to grant a role on someone else's property. Fix `GA4_PROPERTY_ID` first.

## Let the agent check for you

If the client can reach the server at all, this returns the same decision tree offline:

```text
get_troubleshooting_guide(topic="iam")
```

Or run the interactive fix:

```text
setup_ga4_access()
```

## Five prompts that resolve a 403

Paste one into [Claude](/ga4-mcp-for-claude/), [Cursor](/ga4-mcp-for-cursor/), [Codex](/ga4-mcp-for-codex/), or any of the [17 clients](/ga4-mcp-for-every-harness/). Each makes the agent read the grant path from the server rather than inventing one.

1. **Identify the exact grantee**
   ```text
   My GA4 query returns 403. Read the boot error, tell me the exact account it names as lacking access, and whether that is a service account or my gcloud identity. Do not tell me to re-download the key.
   ```
2. **Walk the grant**
   ```text
   Call get_troubleshooting_guide(topic="iam") and walk me through the property access grant for this exact grantee, naming the Admin screen at each step.
   ```
3. **Wrong property ID**
   ```text
   The 403 message quotes a property ID. Compare it against my configured GA4_PROPERTY_ID digit by digit and tell me whether I granted access to a different property.
   ```
4. **Zero properties listed**
   ```text
   list_properties returned an empty list and no error. Explain what that result means about my permissions, and list which properties this identity can actually read.
   ```
5. **After the grant**
   ```text
   I added the service account as Viewer. Retry the failed query now without restarting the client, and confirm with a totals block whether access is working.
   ```

## Next

[Setup](/setup/) for creating the service account key, [troubleshooting](/troubleshooting/) for common 400 and quota errors, and [query shapes](/schema/) for filter syntax.
