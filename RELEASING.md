# Releasing `google-analytics-mcp`

`pyproject.toml` is the version source of truth for this project. `server.json` mirrors that version for registry consumers, and `CHANGELOG.md` is the source for release notes.
The project is distributed under the Apache License 2.0.

## Release Checklist

1. Update `version` in `pyproject.toml`.
2. Mirror the same version in `server.json` for both the server and package entries.
3. Add a matching changelog entry in `CHANGELOG.md`.
4. Run `python scripts/check_package_consistency.py`.
5. Run `python -m build`.
6. Publish the artifacts to PyPI.
7. Create the matching GitHub release from the changelog entry.

## Notes

- Supported launch commands are `ga4-mcp-server` and `python -m ga4_mcp`.
- Package-facing docs and config should never reference the legacy single-file entrypoint or module path.
