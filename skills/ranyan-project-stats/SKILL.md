---
name: ranyan-project-stats
description: >
  Pull and interpret Ranyan's operation stats via the Ranyan MCP server.
  The three project-bound stats — called "project-stats" or
  "jobsite-stats" — are budget, work orders and inspections; in
  combination they produce the analytical read an operations team uses to
  point attention where improvement is needed. Also covers project health
  scores (one per project, sweepable tenant-wide) and inspection coverage
  (which sites are being inspected at all). Use when the user asks for
  stats for a site or project, how a job site is performing, account
  health, margins, unbilled tag jobs, inspection failures or remediation,
  or which sites never get inspected. In Ranyan, "job site" and "project"
  are the same entity — never ask which one is meant.
---

# Ranyan project / jobsite stats

A customer can drop an ongoing contract without warning, so the point of a
stats report is to surface the signals early — not just to recite numbers.

**Prerequisite:** the Ranyan MCP server must be connected (endpoint and
credentials come from your Ranyan admin). Tool names below are bare MCP
names; most hosts prefix them (e.g. `mcp__ranyan__list_projects`). If the
tools are missing, say so and stop — never invent numbers.

## Naming & ask routing

- **"Project-stats" = "jobsite-stats"** — the three operation stats bound
  to a project/job site: **Budget + Work Orders + Inspections**.
- **Single stat named** ("get me the work order stats for Job Site A") →
  run ONLY that tool and return ONLY what was asked; once the result is
  delivered, you MAY offer the other stats as a follow-up question — never
  pre-run them.
- **Open-ended site check** ("what's going on at <site>", "site stats for
  <site>") → run the full trio (+ the health score) and synthesize the
  combined read below.
- Retention or contract-dispute analysis → compare full months: call each
  stats tool once per month and synthesize the deltas (margin trend,
  complaint history, remediation track record over time).

## Retrieval basics (all five tools)

1. Stats bind to the project **UUID**, not the name — resolve first with
   `list_projects(q=<name or site number>)`; exact-name match wins,
   ambiguous → ask.
2. `month` params are `YYYY-MM`; omitting means the current month — a
   **running (partial) snapshot**. Always state which month a report
   covers and its `mode` (`running` | `actual` | `future`); never present
   running-month numbers as final.
3. All five accept `timezone` (IANA) — pass the branch's zone; the host
   default can push near-midnight records across month boundaries.
4. **Sweep pitfall:** `list_projects` paginates (`page`/`limit`, limit
   ≤100; a single default page may cover only ~20 of 200+ sites). For
   tenant-wide sweeps, take the full roster from `get_inspection_coverage`
   (it returns every project in one call) or page `list_projects` until
   exhausted — a single page silently misses most sites.

## The three operation stats (project-bound)

### Budget — `get_budget_stats(projectId[, month, budgetTypeId, payOption, timezone])`

- The ESTIMATE from the contract budget, the ACTUAL from time logs, and the
  VARIANCE between them — per tenant-defined budget type (Porter, Night
  Janitor, …) and rolled up. Report from `totals.estimate` plus per
  `budgetTypes[]`: revenue, `totalCOGS`, `grossMargin` (value, % and
  score), worker slots (position, hrs/wk, hourly wage, monthly cost), PTI,
  supplies, uniforms, `laborRatio`. Exact estimate keys:
  `estimatedPTI`/`estimatedPTIPercentage`, `projectedSupplyCost(+
  Percentage)`, `paperSupplies`, `totalUniformCost`,
  `averageHealthAndWelfare`, `benefits`, `overhead`, `pricePerSquareFoot`,
  `occupiedSquareFootage`, `cleanerProductionRate`, `laborRatio`,
  `workers[]` (hours, hourlyWage, monthlyHours, monthlyCost). The app's
  project-level "code" and "service code" fields are not exposed via MCP —
  only the budget-level PTI percentages exist server-side.
- **ACTUAL is LABOUR-ONLY.** Non-labour COGS is carried unchanged from the
  estimate and flagged `nonLabourBasis: "estimate"` — always report it as a
  LABOUR variance, never a full cost variance.
- `labourCost`/`labourHours` include BOTH approved and unapproved
  (`approvedLabour` = paid, `unapprovedLabour` = still to be paid — normal
  mid-period state, NOT a problem). Never subtract unapproved, never quote
  `approvedLabour` alone.
- `variance` = actual − estimate: positive on cost = OVER budget; positive
  on margin = better than planned.
- Check before concluding: `unattributedLabour` (time from employees holding
  slots under more than one budget type — counts in the project total, in no
  per-type figure); `nonOperationalBudgetTypes` (earn no revenue, excluded);
  `warnings: no_pay_rate` (hours costed at $0 → actual UNDERSTATED).
- **Phantom-margin trap:** where little or no time is logged yet, actual
  labour reads near $0 and margins read absurdly good (an estimated 45%
  margin can show up as a 95% "actual"). Flag this whenever
  actuals/variances are quoted. On tenants where actuals are not populated
  at all (`actualsAvailable: false`), say "actuals not available yet" and
  report the estimate only.

### Work Orders — `get_work_order_stats(projectId[, month, compare])`

- Complaints total plus recurring service types; Tag Jobs (chargeable work
  outside the contract) current vs previous counts, value and delta
  (`compare` defaults on). A "complaint" = a work order under the tenant's
  complaint work type (name-based configuration — see the
  `ranyan-work-orders` skill).
- Headline metric: **`unbilled`** (orders + `quotedNotInvoiced`). Its
  `detail[]` list is a ready-made billing worklist — each entry can be
  closed out with `set_work_order_cost` / `set_work_order_invoice`. A zero
  is also newsworthy.
- **Pitfall: `unbilled` is scoped to the queried month.** A current-month
  zero can hide older leakage — a site can report 0 unbilled this month
  while prior-month tag jobs remain uninvoiced. For a real
  outstanding-balance view, run past months or list the work orders
  directly.

### Inspections — `get_inspection_stats(projectId[, month, categoryId])`

- `completed` count plus `byCategory`; items inspected/passed/failed and
  `failureRate`; remediation completed/outstanding/rate; assignment status
  (unassigned failures mean nobody owns the fix list); `repeatFailures`
  (consecutive count = chronic).
- When remediation `rate` is 0 or null, check `noRemediationReason`
  **before** drawing a conclusion:
  - `not-configured` → the tenant never set up an inspection work type, so
    no remediation work orders are generated at all — a setup gap, NOT
    performance;
  - `legacy-unlinked` → work orders exist but aren't linked to the
    inspection;
  - `none-failed` → nothing failed, so nothing to fix.
  Only a rate with a null reason is a genuine performance number.

## Tenant-wide / cross-project stats

### Project Health — `get_project_health(projectId[, timezone])`

- One 0–100 figure weighting three components: the average inspection score,
  the complaint work-order score per month, and the budget gross-margin
  score. The tenant's own weighting is echoed in `weights`, so the number
  matches what the project screen shows.
- The result key is **`health`** (top level) — not `score`. `components`
  carries the workings: `inspection.categories[]` (category, score,
  sampled), `workOrder.months[]` (month, complaints, score), `budget`
  (grossMarginPercentage, revenue). Use them to EXPLAIN a low score, not
  just report it.
- **Trap:** a category with no inspections is not sampled — an inspection
  score of 0 with empty `categories` means NEVER inspected, not inspected
  badly. Cross-check coverage before ranking such sites worst.
- Tenant-wide health view = sweep: coverage roster → `get_project_health`
  per project → rank ascending.

### Inspection Coverage — `get_inspection_coverage([sinceDays, timezone])`

- Tenant-wide list: `{projectId, projectName, lastInspectedAt,
  daysSinceLastInspection, inspectionsInPeriod}`; **never-inspected
  projects are returned first**. `sinceDays` sets the counting window
  (default 90).
- Purpose: a project with no inspection findings may simply be one nobody
  has inspected — invisible to every other inspection statistic. This tool
  makes those gaps countable.
- Side benefit: it is a full project roster in one call — the cheapest
  starting point for tenant-wide sweeps.

## The combined read — where ops should point attention

For a site, run the trio (+ health for the single figure) and synthesize in
this order; each maps to a concrete action:

1. **Never-inspected / stale coverage** → invisible to QA entirely; schedule
   an inspection FIRST — data before judgment.
2. **Inspection failures with outstanding or unassigned remediation** →
   visible service failure; assign owners to the fix list.
3. **Chronic repeat failures (same category)** → systematic cleaning
   problem, not a one-off.
4. **Recurring complaint service types** → what the customer actually
   notices; target improvement here.
5. **Unbilled Tag Jobs** → revenue leakage; `detail[]` is the billing
   worklist.
6. **Margin + labour variance** → contract economics (mind the labour-only
   and phantom-margin traps).
7. **Health score** → the tenant's own weighted rollup of 1–6; use it to
   RANK across sites when deciding where attention goes first.

For multi-site asks: sweep health + coverage across the roster, rank health
ascending — but treat never-inspected sites as "unknown", not "worst".

## Delivery

1. Crisp text report first: the figures, then 1–2 watch-outs or action
   items. Lead the combined read with churn-risk signals — complaint trend,
   chronic failures, unowned remediation, unbilled work, margin health, time
   since last inspection.
2. **Offer — don't assume** — the deeper formats: the last full month, a
   multi-month trend, or a written report for the customer file (some hosts
   can also read the summary aloud on request).
3. Stay inside the documented tool shapes. A field not described here gets
   reported raw or called undocumented.

## Example flow

"Inspection stats for a site" → `list_projects(q="<site>")` →
`get_inspection_stats(<uuid>)` →

> 2 QA inspections (September, running month). 54/60 items passed (10%
> fail). 5 remediation work orders raised, 2 done, 3 outstanding — all
> unassigned. "Restrooms" failed its 3rd consecutive inspection (chronic).
> Want last month's full numbers, or a budget + work-order read for the
> same site?
