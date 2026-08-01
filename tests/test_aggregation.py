# SPDX-License-Identifier: Apache-2.0
"""Coaching: multi-row pulls (e.g. 7 days of daily rows) must come back with a
server-side `totals` block so the model reads the period figure directly instead
of summing rows itself (a known LLM error mode). GA4 computes the totals in the
same response (metric_aggregations=[TOTAL]) — we must surface response.totals.

Pure transform over the GA4 response object; a faithful stub stands in for the
proto response (the live client needs credentials). Run: python tests/test_aggregation.py"""

import sys

from ga4_mcp.tools.reporting import _build_report_payload


class _Val:
    def __init__(self, value):
        self.value = value


class _Header:
    def __init__(self, name):
        self.name = name


class _Row:
    def __init__(self, dims, mets):
        self.dimension_values = [_Val(v) for v in dims]
        self.metric_values = [_Val(v) for v in mets]


class _Resp:
    """Mimics RunReportResponse: rows, totals, headers, row_count."""

    def __init__(self, dim_names, met_names, rows, totals=None, row_count=None):
        self.dimension_headers = [_Header(n) for n in dim_names]
        self.metric_headers = [_Header(n) for n in met_names]
        self.rows = [_Row(d, m) for (d, m) in rows]
        self.totals = [_Row([], t) for t in (totals or [])]
        self.row_count = row_count if row_count is not None else len(self.rows)


def _run():
    failures = []

    # 7 days of daily totalUsers/sessions, with a GA4 totals row.
    rows = [(["2026-07-2%d" % i], [str(100 + i), str(50 + i)]) for i in range(7)]
    grand = [str(sum(100 + i for i in range(7))), str(sum(50 + i for i in range(7)))]
    resp = _Resp(["date"], ["totalUsers", "sessions"], rows, totals=[grand])

    payload = _build_report_payload(resp, skill=None)

    if len(payload.get("data", [])) != 7:
        failures.append(f"expected 7 data rows, got {len(payload.get('data', []))}")

    totals = payload.get("totals")
    if not totals:
        failures.append("multi-row response has no `totals` block (server-side aggregation not surfaced)")
    else:
        if totals.get("totalUsers") != grand[0]:
            failures.append(f"totals.totalUsers wrong: {totals.get('totalUsers')!r} != {grand[0]!r}")
        if totals.get("sessions") != grand[1]:
            failures.append(f"totals.sessions wrong: {totals.get('sessions')!r} != {grand[1]!r}")

    # A coaching note must tell the model to use totals rather than sum rows.
    note = payload.get("metadata", {}).get("aggregation_note", "")
    if "total" not in note.lower():
        failures.append("no aggregation coaching note in metadata")

    # Single-row response (no dimensions) needs no separate totals block —
    # the one row already IS the aggregate; don't clutter.
    single = _Resp([], ["totalUsers"], [([], ["777"])], totals=None)
    p2 = _build_report_payload(single, skill=None)
    if p2.get("data", [{}])[0].get("totalUsers") != "777":
        failures.append("single-row payload lost its data")

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("PASS: server-side totals surfaced with coaching note; single-row unaffected")


if __name__ == "__main__":
    _run()
