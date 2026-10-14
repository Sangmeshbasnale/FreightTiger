# FreightTiger Shipping Cost Assistant: Assumptions & Design Decisions

This document formally captures all operational assumptions, edge-case treatments, and architectural choices implemented in accordance with `plan.md`.

---

## 1. Output Scope & Row Selection
- **One row per valid route-week**: The primary submission output (`outputs/submission.csv`) outputs one row for every valid route-week (728 rows across 104 calendar weeks).
- **Configurable output mode**: The system supports both `all_route_weeks` (default) and `anomalies_only` via `config.yaml` (`output.mode`).

---

## 2. Baseline & History Handling
- **Strictly Trailing Window**: The own-history baseline uses an unweighted trailing average of up to 8 prior weeks strictly before the current week (`shift(1)`), preventing data leakage.
- **Fewer than 8 Prior Weeks**: When a route has fewer than 8 prior weeks (e.g. week 2, 3, 4), all available prior weeks are used. No padding, interpolation, or synthetic extrapolation is performed.
- **First Week (No History)**: The first week of any route has no prior history. The `vs_own_history` field is left empty (`""`). It is evaluated for an anomaly only if peer comparisons are exceptionally high.
- **Peer Route Comparison**: Peer comparison averages all other routes sharing the exact same `route_type` (`Short`, `Medium`, `Long`) in the same `week_of`, strictly excluding the route itself. If no peer exists, the field is left empty (`""`).
- **Route Length Buckets**: The supplied `route_type` is used directly as specified in the case study brief; no custom distance bins are invented.

---

## 3. Weekly Aggregation Formula
- **Week Boundaries**: Weeks run Monday to Sunday. `week_of` represents the Monday date (`YYYY-MM-DD`).
- **Cost Calculation**:
  $$\text{cost\_per\_tonne\_km} = \frac{\sum \text{freight\_cost\_inr}}{\sum (\text{quantity\_tonnes} \times \text{distance\_km})}$$
  Aggregated from group sums, never an average of individual shipment rates.

---

## 4. Context Notes Justification & Guardrails
- **Whitelist**: Only `N001`, `N002`, and `N003` describe authentic, quantifiable cost-increasing events applicable to this dataset.
- **Trap Notes**: Notes `N004`, `N005`, `N006`, `N007`, `N008`, `N009`, and `N010` describe unaffected costs, normal conditions, or out-of-dataset routes, and are barred from justifying cost rises.
- **Date Overlap**: A note applies to a route-week if and only if:
  $$\text{week\_start} \le \text{note\_end} \quad \text{and} \quad \text{week\_end} \ge \text{note\_start}$$
- **Matched Note ID**: Stored as the exact note ID (e.g. `N002`) for justified rows, and an empty string (`""`) for unexplained or normal rows.

---

## 5. Determinism & Zero-Cost Architecture
- **Deterministic Reason Formatting**: To ensure 100% reproducible results across runs, explanations use grounded deterministic templates anchored to the retrieved context notes.
- **100% Free & Open-Source Stack**: Local embeddings (`all-MiniLM-L6-v2`) via `sentence-transformers` and `faiss-cpu`. Zero cloud APIs or paid services are required.
- **Rounding Rule**: Unrounded values are maintained throughout all intermediate calculations and only formatted to 2 decimals for cost and 1 decimal for percentage strings at output generation.
