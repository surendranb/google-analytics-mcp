# Releasing `google-analytics-mcp`

`pyproject.toml` is the version source of truth for this project. `server.json` mirrors that version for registry consumers, and `CHANGELOG.md` is the source for release notes.
The project is distributed under the Apache License 2.0.

## Trusted Publishing Setup

This repository is configured for PyPI Trusted Publishing from GitHub Actions. After the one-time setup below, releases no longer need `~/.pypirc`, `twine upload`, or a long-lived PyPI token in GitHub.

### PyPI project setup

In PyPI, open the `google-analytics-mcp` project, go to `Publishing`, and add a GitHub Actions publisher with:

- Owner: `surendranb`
- Repository name: `google-analytics-mcp`
- Workflow filename: `.github/workflows/release.yml`
- Environment name: `pypi`

### GitHub setup

In GitHub, create an environment named `pypi`.

The environment is optional for GitHub itself, but it is strongly recommended and should match the PyPI publisher configuration exactly. You can use it to add approval rules before publication.

## Release Checklist

1. Update `version` in `pyproject.toml`.
2. Mirror the same version in `server.json` for both the server and package entries.
3. Add a matching changelog entry in `CHANGELOG.md`.
4. Run `python scripts/check_package_consistency.py`.
5. Push the release commit and tag to GitHub.
6. Publish the matching GitHub release.
7. Let `.github/workflows/release.yml` build and publish the artifacts to PyPI.

## Notes

- Supported launch commands are `ga4-mcp-server` and `python -m ga4_mcp`.
- Package-facing docs and config should never reference the legacy single-file entrypoint or module path.
- Trusted Publishing uses GitHub OIDC, so the release workflow should not use a stored PyPI API token.
