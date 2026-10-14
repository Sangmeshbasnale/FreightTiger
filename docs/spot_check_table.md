# Ground Truth Spot-Check Table: Justified Route-Weeks

As required by Section 7.6 of `plan.md` and the Case Study guardrails, every route-week marked as `No (justified)` must be manually audited against the original text in `context_notes.csv` to prove zero fabrication.

| Route | Week of | Matched Note ID | Note Route Applies? | Note Time Applies? | Note Supports Cost Rise? | Observed Cost Spike | Note Event Details | Final Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **Ahmedabad-Mumbai** | `2025-01-20` | `N002` | **Yes** (Exact route match) | **Yes** (Week of Jan 20, 2025 matches Jan 20 festival week) | **Yes** (Temporary surcharge due to capacity shortage) | `+29.5% own` / `+22.5% peer` | *"A regional festival week saw a temporary surcharge applied by transporters..."* | **No (justified)** |
| **Chennai-Bangalore** | `2025-02-24` | `N001` | **Yes** (Exact route match) | **Yes** (Feb 24 to Mar 8 flood window) | **Yes** (Longer detours and higher trip costs) | `+31.5% own` / `+38.7% peer` | *"Heavy flooding on highway forced longer detours and higher trip costs..."* | **No (justified)** |
| **Chennai-Bangalore** | `2025-03-03` | `N001` | **Yes** (Exact route match) | **Yes** (Overlaps Feb 24 to Mar 8 flood window) | **Yes** (Detours ongoing through Mar 8) | `+27.8% own` / `+34.9% peer` | *"Roads were passable again by Mar 9."* | **No (justified)** |
| **Mumbai-Delhi** | `2025-05-12` | `N003` | **Yes** (Applies to All Routes) | **Yes** (Overlaps nationwide diesel rise starting May 5) | **Yes** (Nationwide diesel price hike ~5–7%) | `+11.6% own` / `+6.7% peer` | *"Diesel prices rose nationwide starting this week..."* | **No (justified)** |

---

### Negative Control Spot-Checks (Trap Notes Barred from Justification)

| Note ID | Date | Route | Stated In Note | Why It Cannot Justify | System Action |
| :---: | :---: | :---: | :--- | :--- | :---: |
| `N004` | `2024-03-11` | All Routes | New toll plaza commissioned on a highway stretch. | Explicitly states: *"affected routes are not part of this dataset"*. | **Never matched** |
| `N005` | `2024-07-29` | Mumbai-Delhi | Scheduled highway maintenance caused minor delays. | Explicitly states: *"costs were not significantly affected"*. | **Never matched** |
| `N006` | `2025-09-22` | All Routes | Logistics industry quarterly report. | Explicitly states: *"stable demand with no major disruptions"*. | **Never matched** |
| `N007` | `2024-05-20` | Delhi-Jaipur | Resurfacing work completed. | Improved road conditions do not explain higher transport costs. | **Never matched** |
| `N008` | `2025-06-09` | Kolkata-Bhubaneswar | Corridor quarterly report. | Explicitly states: *"freight movement remained normal"*. | **Never matched** |
| `N009` | `2025-03-17` | Chennai-Bangalore | Highway reopened after repairs. | Post-flood normalization does not justify cost rise. | **Never matched** |
| `N010` | `2025-10-27` | All Routes | New commercial fleet tracking mandate. | Explicitly states: *"compliance costs were absorbed without a rate change"*. | **Never matched** |
