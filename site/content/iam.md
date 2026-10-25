---
slug: /iam/
title: "Fix the GA4 permission error"
description: "The service account is valid but not authorised on the property. Nine steps in the Analytics UI, plus what to check when the change has not taken effect yet."
group: start
nav: "Permissions"
order: 3
---

# The 403 that is not a bug

If you see this error, the credentials worked. The query reached Google and Google said no:

```text
IAM Error: The service account does not have Viewer access to the GA4 property
```

Nothing is wrong with your JSON key, your file path, or your property ID. The service account exists, it authenticated, and it has no permission on that property. Adding it is nine clicks.

## The nine steps

You need the `client_email` value from your service-account JSON key. It looks like `my-agent@my-project.iam.gserviceaccount.com`. Open the key file in any text editor and copy that field — not `client_id`, not the private key.

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

## Let the agent check for you

If the client can reach the server at all, this returns the same decision tree offline:

```text
get_troubleshooting_guide(topic="iam")
```

And `setup_ga4_access` walks the fix in-session where the client supports prompts.

## Next

If permissions are fine and queries still fail, the problem is a field name or a filter shape. Read [query shapes](/schema/).
