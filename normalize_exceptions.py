#!/usr/bin/env python3
"""Normalize FreightWorks exception exports (Ajaia / Corrigan Peak, DET-121).

Usage: python normalize_exceptions.py exceptions.csv [clean_output.csv]
Prints a summary by event type and a list of records that need human review.
Nothing is silently guessed: anything uncertain is flagged, never dropped.
"""
import csv
import re
import sys
from collections import Counter
from datetime import datetime

TERMINAL_RE = re.compile(r"^(?:terminal|t)\s*[-_ ]?\s*(\d+)$", re.I)


def norm_terminal(raw):
    m = TERMINAL_RE.match((raw or "").strip())
    if not m:
        return None, f"unrecognized terminal '{raw}'"
    return f"Terminal {int(m.group(1))}", None


def norm_carrier(raw):
    c = (raw or "").strip().upper()
    if not c:
        return None, "carrier code missing - cannot infer, ask Corrigan Peak IT"
    return c, None


def norm_event(raw):
    e = re.sub(r"[\s\-]+", "_", (raw or "").strip().lower())
    return (e or None), (None if e else "event_type missing")


def norm_ts(raw):
    """Return (iso_string, tz_label, note). Never converts timezones silently."""
    s = (raw or "").strip()
    if not s:
        return None, None, "timestamp missing"
    # ISO with explicit UTC marker
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?Z$", s)
    if m:
        y, mo, d, h, mi, sec = (int(x or 0) for x in m.groups())
        return datetime(y, mo, d, h, mi, sec).isoformat(), "UTC (explicit)", None
    # ISO without timezone
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?$", s)
    if m:
        y, mo, d, h, mi, sec = (int(x or 0) for x in m.groups())
        return datetime(y, mo, d, h, mi, sec).isoformat(), "unspecified", None
    # Slash dates: ambiguous between MM/DD and DD/MM when both parts <= 12
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?$", s)
    if m:
        a, b, y, h, mi, sec = (int(x or 0) for x in m.groups())
        if a > 12 and b <= 12:
            day, mon = a, b
        elif b > 12 and a <= 12:
            mon, day = a, b
        elif a <= 12 and b <= 12:
            if a == b:
                mon, day = a, b
            else:
                return None, None, f"ambiguous date '{s}' (MM/DD vs DD/MM)"
        else:
            return None, None, f"invalid date '{s}'"
        try:
            return datetime(y, mon, day, h, mi, sec).isoformat(), "unspecified", None
        except ValueError:
            return None, None, f"invalid date '{s}'"
    return None, None, f"unrecognized timestamp format '{s}'"


def clean_row(row):
    notes = []
    terminal, n = norm_terminal(row.get("terminal")); notes += [n] if n else []
    event, n = norm_event(row.get("event_type")); notes += [n] if n else []
    carrier, n = norm_carrier(row.get("carrier_code")); notes += [n] if n else []
    ts, tz, n = norm_ts(row.get("event_ts")); notes += [n] if n else []
    return {
        "exception_id": (row.get("exception_id") or "").strip(),
        "terminal": terminal or "",
        "event_type": event or "",
        "carrier_code": carrier or "",
        "event_ts": ts or "",
        "tz": tz or "",
        "review_notes": "; ".join(notes),
    }


def process(rows):
    cleaned = [clean_row(r) for r in rows]
    # Cross-record check: mixed explicit-UTC and unspecified timestamps
    tzs = {c["tz"] for c in cleaned if c["tz"]}
    if "UTC (explicit)" in tzs and "unspecified" in tzs:
        for c in cleaned:
            if c["tz"] == "UTC (explicit)":
                c["review_notes"] = "; ".join(filter(None, [
                    c["review_notes"],
                    "only record with explicit UTC; others have no timezone - "
                    "NOT converted, confirm FreightWorks timezone"]))
    return cleaned


def summarize(cleaned):
    counts = Counter(c["event_type"] or "UNKNOWN" for c in cleaned)
    flagged = [c for c in cleaned if c["review_notes"]]
    return counts, flagged


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 1
    with open(argv[1], newline="", encoding="utf-8-sig") as f:
        cleaned = process(list(csv.DictReader(f)))
    out = argv[2] if len(argv) > 2 else "exceptions_clean.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(cleaned[0].keys()))
        w.writeheader(); w.writerows(cleaned)
    counts, flagged = summarize(cleaned)
    print(f"Records: {len(cleaned)}  |  Clean: {len(cleaned)-len(flagged)}  |  Need review: {len(flagged)}\n")
    print("Exceptions by event type:")
    for k, v in sorted(counts.items()):
        print(f"  {k:<22}{v}")
    if flagged:
        print("\nNeeds human review:")
        for c in flagged:
            print(f"  {c['exception_id']}: {c['review_notes']}")
    print(f"\nClean file written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
