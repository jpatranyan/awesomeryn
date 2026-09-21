---
name: ranyan-budget-stats
description: >
  Pull and interpret job-site stats from Ranyan (a Janitorial Management
  System) via the Ranyan MCP server: budget, work orders, and inspections.
  Use when the user asks how a site or project is performing, wants a stats
  report, asks about margins, unbilled tag jobs or billing leakage,
  inspection failures or remediation, or reviews account health and
  churn/contract risk. In Ranyan, "job site" and "project" are the same
  entity — never ask which one is meant.
---

# Ranyan job-site stats

Turn the Ranyan MCP stats tools into a readable account-health report.
A customer can drop an ongoing contract without warning, so the point of a
stats report is to surface the signals early — not just to recite numbers.

**Prerequisite:** the Ranyan MCP server must be connected (endpoint and
credentials come from your Ranyan admin). Tool names below are bare MCP
names; most hosts prefix them (e.g. `mcp__ranyan__list_projects`). If the
tools are missing, say so and stop — never invent numbers.

## Common steps

1. **Resolve the site to its UUID** with `list_projects(q=<name or site
   number>)` and take the exact-name match's `id`. Every stats tool needs
   the UUID, not the name. Ambiguous match → ask.
2. `month` parameters are `YYYY-MM`; omitting them means the current month.
   **Always state which month a report covers**, and flag that a
   current-month report is a running (partial) snapshot.
3. For an account-health read, run **all** relevant stat tools (budget +
   work orders + inspections), not only the one named, and lead the
   synthesis with **churn-risk signals**: complaint trend, chronic repeat
   inspection failures, outstanding or unassigned remediation (poor
   follow-up is a visible service failure), unbilled tag jobs (revenue
   leakage), margin health, and time since the last inspection
   (`get_inspection_coverage`).
4. For retention or contract-dispute analysis, compare full months: call
   each stats tool once per month and synthesize the deltas (margin trend,
   complaint history, remediation track record over time).

## Budget — `get_budget_stats(projectId[, month, budgetTypeId])`

- Report from `totals.estimate` plus per `budgetTypes[]`: revenue,
  `totalCOGS`, `grossMargin` (value, %, and score), worker slots (position,
  hrs/wk, hourly wage, monthly cost), PTI, supplies, uniforms, `laborRatio`.
- **Never report a variance**: actuals are not populated yet
  (`actualsAvailable: false`). Say "actuals not available yet" instead.

## Work orders — `get_work_order_stats(projectId[, month, compare])`

- Complaints total plus recurring service types; tag jobs current vs
  previous counts, value, and delta.
- Headline metric: `unbilled` (orders + `quotedNotInvoiced`). Its
  `detail[]` list is a ready-made billing worklist — each entry can be
  closed out with `set_work_order_cost` / `set_work_order_invoice`. A zero
  is also newsworthy.
- **Pitfall: `unbilled` is scoped to the queried month.** A current-month
  zero can hide older leakage — a site can report 0 unbilled this month
  while prior-month tag jobs remain uninvoiced. For a real
  outstanding-balance view, run past months or list the work orders
  directly.

## Inspections — `get_inspection_stats(projectId[, month, categoryId])`

- `completed` count plus `byCategory`; items inspected/passed/failed and
  `failureRate`; remediation completed/outstanding/rate; assignment status
  (unassigned failures mean nobody owns the fix list); `repeatFailures`
  (consecutive count = chronic).
- When remediation `rate` is 0 or null, check `noRemediationReason`
  **before** drawing a conclusion:
  - `not-configured` → tenant setup gap, not site performance;
  - `legacy-unlinked` → work orders exist but aren't linked to the
    inspection;
  - `none-failed` → nothing failed, so there is nothing to fix.
  Only a rate with a null reason is a genuine performance number.

## Tenant-wide tools

- `get_inspection_coverage` — how long since each project was last
  inspected; feeds the churn-risk read.
- `get_monitoring_summary` — tenant operational snapshot.

## Delivery

1. Crisp text report first: the figures, then 1–2 watch-outs or action
   items. Never present running-month numbers as final.
2. **Offer — don't assume** — the deeper formats: the last full month, a
   multi-month trend, or a written report for the customer file (some
   hosts can also read the summary aloud on request).
3. Stay inside the documented tool shapes. If a field isn't described
   here, report it raw or say it isn't documented — same rule as `ryn`.

## Example flow

"Inspection stats for a site" → `list_projects(q="<site>")` →
`get_inspection_stats(<uuid>)` →

> 2 QA inspections (September, running month). 61/67 items passed (9%
> fail). 6 remediation work orders raised, 2 done, 4 outstanding — all
> unassigned. "Walls & Partitions" failed its 4th consecutive inspection
> (chronic). Want last month's full numbers, or a budget + work-order
> read for the same site?
