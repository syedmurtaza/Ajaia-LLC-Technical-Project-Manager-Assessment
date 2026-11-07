"""
To Run: python test_normalize.py
"""
import csv
from normalize_exceptions import norm_terminal, norm_carrier, norm_ts, process, summarize

def test_terminal():
    assert norm_terminal("T3")[0] == "Terminal 3"
    assert norm_terminal("Terminal 3")[0] == "Terminal 3"
    assert norm_terminal("terminal3")[0] == "Terminal 3"
    assert norm_terminal("Dock 9")[0] is None

def test_carrier():
    assert norm_carrier(" Swft ")[0] == "SWFT"
    assert norm_carrier("")[0] is None

def test_timestamps_all_formats_agree():
    assert norm_ts("2026-08-14 09:12:00")[0] == "2026-08-14T09:12:00"
    assert norm_ts("08/14/2026 09:45")[0] == "2026-08-14T09:45:00"
    assert norm_ts("2026-08-14T10:03:00Z")[0] == "2026-08-14T10:03:00"

def test_ambiguous_date_is_flagged_not_guessed():
    iso, _, note = norm_ts("03/04/2026 09:00")
    assert iso is None and "ambiguous" in note

def test_invalid_date_flagged():
    assert norm_ts("13/45/2026 09:00")[0] is None

def test_full_file():
    rows = list(csv.DictReader(open("exceptions.csv")))
    cleaned = process(rows)
    counts, flagged = summarize(cleaned)
    assert len(cleaned) == 5                      # nothing dropped
    assert counts == {"missed_pickup": 2, "doc_mismatch": 2, "carrier_substitution": 1}
    assert {c["exception_id"] for c in flagged} == {"CPX-88215", "CPX-88216"}
    assert all(c["terminal"] == "Terminal 3" for c in cleaned)

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("PASS", n)
