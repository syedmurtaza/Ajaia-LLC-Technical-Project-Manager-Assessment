# Ajaia Technical Project Manager Assessment: Syed Murtaza Hussain Kazmi

**Video:** https://screenrec.com/share/68U5g0RSJI
**Reference:** https://ajaia.ai
**Build files:** `normalize_exceptions.py`, `test_normalize.py`, `exceptions.csv` (input), `exceptions_clean.csv` (output)

*Scenario date assumed: Monday, August 17. Go-live: Tuesday, September 8.*

---

## Task 1: Triage

**Noise item: E (the blue shade).** It is cosmetic, came from an offhand remark in an ops conversation and not from Dana, and has no bearing on the go-live.

| Rank | Item | This week | Why |
|---|---|---|---|
| 1 | **C. DET-121, Terminal 3 null urgency scores** | **Worked** | This is the one real go-live blocker: null scores mean Terminal 3 exceptions are never ranked or routed. It needs about 2 days of work after Corrigan Peak IT answers, and that request has sat unsent since 8/6, so the clock is already running. I sent the IT request today with specific questions taken from their own export. |
| 2 | **B. Priya's duplicate-push risk** | **Worked, fix lands before the PR merges** | Duplicate pushes would flood dispatchers with repeats, which recreates the "shared inbox everyone ignores" problem the tool exists to fix. Priya was right to flag it, so I treat it as a today problem: hold the merge, add an idempotency guard (claim the exception atomically before pushing) and a lock so overlapping poll cycles cannot run together. |
| 3 | **A. Dana's auto-reassign request** | **Declined for Sept 8, with a phased alternative offered** | Automatically moving freight to a backup carrier is a cost and service decision nobody has validated, and the terminal leads have not yet reviewed the routing rules. Adding it in the same three weeks as DET-121 and the retry fix puts the date at risk. I offer "suggest a backup carrier, dispatcher confirms in one click" for launch and full auto-reassign as a follow-up phase once the leads sign off. Dana needs to decide how to frame this to her COO. |
| 4 | **D. DET-118, terminal lead review** | **Worked (invites go out today)** | "No blocker" is misleading: this review is how we validate the routing rules before launch, and it is the right place to scope the auto-reassign question. It is cheap, but it takes calendar time, so it cannot wait. |
| 5 | **E. Blue shade change** | **Deferred** | Not requested by the client sponsor and not tied to the date. If it truly is one CSS line, it gets bundled into the already-scheduled UI review. No separate work this week. |

### Protecting the date

September 8 holds only if two things are true: Corrigan Peak IT answers on Terminal 3 fields by **Friday, August 21**, and auto-reassign is **not** added to launch scope. The team will not "work faster"; this is what changes:

- **Cut from Sept 8 scope:** auto-reassign (replaced by suggested backup carrier with one-click confirm).
- **Deferred:** the UI color change.
- **Fallback if IT's answer is late:** Terminals 1 and 2 launch September 8, and Terminal 3 runs in flag-only mode (no scoring) until DET-121 closes. The alternative is moving the full launch, which I recommend against because Dana gave the date to her board.

**Also noted:** last Friday's update (Green, "no blockers", "minor validation task") was inaccurate. DET-121 was already open and unpicked since 8/6, and it depends on the client. That is corrected in Task 3.

---

## Task 2: Build

**Files:** `normalize_exceptions.py` (script), `test_normalize.py` (tests), `exceptions.csv` (Material 3 input), `exceptions_clean.csv` (output).

**Run it:**
```
python normalize_exceptions.py exceptions.csv exceptions_clean.csv
python test_normalize.py
```
Standard-library Python 3, nothing to install.

**Sample output:**
```
Records: 5  |  Clean: 3  |  Need review: 2

Exceptions by event type:
  carrier_substitution  1
  doc_mismatch          2
  missed_pickup         2

Needs human review:
  CPX-88215: only record with explicit UTC; others have no timezone - NOT converted, confirm FreightWorks timezone
  CPX-88216: carrier code missing - cannot infer, ask Corrigan Peak IT
```

**Note on what it does and how I checked it.** The script reads the FreightWorks export and normalizes three things: terminal names (`T3` and `Terminal 3` both become `Terminal 3`), carrier codes (uppercased, so `swft`, `Swft` and `SWFT` match), and timestamps (three input formats converted to one ISO format). It then counts exceptions by event type and lists any record it could not confidently clean, with the reason. It never drops a record and never guesses: a missing carrier code stays blank and is flagged, an ambiguous date such as `03/04/2026` is flagged instead of assumed, and the one timestamp marked UTC is not converted, because the other four carry no timezone and converting only one would silently create a wrong record. To check that it works, and not just that it runs, I wrote six tests covering each normalizer, the ambiguous-date and invalid-date cases, and the full file (5 records in and 5 out, counts of 2 / 2 / 1, and exactly CPX-88215 and CPX-88216 flagged), then compared the output file row by row against the raw data. Limits: five rows is a tiny sample, so real exports will likely show more formats; `RLCX` appears only once and cannot be validated without a carrier master list; and for `carrier_substitution` records it is unclear whether the carrier code is the original or the replacement. Both of those go to Corrigan Peak IT as questions.

---

## Task 3: Client Status Update

**To:** Dana Okafor, VP Operations, Corrigan Peak Logistics
**Subject:** Dispatch Exception Triage: status correction, and two decisions I need from you

Dana,

I need to correct last Friday's update. It showed Green with no blockers. A more accurate status is **Yellow**: September 8 is still achievable, but it now depends on one answer from your IT team and one decision from you.

**What I got wrong on Friday.** I described the Terminal 3 issue as a minor data validation task with no impact on the date. It is bigger than that. Urgency scores are coming back empty for part of Terminal 3's data, because the fields Terminal 3 sends don't match what we built against. Until that is fixed, those exceptions won't be scored or routed correctly. The ticket had also been open since August 6 and wasn't picked up. That was our miss, not yours.

**Where things stand.**
- Ingestion, scoring and routing remain substantially complete for all three terminals except the Terminal 3 issue above.
- The fix takes about two days of engineering work once your IT contact confirms which fields Terminal 3 sends. The request went to your team today.
- Our engineer found a risk in her own code: in rare cases the same exception could be sent to a dispatcher twice. We are fixing that before it merges, not after launch.
- We had not yet contacted the three terminal leads about the routing-rules review, though last Friday's update implied we were waiting on their schedules. Invitations go out today, and we are asking for the review during the week of August 24.

**What I need from you.**
1. **By Friday, August 21:** your IT contact's confirmation of the fields Terminal 3 sends. In the sample export you sent, one record has no carrier code, and one timestamp is marked UTC while the others show no timezone, so we'd also like to know which timezone FreightWorks uses. I'll send the exact questions today so it takes them minutes, not hours.
2. **By Wednesday, August 19:** your decision on the backup-carrier request. I would like to say yes to your COO, and I don't want you going back to him with a bare "no." But automatically reassigning freight changes a decision your dispatchers make today, and your terminal leads haven't yet reviewed the rules it would follow. Adding it now would put September 8 at risk. My recommendation: for September 8, the tool **suggests a backup carrier** on missed pickups and the dispatcher confirms with one click. Full automatic reassignment follows as a second phase, once the terminal leads have signed off on the rules. If it helps, I can give you a short summary for the COO.

**What this means for the date.** If we have IT's answer by August 21, September 8 holds. If the answer comes later, I would recommend launching Terminals 1 and 2 on September 8, with Terminal 3 flagging exceptions for dispatchers without automatic scoring until the fix is in. The other choice is moving the full launch date, but I know you gave September 8 to your board, so I'd rather not do that unless you tell me to.

We are also postponing a request to change the dispatcher queue color. It isn't tied to the launch, and we'll cover it during the UI review.

I'll send the next update on **Thursday, August 20**, whether or not we have IT's answer. If you'd like to talk it through, I'm available any time this week.

Syed Murtaza Hussain Kazmi
Technical Project Manager, Ajaia
https://ajaia.ai

---

## Task 4: AI Workflow Note

I used Claude for the triage reasoning (pressure-testing my ranking), for writing and testing the normalization script, and for drafting the status update. I kept human the final ranking, the decision to decline auto-reassign for September 8 while offering a phased alternative, the dates and commitments in the client update, and the decision to launch Terminal 3 in flag-only mode if IT's answer is late. I also reviewed and ran the script myself. One thing I chose not to do: convert the one UTC-marked timestamp to local time, which an obvious cleanup step would do, because the other four records have no timezone and converting only one would silently create a wrong record, so the script flags it for the client instead.
