---
name: ranyan-inspections
description: >
  The inspection quality module in Ranyan (a Janitorial Management
  System): supervisor-performed on-site inspections built from custom
  types (templates of areas and items), two-level pass/fail scoring, the
  auto-generated remediation work orders that carry photos, notes and an
  inherited employee, and how to read the inspection stats and coverage
  tools on the Ranyan MCP server. Use when the user asks about
  inspections, QA scores, failed items, remediation status, repeat or
  chronic failures, inspection assignments, or which sites never get
  inspected.
---

# Ranyan Inspections — the quality module

An inspection is a routine on-site task performed **by the supervisor in
the web app** to ensure work is done right and catch places needing
rework, for client satisfaction. A work order's `inreview` verification
by management is a **different action** — never conflate the two. The
inspection module has a **stats-only MCP surface** (no session create or
read): `get_inspection_stats`, `get_inspection_coverage`, and the health
component of `get_project_health` are the only windows into it — this
skill is how to read them correctly.

**Prerequisite:** the Ranyan MCP server must be connected (endpoint and
credentials come from your Ranyan admin). Tool names are bare MCP names;
most hosts prefix them. If the tools are missing, say so and stop — never
invent numbers.

## Model (all custom-built by the tenant, in the app UI)

- **Categories** — grouping of inspections (e.g. QA, Training).
- **Types** — inspection TEMPLATES custom-made by management, bundling
  areas and their items.
- **Areas** — the area/object inspected (Lobby, Restroom…); **Items** —
  the particular checks within an area (Table top, Chairs…).
- Setup path: **Settings → core setup → inspection** → categories / areas
  / items.
- A Type is a template — not every area or item applies at every visit.
  Supervisors skip non-applicable rows; those count as
  `items.notInspected`, which means **"doesn't apply", NOT "forgot to
  inspect"**. Never report skips as misses.

## Scoring — a two-level average

Items are pass/fail. The area score combines and averages its items; the
overall result averages again across all areas. Health sampling uses the
average score of the last few completed inspections per category.

## Remediation chain — the engine link to work orders

- A failed item auto-generates a **work order** as the actionable item —
  through the work type + service configured on the inspection/training
  Type (e.g. one named "Needs Action"). Both Inspection and Training
  types generate work orders.
- The failed item's **photos and notes are carried onto the generated
  work order** so the employee can act on them — this is where much of a
  WO's images/comments come from.
- Assigning an employee to a failed item is **optional**; if one is
  recorded on the item, the generated WO **inherits that employee**.
  Otherwise the WO lands **unassigned**. Empty assignment columns across a
  whole month (`assignment.unassigned` = every failure) means the fix
  list has no owner — flag it in any inspection report; unowned
  remediation is a visible service-failure risk.
- `remediation.rate` = completed ÷ failed. Before judging a 0/null rate,
  check `noRemediationReason`: `not-configured` (setup gap — the type's
  work type/service was never wired, so no WOs exist at all),
  `legacy-unlinked`, `none-failed`. Only a rate with a null reason is
  real performance.

## Stats response shape (what each field means)

```
inspections: { completed, byCategory[]:{categoryId,name,inspections} }
items:       { inspected, passed, failed, notInspected, failureRate }
remediation: { failed, withWorkOrder, completed, outstanding,
               rate, noRemediationReason, orphaned[] }
assignment:  { toUser, toEmployee, unassigned }   # same app-user vs
                                                  # site-employee split as WOs
repeatFailures: [{ itemId, name, consecutiveInspections, lastFailedAt }]
warnings: []
```

- `repeatFailures.consecutiveInspections` is a CONSECUTIVE count — the
  chronic problem signal.
- When the chain is configured, `failed == withWorkOrder`; a gap points
  at setup trouble, not staff behaviour.

## Coverage (tenant-wide)

`get_inspection_coverage([sinceDays])` returns days-since-last-inspection
per project with **never-inspected projects first** — and doubles as the
full project roster for sweeps. A project with no findings may simply be
one nobody has inspected; such projects are invisible to every other
inspection statistic. "Data before judgment": schedule the inspection
before scoring the site.

## Report pattern

Completed count (with category), pass/fail with `failureRate` (state the
month and running/partial mode), remediation outstanding and rate (with
the reason-check), **assignment status — owned vs unowned fix lists**,
chronic repeat failures, and days since last inspection. Lead
watch-outs with unassigned percentage and stale/never coverage.

## Example flow

"How is QA at <site> this month?" → `get_inspection_coverage` (is it even
being inspected?) → `get_inspection_stats(projectId, month)` →

> 3 QA inspections completed, 44/47 items passed (6% fail). Two failures
> raised remediation work orders — one done, one still outstanding and
> unassigned, so nobody owns that fix. No chronic items this window. Want
> last month for trend, or the work-order read for the same site?

## Not documented — do not assert

- What populates `remediation.orphaned[]` (presumed unlinked remediation
  WOs — confirm before interpreting).
- Whether any scheduled/recurring inspection concept exists vs purely
  ad-hoc supervisor runs.
- How the Training module relates to Training-type inspections.
