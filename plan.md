Below is a **case-study-oriented, end-to-end plan** for building the FreightTiger “Smart Assistant That Watches Shipping Costs.” I have structured it so that every requirement from the PDF, the sample output contract, the shipment data, and the context notes is covered. After the plan, I do a **revisit/verification pass** against the uploaded files and explicitly list the missing/edge-case items that I added.

---

# 1. Project goal, deliverables, and definition of done

## 1.1 Core problem

Build an assistant that:

1. Groups shipment records by:
   - `route` = same origin and destination, e.g. `Delhi-Jaipur`
   - `route_type` = provided `Short` / `Medium` / `Long`
2. Computes weekly cost efficiency:
   - `cost_per_tonne_km = total freight cost / total tonne-km`
   - Weeks are Monday to Sunday.
   - `week_of` is the Monday date of that week.
3. Compares each route-week against:
   - Its own trailing 8-week history, strictly before the current week.
   - The average of similar routes in the same week, excluding itself.
4. Flags unusual cost rises.
5. Checks context notes to see whether the rise is genuinely justified.
6. Outputs a CSV matching the exact sample format.
7. Provides trust artifacts:
   - Evaluation harness / labeled checks
   - Reproducibility evidence across 3 runs
   - Token/cost log
   - README explaining decisions

## 1.2 Mandatory hand-ins

The submission must contain:

1. Working code.
2. Output CSV matching `sample_output_format_v2.csv` exactly in column names, order, and type.
3. README explaining:
   - How it works
   - How it was built
   - How correctness was checked
   - What happens when fewer than 8 prior weeks exist
4. Reproducibility check:
   - 3 untouched runs on same input
   - Identical flags and numbers
   - Explanation wording may vary only if LLM is used; cited note, verdict, and numbers must not vary.
5. Token/cost log:
   - Total input tokens
   - Total output tokens
   - Number of LLM calls
   - Approximate cost
6. Short 10-minute walkthrough plan for Round 2.

## 1.3 Non-negotiable grading constraints

These must be treated as hard requirements:

- Use the exact comparison definitions.
- Do not improvise the baseline windows.
- Do not derive your own route-length buckets; use `route_type`.
- Do not pad or extrapolate missing weeks.
- Every “justified” verdict must cite the exact note.
- The cited note must apply to that route and that time.
- Notes that say costs were not affected cannot justify a rise.
- No supporting note means `unexplained`.
- Wrong route, wrong time window, or fabricated reasoning is fatal.
- Output must follow the sample CSV contract.
- `matched_note_id` must contain the note ID for justified rows, blank for unexplained.
- Prefer open-source/free-tier tools.
- Show that the system is trustworthy, not just runnable.

---

# 2. High-level architecture

Recommended architecture:

```text
/raw data
  shipment_records.csv
  context_notes.csv
  sample_output_format_v2.csv

/src
  config.py / config.yaml
  data_loader.py
  data_quality.py
  weekly_features.py
  baselines.py
  anomaly_policy.py
  notes_registry.py
  retrieval.py
  justification.py
  explanation.py
  output_writer.py
  pipeline.py
  evaluate.py
  reproducibility.py
  token_cost_logger.py

/scripts
  run_pipeline.py
  run_eval.py
  run_repro.py
  run_qa.py

/outputs
  route_week_features.parquet/csv
  baselines.parquet/csv
  anomaly_candidates.csv
  submission.csv
  eval_report.json
  repro_report.txt
  token_cost_log.json

/tests
  test_week_grouping.py
  test_baselines.py
  test_anomaly_policy.py
  test_note_validation.py
  test_output_format.py

/notebooks
  exploratory_analysis.ipynb

README.md
requirements.txt
Makefile
```

---

# 3. Detailed implementation plan by phase

## Phase 0: Project setup and requirement capture

### Goals

- Create repo structure.
- Freeze the output contract.
- Document assumptions.
- Decide tooling.

### Tasks

1. Create a new project folder or Git repo.
2. Copy input files into `data/raw/`:
   - `shipment_records.csv`
   - `context_notes.csv`
   - `sample_output_format_v2.csv`
3. Create `requirements.txt`.
4. Create `config.yaml` for thresholds, seeds, model names, output paths.
5. Create a `docs/assumptions.md` file.
6. Decide whether to use:
   - Local open-source embeddings only.
   - Optional local LLM.
   - Deterministic templates for final explanation.

### Recommended tooling

Core:

- Python 3.11
- pandas
- numpy
- pytest

AI/retrieval:

- `sentence-transformers` with `all-MiniLM-L6-v2`
- ChromaDB or FAISS for local vector search

Optional LLM:

- Local open-source model via Ollama, e.g. `llama3.2:3b`
- Temperature `0`
- Optional seed if supported

Why this stack?

- Free/open-source.
- Runs locally.
- Reproducible.
- No paid API dependency.
- Good enough for only 10 notes.

### Definition of done for Phase 0

- Repo created.
- Input files present.
- Dependencies installable.
- Output contract documented.
- Assumptions file started.

---

## Phase 1: Data profiling and validation

### Goals

Understand the exact shape and quality of the shipment records and context notes.

### Shipment data checks

For `shipment_records.csv`, validate:

1. Required columns exist:
   - `shipment_id`
   - `origin`
   - `destination`
   - `route_type`
   - `material`
   - `quantity_tonnes`
   - `distance_km`
   - `freight_cost_inr`
   - `shipment_date`
   - `transporter`

2. Data types:
   - `quantity_tonnes`: numeric, positive.
   - `distance_km`: numeric, positive.
   - `freight_cost_inr`: numeric, non-negative.
   - `shipment_date`: parseable date.

3. Route consistency:
   - `route_type` values are only `Short`, `Medium`, `Long`.
   - Same origin-destination should not have conflicting `route_type` values.
   - Create route name as:
     ```python
     route = f"{origin}-{destination}"
     ```

4. Date range:
   - Minimum date.
   - Maximum date.
   - Presence of leap days, e.g. `2024-02-29`.
   - Confirm week boundaries.

5. Route list:
   - Mumbai-Pune
   - Delhi-Jaipur
   - Chennai-Bangalore
   - Kolkata-Bhubaneswar
   - Ahmedabad-Mumbai
   - Mumbai-Delhi
   - Delhi-Chennai

Important: Delhi-Chennai appears later in the dataset. It must not be ignored.

### Context notes checks

For `context_notes.csv`, validate:

1. Columns:
   - `note_id`
   - `date`
   - `applies_to`
   - `note`

2. Notes include:
   - Route-specific notes.
   - All-route notes.
   - Negative/no-effect notes.
   - Trap notes that must not justify cost rises.

3. Special notes:
   - `N004` says affected routes are not part of this dataset. It must never justify.
   - `N005` says costs were not significantly affected. It must never justify a rise.
   - `N006` says stable demand/no major disruptions. It must never justify a rise.
   - `N008` says no significant disruptions. It must never justify a rise.
   - `N010` says compliance costs were absorbed without rate change. It must never justify a rise.

### Data quality rules

Create a data-quality module that:

- Drops or logs rows with missing essential fields.
- Drops or logs rows where:
  - `quantity_tonnes <= 0`
  - `distance_km <= 0`
  - `freight_cost_inr < 0`
  - `shipment_date` is invalid
- Writes a data-quality report.

### Definition of done for Phase 1

- All rows parsed.
- Invalid rows logged.
- Route list known.
- Date range known.
- Context notes reviewed manually.
- Data-quality report generated.

---

## Phase 2: Weekly route-level cost computation

This is the core numeric engine.

### Route definition

Use:

```python
route = origin + "-" + destination
```

Do not combine reverse routes unless they are identical origin and destination. For example, `Delhi-Jaipur` and `Jaipur-Delhi` would be different if both existed.

### Week definition

Weeks run Monday to Sunday.

For each shipment date:

```python
week_of = shipment_date - timedelta(days=shipment_date.weekday())
```

where Monday is weekday `0`.

Example:

- `2024-01-01` is Monday → `week_of = 2024-01-01`
- `2024-01-07` is Sunday → `week_of = 2024-01-01`
- `2024-01-08` is Monday → `week_of = 2024-01-08`

### Weekly aggregation

For each group:

- `route`
- `route_type`
- `week_of`

Compute:

```text
total_freight_cost = sum(freight_cost_inr)
total_tonne_km = sum(quantity_tonnes * distance_km)
shipment_count = count(shipment_id)
cost_per_tonne_km = total_freight_cost / total_tonne_km
```

Important: Do not average per-shipment cost ratios. Use the exact formula:

```text
cost_per_tonne_km = total freight cost / total quantity-tonnes × total distance-km
```

More precisely, for the group:

```text
cost_per_tonne_km =
    sum(freight_cost_inr)
    /
    sum(quantity_tonnes * distance_km)
```

### Handling missing/invalid weeks

If a route has no valid shipments in a week, do not fabricate a weekly cost.

Do not pad missing weeks.

### Definition of done for Phase 2

- One row per valid route-week.
- Correct Monday `week_of`.
- Correct cost per tonne-km.
- No fabricated missing weeks.
- Unit tests pass for week grouping and aggregation.

---

## Phase 3: Baseline computations

The PDF says the two comparison fields are numeric fields that will be graded, so these definitions must be exact.

---

## 3.1 Own-history baseline

### Required definition

For each route and current week:

- Use trailing 8-week rolling average of that route’s `cost_per_tonne_km`.
- Use only weeks strictly before the current week.
- No look-ahead.
- If fewer than 8 prior weeks exist, use all prior weeks available.
- Do not pad or extrapolate.

### Implementation

For each route, sort weeks ascending.

Let:

```text
current_week_cost = cost_per_tonne_km for current route-week
prior_costs = cost_per_tonne_km for same route in previous weeks, strictly before current week
own_history_baseline = mean(last up to 8 values in prior_costs)
```

Then:

```text
vs_own_history_pct =
    ((current_week_cost - own_history_baseline) / own_history_baseline) * 100
```

### Output string format

Match sample style exactly:

```text
+35.5% vs this route's past average
```

So:

```python
vs_own_history = f"{pct:+.1f}% vs this route's past average"
```

If no prior history exists:

- Leave `vs_own_history` blank.
- Do not invent `0%`.
- Mention in README that first weeks have no own-history baseline.

### Fewer than 8 prior weeks

If a route has only 3 prior weeks, use those 3.

README must explicitly say:

> When fewer than 8 prior weeks exist, all available prior weeks are used. No padding or extrapolation is performed.

### Definition of done

- Own-history baseline uses strictly prior weeks.
- Maximum of 8 prior weeks used.
- If fewer than 8, all available prior weeks used.
- No look-ahead.
- Unit tests prove no future data leakage.

---

## 3.2 Similar-routes baseline

### Required definition

For each route-week:

- Use the same `week_of`.
- Use all other routes with the same `route_type`.
- Exclude the route itself.
- Compute the average `cost_per_tonne_km` of those peer route-weeks.

### Implementation

For a given row:

```text
peer_costs =
    cost_per_tonne_km of all rows
    where week_of = current week_of
    and route_type = current route_type
    and route != current route
```

Then:

```text
similar_routes_baseline = mean(peer_costs)
```

Then:

```text
vs_similar_routes_pct =
    ((current_week_cost - similar_routes_baseline) / similar_routes_baseline) * 100
```

### Output string format

Match sample style exactly:

```text
+21.0% vs similar-length routes this week
```

So:

```python
vs_similar_routes = f"{pct:+.1f}% vs similar-length routes this week"
```

If no peer routes exist in that week:

- Leave `vs_similar_routes` blank.
- Do not invent a value.

### Definition of done

- Peer average excludes the route itself.
- Peer average uses only the same week.
- Peer average uses only same `route_type`.
- Unit tests validate exclusion logic.

---

## Phase 4: Flagging policy

The case study does not prescribe exact anomaly thresholds. It says:

> Flag any route where the cost is rising and looks out of the ordinary compared to its own history or to similar routes.

Therefore, we need a transparent, deterministic policy.

## 4.1 Recommended flagging logic

Use a rule-based policy stored in config.

### Basic rising condition

If own history is available:

```text
cost_rising_vs_own = current_cost > own_history_baseline
```

If own history is unavailable:

- Allow peer-based rising condition only if peer comparison is available.

### Starting thresholds

Because the sample output includes:

- `+35.5%` own, `+21.0%` peer → flagged
- `+29.5%` own, `+22.5%` peer → justified, not flagged
- `+9.2%` own, `+23.6%` peer → flagged

The thresholds must allow a `+9.2%` own or `+23.6%` peer case to be considered unusual.

Recommended starting config:

```yaml
flagging:
  own_pct_threshold: 8.0
  peer_pct_threshold: 15.0
  no_history_peer_pct_threshold: 25.0
  require_positive_own_if_available: true
```

### Flag condition

If own-history baseline exists:

```text
flag_candidate =
    cost_rising_vs_own
    and
    (
        vs_own_history_pct >= own_pct_threshold
        or
        vs_similar_routes_pct >= peer_pct_threshold
    )
```

If own-history baseline does not exist:

```text
flag_candidate =
    vs_similar_routes_pct >= no_history_peer_pct_threshold
```

### Optional statistical refinement

If time permits, add a route-specific volatility check:

```text
own_z_score =
    (current_cost - own_history_mean) / own_history_std
```

Then flag only if:

```text
own_z_score >= 2.0
```

or if the percentage rise is very large.

But keep the simple threshold policy as the primary version because it is easier to explain and reproduce.

## 4.2 Flag values

Use these exact strings:

| Situation | `flagged` value |
|---|---|
| Unexplained unusual rise | `Yes` |
| Normal non-anomalous row | `No` |
| Unusual rise explained by valid note | `No (justified)` |

The sample uses `No (justified)`, so use that exact phrase.

## 4.3 Threshold calibration step

Before final submission:

1. Run the pipeline with thresholds `8%` own / `15%` peer.
2. Inspect all flagged rows.
3. Check whether known events are captured:
   - Ahmedabad-Mumbai festival week, note `N002`.
   - Chennai-Bangalore flooding, note `N001`.
   - Possible diesel price rise, note `N003`.
4. If the diesel 5–7% rise should be considered, either:
   - Lower own threshold to `5%`, or
   - Add a note-aware moderate-rise justification rule.
5. Document the final threshold and why it was chosen.

Important trade-off:

- Lower threshold catches more real mild increases but creates more noise.
- Higher threshold reduces noise but may miss mild justified increases.

The README should explain this trade-off.

### Definition of done for Phase 4

- Deterministic flag policy.
- Thresholds in config.
- Flag values match sample style.
- Known sample rows behave correctly.
- Threshold decision documented.

---

## Phase 5: Context-note understanding and RAG design

This is the AI/bonus part, but it must be grounded and non-hallucinatory.

## 5.1 Notes inventory

The given notes are:

| note_id | date | applies_to | Can justify cost rise? |
|---|---:|---|---|
| N001 | 2025-02-24 | Chennai-Bangalore | Yes, flooding disruption |
| N002 | 2025-01-20 | Ahmedabad-Mumbai | Yes, festival surcharge |
| N003 | 2025-05-05 | All Routes | Possibly yes, diesel price rise |
| N004 | 2024-03-11 | All Routes | No, affected routes not in dataset |
| N005 | 2024-07-29 | Mumbai-Delhi | No, costs not significantly affected |
| N006 | 2025-09-22 | All Routes | No, stable/no disruptions |
| N007 | 2024-05-20 | Delhi-Jaipur | No, improved road conditions; not a cost-rise reason |
| N008 | 2025-06-09 | Kolkata-Bhubaneswar | No, no significant disruptions |
| N009 | 2025-03-17 | Chennai-Bangalore | No, normalization after repairs; not a cost-rise reason |
| N010 | 2025-10-27 | All Routes | No, compliance costs absorbed, no rate change |

## 5.2 Create a curated note registry

Do not rely only on raw note text. Create a structured registry derived from the exact notes.

Example:

```json
[
  {
    "note_id": "N001",
    "date": "2025-02-24",
    "applies_to": ["Chennai-Bangalore"],
    "effective_start": "2025-02-24",
    "effective_end": "2025-03-08",
    "effect": "cost_increase",
    "can_justify": true,
    "magnitude_min_pct": null,
    "magnitude_max_pct": null,
    "summary": "Heavy flooding disrupted truck movement, forcing longer detours and higher trip costs from Feb 24 to Mar 8."
  },
  {
    "note_id": "N002",
    "date": "2025-01-20",
    "applies_to": ["Ahmedabad-Mumbai"],
    "effective_start": "2025-01-20",
    "effective_end": "2025-01-26",
    "effect": "cost_increase",
    "can_justify": true,
    "magnitude_min_pct": null,
    "magnitude_max_pct": null,
    "summary": "A regional festival week caused a temporary surcharge due to high demand and limited truck availability."
  },
  {
    "note_id": "N003",
    "date": "2025-05-05",
    "applies_to": ["ALL"],
    "effective_start": "2025-05-05",
    "effective_end": "2025-06-01",
    "effect": "cost_increase",
    "can_justify": true,
    "magnitude_min_pct": 3.0,
    "magnitude_max_pct": 10.0,
    "summary": "Diesel prices rose nationwide, pushing transport costs up roughly 5-7%."
  },
  {
    "note_id": "N004",
    "date": "2024-03-11",
    "applies_to": ["ALL"],
    "can_justify": false,
    "reason": "Note explicitly says affected routes are not part of this dataset."
  },
  {
    "note_id": "N005",
    "date": "2024-07-29",
    "applies_to": ["Mumbai-Delhi"],
    "can_justify": false,
    "reason": "Note says costs were not significantly affected."
  },
  {
    "note_id": "N006",
    "date": "2025-09-22",
    "applies_to": ["ALL"],
    "can_justify": false,
    "reason": "Note says stable demand and no major disruptions."
  },
  {
    "note_id": "N007",
    "date": "2024-05-20",
    "applies_to": ["Delhi-Jaipur"],
    "can_justify": false,
    "reason": "Improved road conditions do not justify a cost rise."
  },
  {
    "note_id": "N008",
    "date": "2025-06-09",
    "applies_to": ["Kolkata-Bhubaneswar"],
    "can_justify": false,
    "reason": "No significant disruptions; freight movement normal."
  },
  {
    "note_id": "N009",
    "date": "2025-03-17",
    "applies_to": ["Chennai-Bangalore"],
    "can_justify": false,
    "reason": "Route returned to normal after repairs; does not explain a cost rise."
  },
  {
    "note_id": "N010",
    "date": "2025-10-27",
    "applies_to": ["ALL"],
    "can_justify": false,
    "reason": "Compliance costs absorbed by transporters without rate change."
  }
]
```

This registry is not hallucination. It is a controlled interpretation of the exact notes, and the final reason still cites the original note ID and date.

## 5.3 Effective date windows

For each note, define an applicability window.

### N001

Text says:

> from Feb 24 to Mar 8

Use:

```text
effective_start = 2025-02-24
effective_end = 2025-03-08
```

Weeks potentially justified:

- `2025-02-24`
- `2025-03-03`

Do not justify week `2025-03-10`.

### N002

Text says:

> a regional festival week

Use:

```text
effective_start = 2025-01-20
effective_end = 2025-01-26
```

Week potentially justified:

- `2025-01-20`

### N003

Text says:

> Diesel prices rose nationwide starting this week, pushing up transportation costs across all routes by roughly 5-7%.

Use a conservative limited window, for example:

```text
effective_start = 2025-05-05
effective_end = 2025-06-01
```

Reason:

- It describes a cost shock starting that week.
- After several weeks, the new diesel cost is absorbed into history.
- We avoid using it months later to justify unrelated rises.

Magnitude filter:

- Justify only if own-history increase is roughly within 3% to 10%.
- If rise is much larger, do not use N003 as the full explanation.

This should be documented as an assumption.

## 5.4 Retrieval approach

Even though there are only 10 notes, implement retrieval to satisfy the AI/RAG requirement.

### Embedding model

Use:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Reasons:

- Open-source.
- Free.
- Small.
- Works on CPU.
- Deterministic enough for this use case.

### Vector store

Use one of:

- ChromaDB local persistent collection.
- FAISS index.

Recommended: ChromaDB for simplicity.

### Retrieval query

For each anomalous route-week, construct a query like:

```text
Cost increase on route Chennai-Bangalore during week 2025-02-24.
The route cost rose +25.0% versus its own history and +12.0% versus similar routes.
Find a note that explains higher freight cost on this route during this time.
```

Retrieve top 5 notes.

### Retrieval is not enough

Retrieval only produces candidates.

A deterministic validator must approve a note before it can become `matched_note_id`.

## 5.5 Justification validator

A note can justify a route-week only if all of these are true:

1. `can_justify == true`
2. Route matches:
   - note applies to exact route, or
   - note applies to all routes.
3. Time window overlaps:
   - route-week Monday to Sunday overlaps note effective window.
4. Effect is cost increase.
5. Magnitude is compatible:
   - If note specifies magnitude, the observed rise must be within tolerance.
6. Note does not say costs were unaffected.
7. Note does not describe normalization/stability/no disruption.

### Route-week overlap logic

For a route-week:

```text
week_start = week_of
week_end = week_of + 6 days
```

Overlap condition:

```text
week_start <= note_effective_end
and
week_end >= note_effective_start
```

## 5.6 Selecting the best note

If multiple valid notes exist:

Rank by:

1. Exact route match beats all-route match.
2. Higher retrieval score.
3. Closer note date to route-week.
4. More specific magnitude/event match.

Only one `matched_note_id` should be output.

### Definition of done for Phase 5

- Notes embedded.
- Retrieval returns candidates.
- Validator prevents hallucination.
- Negative notes cannot justify.
- Correct note windows enforced.
- Justification is deterministic.

---

## Phase 6: Explanation generation and output writing

## 6.1 Explanation strategy

For maximum reproducibility, use deterministic templates for the graded output.

LLM can be optional for stretch Q&A, but the main submission CSV should be generated with grounded templates.

Why?

- Identical output across runs.
- Zero LLM cost.
- No hallucinated wording.
- Still uses AI through embedding retrieval.
- Explanations are grounded in validated notes.

## 6.2 Reason templates

### Unexplained unusual rise

```text
No matching note found for this route or date range. Cost rise looks unexplained and worth a human review.
```

### Justified unusual rise

```text
Matches note {note_id} dated {note_date}: {note_summary}. The cost rise has a clear explanation.
```

Example:

```text
Matches note N002 dated 2025-01-20: a regional festival week caused a temporary surcharge due to high demand and limited truck availability. The cost rise has a clear explanation.
```

### Normal non-anomalous row

```text
No unusual cost rise detected relative to this route's history or similar routes.
```

### Optional closest non-qualifying note

The sample output sometimes mentions the closest note even when it does not justify the rise.

Example style:

```text
The closest note (N006, 2025-09-22) mentions stable demand with no major disruptions -- it does not describe a reason for a cost rise on this route. No genuine justification found; flagged for review.
```

This is optional. If used:

- `matched_note_id` must remain blank.
- The note must not be presented as justification.
- The note text must be represented accurately.
- If unsure, use the simpler generic unexplained reason.

## 6.3 Output CSV contract

The output must have exactly these columns in this order:

```text
route,week_of,cost_per_tonne_km,vs_own_history,vs_similar_routes,flagged,matched_note_id,reason
```

### Formatting rules

| Field | Format |
|---|---|
| `route` | `Origin-Destination` |
| `week_of` | `YYYY-MM-DD` |
| `cost_per_tonne_km` | numeric, 2 decimal places |
| `vs_own_history` | string like `+35.5% vs this route's past average` or blank |
| `vs_similar_routes` | string like `+21.0% vs similar-length routes this week` or blank |
| `flagged` | `Yes`, `No`, or `No (justified)` |
| `matched_note_id` | note ID if justified, otherwise blank |
| `reason` | human-readable explanation |

### Rounding

Use unrounded values for all calculations.

Then format:

- `cost_per_tonne_km`: 2 decimals.
- percentages: 1 decimal.

Recommended rounding:

```python
from decimal import Decimal, ROUND_HALF_UP
```

Avoid accidental banker’s rounding issues.

### Blank fields

If unexplained:

```text
matched_note_id = ""
```

Do not write:

```text
None
NaN
null
```

If comparison unavailable:

```text
vs_own_history = ""
vs_similar_routes = ""
```

### Row selection

Recommended default:

> Output one row for every valid route-week.

Reason:

- The brief asks to track cost week by week.
- It shows comparisons.
- It is safer for demonstrating core logic.

However, because the sample only shows a few rows, create a config option:

```yaml
output:
  mode: all_route_weeks # or anomaly_candidates_only
```

For final submission, use `all_route_weeks` unless HR clarifies otherwise.

### Row ordering

Use deterministic ordering:

```text
route ascending, week_of ascending
```

Document this in README.

### Definition of done for Phase 6

- Output CSV matches sample columns exactly.
- No extra columns.
- Correct formatting.
- Blank `matched_note_id` where unexplained.
- Deterministic output.
- CSV quoting handles commas inside `reason`.

---

## Phase 7: Evaluation harness and trust checks

The PDF explicitly asks:

> Show a check—a lightweight eval harness or a small labeled set you score against—and why you trusted the result enough to submit.

## 7.1 Unit tests

Create unit tests for:

### Date/week logic

Test:

```text
2024-01-01 -> 2024-01-01
2024-01-07 -> 2024-01-01
2024-01-08 -> 2024-01-08
```

### Weekly cost formula

Given:

| shipment | cost | quantity | distance |
|---|---:|---:|---:|
| A | 100 | 2 | 10 |
| B | 200 | 3 | 20 |

Total cost = 300.

Total tonne-km:

```text
2*10 + 3*20 = 20 + 60 = 80
```

Cost per tonne-km:

```text
300 / 80 = 3.75
```

### Own-history baseline

Test:

- Uses only prior weeks.
- Uses up to 8 weeks.
- Does not use current week.
- Does not use future weeks.
- Uses all prior weeks if fewer than 8.

### Peer baseline

Test:

- Same week only.
- Same route_type only.
- Excludes current route.
- Blank if no peers.

### Output formatting

Test:

- Percentage string exact suffix.
- One decimal place.
- Cost two decimals.
- Blank matched note ID for unexplained.
- Flag values exact.

## 7.2 Golden/labeled rows

Create a small labeled CSV.

Start with the sample output rows as sanity checks:

```csv
route,week_of,expected_flag,expected_note_id,reason_label
Delhi-Jaipur,2024-11-11,Yes,,Sample unexplained rise
Ahmedabad-Mumbai,2025-01-20,No (justified),N002,Sample justified festival rise
Mumbai-Pune,2025-09-15,Yes,,Sample unexplained rise
```

Then add known event rows:

```csv
Chennai-Bangalore,2025-02-24,No (justified),N001,Flood disruption
Chennai-Bangalore,2025-03-03,No (justified),N001,Flood disruption tail
Ahmedabad-Mumbai,2025-01-20,No (justified),N002,Festival surcharge
```

Depending on threshold and observed data, add:

```csv
All relevant route,2025-05-05,No (justified),N003,Diesel price rise
```

But only if the computed rise is in the expected 5–7% band and the final threshold treats it as a candidate.

## 7.3 Negative-control tests

These are crucial because the PDF warns about hallucination.

Create tests that assert these notes are never used as `matched_note_id` for justification:

| Note | Why it must not justify |
|---|---|
| N004 | Affected routes not in dataset |
| N005 | Costs not significantly affected |
| N006 | Stable demand/no disruptions |
| N007 | Improved road conditions, not cost-rise reason |
| N008 | No significant disruptions |
| N009 | Normalization after repairs |
| N010 | Compliance costs absorbed, no rate change |

Example test:

```text
Given an anomalous Mumbai-Delhi row near 2024-07-29,
when justification is attempted,
then matched_note_id must not be N005.
```

## 7.4 Retrieval evaluation

For each labeled positive event:

- Check that the correct note appears in top-k retrieved candidates.
- Target: 100% recall@3 for known justified events.

## 7.5 End-to-end scorer

Create `scripts/run_eval.py` that checks:

1. Output file exists.
2. Columns exactly match sample.
3. Numeric fields are parseable.
4. Flag values are valid.
5. For labeled rows:
   - Flag matches expected.
   - `matched_note_id` matches expected.
6. For justified rows:
   - Note ID is valid.
   - Note applies to route.
   - Note applies to week.
   - Note is not a negative-control note.
7. No justified row cites a note that says costs were unaffected.

Output:

```text
outputs/eval_report.json
```

## 7.6 Manual spot-check table

Create a small table in README or docs:

| route | week | matched note | note applies? | note time applies? | note supports cost rise? | final verdict |
|---|---|---|---|---|---|---|

Every justified row should be manually checked against the original note text.

### Definition of done for Phase 7

- Unit tests pass.
- Golden rows checked.
- Negative controls pass.
- Eval report generated.
- Manual spot-check completed.
- You can explain why the output is trustworthy.

---

## Phase 8: Reproducibility

The PDF requires:

> Three untouched runs on the same input: identical flags and numbers. Explanation wording may vary; cited note, verdict, and numbers must not.

## 8.1 Determinism rules

Set:

```python
RANDOM_SEED = 42
```

Use:

- Deterministic sorting.
- Fixed config.
- Fixed model version.
- Fixed note registry.
- No timestamps in output.
- No random sampling.
- Temperature `0` if LLM is used.

## 8.2 Explanation determinism

Recommended:

- Use deterministic templates for final CSV.
- This makes even `reason` identical.
- This is safest.

If LLM is used for wording:

- Use temperature `0`.
- Keep verdict, note ID, and numbers fixed.
- Compare core columns across runs.

Core columns:

```text
route
week_of
cost_per_tonne_km
vs_own_history
vs_similar_routes
flagged
matched_note_id
```

## 8.3 Three-run script

Create `scripts/run_repro.py`:

1. Run pipeline three times from raw inputs.
2. Write:
   - `outputs/run_1/submission.csv`
   - `outputs/run_2/submission.csv`
   - `outputs/run_3/submission.csv`
3. Compare all core columns.
4. If deterministic templates are used, compare all columns including `reason`.
5. Write:

```text
outputs/repro_report.txt
```

Example content:

```text
Run 1 vs Run 2: identical core columns
Run 1 vs Run 3: identical core columns
Run 2 vs Run 3: identical core columns
```

If LLM wording varies:

```text
Reason wording differs in 3 rows, but route, week_of, cost, comparisons, flagged, and matched_note_id are identical.
```

### Definition of done for Phase 8

- Three runs completed.
- Core output identical.
- Repro report saved.
- Any randomness documented.

---

## Phase 9: Token and cost logging

The PDF requires:

> For one full run over the entire shipments file, report total input tokens, total output tokens, number of LLM calls, and rough cost.

## 9.1 If no LLM is used

If final explanation uses templates:

Report:

```json
{
  "llm_calls": 0,
  "input_tokens": 0,
  "output_tokens": 0,
  "cost_usd": 0.0,
  "notes": "Explanations generated by deterministic templates. AI is used via local embedding retrieval."
}
```

This is acceptable if AI is still meaningfully used through retrieval/embeddings.

## 9.2 If LLM is used

Log for each call:

- Call ID
- Purpose
- Model name
- Input tokens
- Output tokens
- Temperature
- Timestamp optional
- Route/week being explained

Then aggregate:

```json
{
  "model": "llama3.2:3b",
  "llm_calls": 42,
  "input_tokens": 18345,
  "output_tokens": 4120,
  "temperature": 0.0,
  "cost_usd": 0.0,
  "cost_basis": "local open-source model"
}
```

If using a hosted API, compute:

```text
cost =
    input_tokens / 1000 * input_rate
  + output_tokens / 1000 * output_rate
```

## 9.3 Embedding cost

Not required, but useful:

- Number of notes embedded: 10.
- Number of queries embedded: number of anomaly candidates.
- Model: local.
- Cost: 0.

### Definition of done for Phase 9

- Token/cost log exists.
- Number of LLM calls known.
- Cost estimate documented.
- If local/free, explicitly say so.

---

## Phase 10: README and walkthrough preparation

The README must make the system easy to understand.

## 10.1 README structure

Recommended:

1. Problem summary.
2. How to run.
3. Architecture diagram.
4. Core logic:
   - Route grouping
   - Week grouping
   - Cost per tonne-km
   - Own-history baseline
   - Similar-routes baseline
5. Flagging policy.
6. Note justification logic.
7. Assumptions:
   - Fewer than 8 prior weeks
   - First week handling
   - Output row selection
   - Note effective windows
   - Thresholds
8. Evaluation:
   - Unit tests
   - Labeled rows
   - Negative controls
   - Manual spot-check
9. Reproducibility:
   - Seed
   - Temperature
   - Three-run result
10. Token/cost log.
11. Limitations.
12. Future improvements.

## 10.2 Required README statement

Include explicitly:

> For the own-history baseline, the trailing average uses up to 8 prior weeks. If fewer than 8 prior weeks exist, all available prior weeks are used. No padding or extrapolation is performed.

Also include:

> The route_type field supplied in the dataset is used directly. No custom distance buckets are derived.

Also include:

> A note is marked as matched only if it applies to the exact route or all routes, overlaps the route-week, describes a cost increase, and does not state that costs were unaffected.

## 10.3 10-minute Round 2 walkthrough plan

Use this structure:

1. 1 min: Problem and output.
2. 2 min: Core pipeline and formulas.
3. 2 min: Baselines and flagging policy.
4. 2 min: RAG/justification guardrails.
5. 1 min: Evaluation harness and negative controls.
6. 1 min: Reproducibility and cost.
7. 1 min: Trade-offs and limitations.

Be ready to answer:

- Why did you choose the threshold?
- Why did you output all route-weeks / only candidates?
- How do you prevent hallucination?
- How do you know N004/N005/N006 are not falsely used?
- What happens with first-week rows?
- What happens with fewer than 8 prior weeks?
- How did you verify the numeric baselines?
- How did you test reproducibility?

---

# 4. Step-by-step implementation sequence

This is the practical order of coding.

## Step 1: Create environment

```bash
mkdir freighttiger_case_study
cd freighttiger_case_study
python -m venv .venv
source .venv/bin/activate
pip install pandas numpy pytest sentence-transformers chromadb pyyaml
```

Create folders:

```bash
mkdir -p data/raw src scripts outputs tests notebooks docs
```

Copy input files into `data/raw/`.

---

## Step 2: Load and validate shipments

Implement:

```text
src/data_loader.py
src/data_quality.py
```

Outputs:

- Cleaned DataFrame.
- Data-quality report.

Checks:

- Positive quantity.
- Positive distance.
- Valid date.
- Valid route_type.

---

## Step 3: Build route-week features

Implement:

```text
src/weekly_features.py
```

Create:

```python
df["route"] = df["origin"] + "-" + df["destination"]
df["shipment_date"] = pd.to_datetime(df["shipment_date"]).dt.date
df["week_of"] = df["shipment_date"] - pd.to_timedelta(df["shipment_date"].apply(lambda d: d.weekday()), unit="D")
df["tonne_km"] = df["quantity_tonnes"] * df["distance_km"]
```

Group:

```python
weekly = df.groupby(["route", "route_type", "week_of"]).agg(
    total_freight_cost=("freight_cost_inr", "sum"),
    total_tonne_km=("tonne_km", "sum"),
    shipment_count=("shipment_id", "count"),
).reset_index()

weekly["cost_per_tonne_km"] = weekly["total_freight_cost"] / weekly["total_tonne_km"]
```

Save:

```text
outputs/route_week_features.csv
```

---

## Step 4: Compute own-history baseline

Implement:

```text
src/baselines.py
```

For each route:

```python
weekly = weekly.sort_values(["route", "week_of"])

weekly["own_history_baseline"] = (
    weekly.groupby("route")["cost_per_tonne_km"]
    .transform(lambda s: s.shift(1).rolling(8, min_periods=1).mean())
)
```

Then:

```python
weekly["vs_own_history_pct"] = (
    (weekly["cost_per_tonne_km"] - weekly["own_history_baseline"])
    / weekly["own_history_baseline"]
    * 100
)
```

Be careful:

- `shift(1)` prevents using the current week.
- `rolling(8, min_periods=1)` uses up to 8 previous weeks.
- If no prior week exists, result is NaN.

---

## Step 5: Compute similar-routes baseline

For each week and route_type, compute peer average excluding current route.

Efficient method:

```python
peer = weekly.groupby(["week_of", "route_type"]).agg(
    route_type_week_sum=("cost_per_tonne_km", "sum"),
    route_type_week_count=("cost_per_tonne_km", "count"),
).reset_index()

weekly = weekly.merge(peer, on=["week_of", "route_type"], how="left")

weekly["peer_sum_excluding_self"] = (
    weekly["route_type_week_sum"] - weekly["cost_per_tonne_km"]
)

weekly["peer_count_excluding_self"] = (
    weekly["route_type_week_count"] - 1
)

weekly["similar_routes_baseline"] = (
    weekly["peer_sum_excluding_self"] / weekly["peer_count_excluding_self"]
)
```

Set baseline to NaN when peer count is zero.

Then:

```python
weekly["vs_similar_routes_pct"] = (
    (weekly["cost_per_tonne_km"] - weekly["similar_routes_baseline"])
    / weekly["similar_routes_baseline"]
    * 100
)
```

---

## Step 6: Apply flag policy

Implement:

```text
src/anomaly_policy.py
```

Use config thresholds.

Pseudo-logic:

```python
def is_anomaly(row, config):
    own_available = not pd.isna(row["own_history_baseline"])
    peer_available = not pd.isna(row["similar_routes_baseline"])

    if own_available:
        rising_vs_own = row["cost_per_tonne_km"] > row["own_history_baseline"]

        if not rising_vs_own and config["require_positive_own_if_available"]:
            return False

        own_high = (
            not pd.isna(row["vs_own_history_pct"])
            and row["vs_own_history_pct"] >= config["own_pct_threshold"]
        )

        peer_high = (
            not pd.isna(row["vs_similar_routes_pct"])
            and row["vs_similar_routes_pct"] >= config["peer_pct_threshold"]
        )

        return own_high or peer_high

    else:
        return (
            peer_available
            and row["vs_similar_routes_pct"] >= config["no_history_peer_pct_threshold"]
        )
```

---

## Step 7: Build note index

Implement:

```text
src/notes_registry.py
src/retrieval.py
```

Tasks:

1. Load `context_notes.csv`.
2. Load curated note metadata.
3. Embed note text.
4. Store in Chroma.
5. Provide function:

```python
retrieve_notes(query: str, top_k: int = 5) -> list[NoteCandidate]
```

---

## Step 8: Validate justification

Implement:

```text
src/justification.py
```

For each anomalous row:

1. Build query.
2. Retrieve top notes.
3. Filter candidates using:
   - route match
   - week overlap
   - `can_justify`
   - effect direction
   - magnitude compatibility
4. Select best valid note.
5. If valid note exists:
   - `flagged = "No (justified)"`
   - `matched_note_id = note_id`
   - reason template with note ID/date/summary.
6. Else:
   - `flagged = "Yes"`
   - `matched_note_id = ""`
   - unexplained reason.

For non-anomalous rows:

```text
flagged = "No"
matched_note_id = ""
reason = "No unusual cost rise detected relative to this route's history or similar routes."
```

---

## Step 9: Generate final CSV

Implement:

```text
src/output_writer.py
```

Rules:

- Exact column order.
- Blank strings for missing note ID.
- Correct rounding.
- Correct percentage strings.
- UTF-8 encoding.
- No pandas index.

Example:

```python
final.to_csv(
    "outputs/submission.csv",
    index=False,
    encoding="utf-8",
)
```

---

## Step 10: Run tests and evaluation

```bash
pytest tests/ -v
python scripts/run_eval.py
```

Expected outputs:

```text
outputs/eval_report.json
```

---

## Step 11: Run reproducibility check

```bash
python scripts/run_repro.py
```

Expected outputs:

```text
outputs/run_1/submission.csv
outputs/run_2/submission.csv
outputs/run_3/submission.csv
outputs/repro_report.txt
```

---

## Step 12: Generate token/cost log

```bash
python scripts/run_pipeline.py --log-cost
```

Expected output:

```text
outputs/token_cost_log.json
```

---

## Step 13: Write README and assumptions

Update:

```text
README.md
docs/assumptions.md
```

Include:

- Thresholds.
- Output row policy.
- Fewer than 8 prior weeks.
- Note windows.
- Repro results.
- Eval results.
- Cost log.

---

# 5. Recommended 24-hour execution timeline

This is a practical schedule.

## Hours 0–1: Setup

- Create repo.
- Install dependencies.
- Copy data.
- Read PDF and sample output.
- Write initial assumptions.

## Hours 1–3: Data profiling

- Load shipment records.
- Validate columns.
- Check dates, routes, route_type.
- Check invalid rows.
- Review context notes manually.

## Hours 3–6: Core numeric engine

- Route grouping.
- Monday week grouping.
- Weekly cost per tonne-km.
- Unit tests for grouping and formula.

## Hours 6–9: Baselines

- Own-history trailing average.
- Similar-routes peer average.
- Percentage strings.
- Unit tests for no look-ahead and peer exclusion.

## Hours 9–11: Flag policy

- Threshold config.
- Anomaly candidate logic.
- Check sample rows.
- Inspect flagged list.

## Hours 11–14: Notes and RAG

- Curate note registry.
- Define effective windows.
- Embed notes.
- Build retrieval query.
- Build validator.

## Hours 14–17: Explanation and output

- Reason templates.
- Output formatting.
- Rounding.
- Blank fields.
- Generate submission CSV.

## Hours 17–20: Evaluation and trust

- Unit tests.
- Golden rows.
- Negative controls.
- Manual spot-check justified rows.
- Eval report.

## Hours 20–22: Reproducibility and cost

- Three-run check.
- Diff report.
- Token/cost log.
- Fix any nondeterminism.

## Hours 22–24: README and demo prep

- README.
- Assumptions.
- Walkthrough notes.
- Final zip/repo.
- Final sanity check.

---

# 6. Risk register and mitigations

| Risk | Impact | Mitigation |
|---|---:|---|
| Ambiguous flag threshold | Flags may not match evaluator expectation | Use sample rows as anchors; document threshold; keep config tunable |
| Output row count ambiguity | Extra rows or missing rows may confuse grader | Default to all route-weeks; make output mode configurable; document assumption |
| Hallucinated justification | Fatal | Deterministic validator; only allow curated valid notes; negative-control tests |
| First-week baseline missing | Comparison fields unclear | Leave comparison blank; document; do not fabricate |
| Fewer than 8 prior weeks | Requirement-specific | Use all prior weeks; mention in README |
| Note date window ambiguity | Wrong-window citation | Curate effective windows from note text; conservative application |
| LLM nondeterminism | Output changes across runs | Use deterministic templates; if LLM used, temp=0 and compare core columns |
| Cost overrun | Irresponsible run | Use local embeddings/templates; log tokens; optional LLM only for stretch |
| Peer baseline unavailable | Cannot compare | Leave blank; do not fabricate; flag only if policy allows |
| Data anomalies | Crash or bad output | Data-quality validation and logging |
| CSV formatting mismatch | Cannot score | Strict output writer and schema test |
| Time pressure | Incomplete submission | Prioritize core logic, output, tests, README before stretch Q&A |

---

# 7. Revisit and verification against the uploaded files

Now I will revisit the files and requirements and verify whether any step or requirement is missing. I will explicitly add anything missing.

## 7.1 Verification against the PDF requirements

| Requirement from PDF | Covered in plan? | Added detail |
|---|---:|---|
| Group by route and route_type | Yes | Phase 2 |
| Use provided route_type, do not derive length buckets | Yes | Phase 2 and README |
| Track cost per tonne per km week by week | Yes | Phase 2 |
| Weeks Monday to Sunday | Yes | Phase 2 |
| `week_of` is Monday date | Yes | Phase 2 |
| Group shipment_date into weeks before computing | Yes | Phase 2 |
| Exact formula: total freight cost / (quantity × distance) | Yes | Phase 2 |
| Own-history trailing 8-week average | Yes | Phase 3.1 |
| Use only weeks strictly before current week | Yes | Phase 3.1 |
| If fewer than 8 prior weeks, use all available | Yes | Phase 3.1 and README |
| Say in README if fewer than 8 prior weeks are used | Yes | Phase 10 |
| No padding/extrapolation | Yes | Phase 3.1 |
| Similar-route average in same week | Yes | Phase 3.2 |
| Same route_type only | Yes | Phase 3.2 |
| Exclude route itself | Yes | Phase 3.2 |
| Flag rising/out-of-ordinary cost | Yes | Phase 4 |
| Check notes before final flag | Yes | Phase 5 |
| Use vector database/RAG | Yes | Phase 5 |
| Plain-English explanation | Yes | Phase 6 |
| Explanation backed by found notes, not made up | Yes | Phase 5/6 |
| Stretch: plain-English Q&A | Yes | Optional stretch section |
| Hallucination guardrails | Yes | Phase 5/7 |
| Justified verdict must cite exact note | Yes | Phase 6 |
| Note must apply to route and time | Yes | Phase 5 |
| Wrong route/window/no-effect note does not count | Yes | Phase 5/7 |
| No supporting note -> unexplained | Yes | Phase 6 |
| Do not guess | Yes | Phase 5/6 |
| Spot-check justified rows | Yes | Phase 7 |
| Lightweight eval harness/labeled set | Yes | Phase 7 |
| Show why system is right | Yes | Phase 7 |
| Three untouched runs identical flags/numbers | Yes | Phase 8 |
| Explanation wording may vary but verdict/numbers must not | Yes | Phase 8 |
| If random, state settings and show verdict stability | Yes | Phase 8 |
| Prefer open-source/free-tier | Yes | Phase 0 |
| Report tokens, outputs, calls, cost | Yes | Phase 9 |
| Output CSV matching sample format | Yes | Phase 6 |
| Column names/order/types are contract | Yes | Phase 6 |
| `matched_note_id` included and blank if unexplained | Yes | Phase 6 |
| Reason may be own words but must name note if justified | Yes | Phase 6 |
| Note ID not only in prose | Yes | Phase 6 |
| Hand in code | Yes | Phase 0/13 |
| Hand in output CSV | Yes | Phase 6 |
| Hand in README | Yes | Phase 10 |
| Hand in reproducibility check | Yes | Phase 8 |
| Hand in token/cost log | Yes | Phase 9 |
| 10-minute walkthrough | Yes | Phase 10 |

No major PDF requirement is missing.

---

## 7.2 Verification against `sample_output_format_v2.csv`

Sample columns:

```text
route,week_of,cost_per_tonne_km,vs_own_history,vs_similar_routes,flagged,matched_note_id,reason
```

Sample observations:

1. `route` uses `Origin-Destination`.
2. `week_of` is `YYYY-MM-DD`.
3. `cost_per_tonne_km` has 2 decimals.
4. `vs_own_history` is a string:
   ```text
   +35.5% vs this route's past average
   ```
5. `vs_similar_routes` is a string:
   ```text
   +21.0% vs similar-length routes this week
   ```
6. `flagged` can be:
   - `Yes`
   - `No (justified)`
7. `matched_note_id` is blank when unexplained.
8. `reason` contains note ID and date for justified rows.
9. Unexplained rows can mention closest note, but matched ID remains blank.

### Missing items added after checking sample

I added the following explicit implementation details:

- Use one decimal for percentages.
- Use two decimals for cost.
- Use exact suffix strings.
- Leave `matched_note_id` blank, not `None`.
- Use `No (justified)` exactly.
- Do not add extra columns.
- Do not include `route_type` in output.
- CSV quoting must handle commas in reason.
- Reason for justified rows must reflect note content and dates.
- If closest non-qualifying note is mentioned, it must not become `matched_note_id`.

---

## 7.3 Verification against `shipment_records.csv`

Important observations:

1. There are multiple routes:
   - Mumbai-Pune
   - Delhi-Jaipur
   - Chennai-Bangalore
   - Kolkata-Bhubaneswar
   - Ahmedabad-Mumbai
   - Mumbai-Delhi
   - Delhi-Chennai

2. Delhi-Chennai appears later and has route_type `Long`.

3. Dates span from 2024-01-01 to late 2025.

4. Route_type is already provided.

5. Materials and transporters are present but not required for the core logic.

### Missing items added after checking shipment data

I added these steps:

- Explicitly include Delhi-Chennai in the route list.
- Ensure new routes with limited history are handled.
- Ensure first week of a route has blank own-history comparison.
- Ensure peer baseline handles cases where a route_type has few routes.
- Ensure later-appearing routes do not cause errors.
- Ignore material and transporter for graded core logic, but allow them for diagnostics.
- Validate positive quantity and distance before computing tonne-km.
- Handle leap day `2024-02-29`.
- Use timezone-naive dates.
- Do not combine routes with different origins/destinations.
- Do not combine reverse-direction routes unless they are identical in the data.

---

## 7.4 Verification against `context_notes.csv`

Important observations:

1. Some notes are positive explanations:
   - N001 flooding.
   - N002 festival surcharge.
   - N003 diesel price rise.

2. Some notes are traps:
   - N004 says affected routes are not part of dataset.
   - N005 says costs not significantly affected.
   - N006 says stable/no disruptions.
   - N008 says no disruptions.
   - N010 says costs absorbed, no rate change.

3. Some notes are route-specific:
   - N001 Chennai-Bangalore.
   - N002 Ahmedabad-Mumbai.
   - N005 Mumbai-Delhi.
   - N007 Delhi-Jaipur.
   - N008 Kolkata-Bhubaneswar.
   - N009 Chennai-Bangalore.

4. Some notes apply to all routes:
   - N003.
   - N004.
   - N006.
   - N010.

### Missing items added after checking notes

I added these steps:

- Build a curated note registry.
- Mark negative/no-effect notes as `can_justify=false`.
- Add negative-control tests for every no-effect note.
- Treat `N004` as never justifying despite `All Routes`.
- Treat `N007` as not justifying cost rise because improved roads do not explain higher cost.
- Treat `N009` as normalization after floods, not a cost-rise justification.
- Define conservative effective windows for notes whose duration is implied but not explicit.
- Add magnitude compatibility for N003 because it says roughly 5–7%.
- Ensure all-route notes are lower priority than route-specific notes.
- Ensure justified reason includes note date and content.
- Ensure no unsupported note becomes `matched_note_id`.

---

# 8. Additional edge cases that must be handled

These are easy to miss, so they should be explicitly implemented.

## 8.1 First week of a route

Problem:

- No own-history baseline exists.

Solution:

- Compute cost.
- Leave `vs_own_history` blank.
- Use peer comparison if available.
- Do not flag based on own history.
- Only flag if peer comparison is extremely high, according to config.
- Document in README.

## 8.2 Route with fewer than 8 prior weeks

Solution:

- Use all prior weeks.
- README must state this.
- No padding.

## 8.3 Missing peer routes

Problem:

- No other route of same route_type in that week.

Solution:

- Leave `vs_similar_routes` blank.
- Do not fabricate peer baseline.
- Flag only based on own-history if available.

## 8.4 Zero or invalid tonne-km

Problem:

- Division by zero.

Solution:

- Exclude invalid shipment rows from weekly aggregation.
- Log excluded rows.
- If a route-week has no valid tonne-km, do not output a cost row.

## 8.5 Duplicate shipment IDs

Solution:

- Check duplicates.
- If duplicates are exact identical rows, decide whether to drop or keep.
- Recommended: keep unless exact duplicate rows indicate data duplication; log decision.
- Document assumption.

## 8.6 Missing values

Solution:

- Missing cost, quantity, distance, date, origin, destination, or route_type should be logged and excluded from numeric computation.
- Do not impute values.

## 8.7 Notes with no clear end date

Solution:

- Use conservative effective windows.
- Document assumptions.
- Avoid applying notes far outside their natural event window.

## 8.8 All-route notes

Solution:

- Apply to every route only if the note truly supports cost increase.
- Do not use all-route no-effect notes.
- Rank route-specific notes higher.

## 8.9 LLM failure

If optional LLM is used:

- If LLM returns invalid note ID, reject.
- If LLM returns malformed JSON, fallback to template.
- If LLM times out, fallback to template.
- Never let LLM create a note ID not in the validated candidate list.

---

# 9. Recommended final assumptions to document

These should be written in README and/or `docs/assumptions.md`.

1. Output contains one row per valid route-week.
2. First week of a route has blank own-history comparison.
3. If fewer than 8 prior weeks exist, all available prior weeks are used.
4. No padding or extrapolation is used.
5. Peer baseline is the unweighted average of peer route-week costs.
6. Own-history baseline is the unweighted average of up to 8 prior route-week costs.
7. Weekly cost per tonne-km is calculated from summed cost divided by summed tonne-km.
8. `route_type` is used as given.
9. Flag thresholds are chosen by us because the brief does not prescribe them.
10. Final flag thresholds are stored in config.
11. A justified row means an applicable, cost-increasing note was found and validated.
12. Notes that say costs were unaffected cannot justify a rise.
13. `matched_note_id` is blank for unexplained rows.
14. Output rows are sorted by route and week.
15. Rounding is only applied at output time.
16. Deterministic templates are used for final explanation unless otherwise stated.
17. If LLM is used, temperature is 0 and only wording may vary.
18. The sample output file is treated as a format contract, not necessarily the full expected row count.

---

# 10. Final submission checklist

Before submitting, verify:

## Code

- [ ] Code runs from raw input to final CSV.
- [ ] Code is organized into modules.
- [ ] Config controls thresholds and paths.
- [ ] No hardcoded secrets or paths.
- [ ] Tests exist and pass.

## Core logic

- [ ] Routes grouped correctly.
- [ ] Weeks start Monday.
- [ ] Cost formula correct.
- [ ] Own-history baseline exact.
- [ ] Similar-routes baseline exact.
- [ ] No look-ahead.
- [ ] No padding.
- [ ] Fewer-than-8-week rule implemented.

## Output

- [ ] Columns exactly match sample.
- [ ] Column order exact.
- [ ] Cost rounded to 2 decimals.
- [ ] Percentages one decimal.
- [ ] Exact percentage suffixes.
- [ ] Flag values exact.
- [ ] `matched_note_id` blank when unexplained.
- [ ] Reason grounded.
- [ ] CSV opens cleanly.
- [ ] No pandas index column.

## AI/justification

- [ ] Retrieval implemented.
- [ ] Notes embedded.
- [ ] Justification validated by rules.
- [ ] No-effect notes cannot justify.
- [ ] Wrong-route notes cannot justify.
- [ ] Wrong-time notes cannot justify.
- [ ] Every justified row cites exact note.
- [ ] Every justified row’s note applies to route and week.

## Trust

- [ ] Unit tests pass.
- [ ] Golden rows checked.
- [ ] Negative-control tests pass.
- [ ] Manual spot-check done.
- [ ] Eval report saved.

## Reproducibility

- [ ] Three runs completed.
- [ ] Core columns identical.
- [ ] Repro report saved.
- [ ] Randomness documented.
- [ ] Temperature documented if LLM used.

## Cost

- [ ] Token/cost log saved.
- [ ] Number of LLM calls reported.
- [ ] Input/output tokens reported.
- [ ] Cost estimate reported.
- [ ] Open-source/free tools used.

## Documentation

- [ ] README complete.
- [ ] Assumptions documented.
- [ ] Thresholds explained.
- [ ] Fewer-than-8-week statement included.
- [ ] Walkthrough notes prepared.

---

# 11. Final recommended approach

The safest implementation is:

1. Use deterministic pandas logic for all numeric fields.
2. Use exact baseline definitions from the PDF.
3. Use a transparent threshold policy anchored to the sample output.
4. Use local embedding retrieval for notes.
5. Use a strict rule-based validator before allowing any note to justify a rise.
6. Use deterministic templates for the final CSV explanation.
7. Keep LLM optional and only for stretch Q&A.
8. Produce a full evaluation, reproducibility, and cost log.
9. Document every assumption clearly.

This gives you a system that is not only working, but also trustworthy, reproducible, cheap, and aligned with the case study’s guardrails.