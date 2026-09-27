---
name: ranyan
description: >
  Time tracking in Ranyan (a Janitorial Management System) via the Ranyan
  MCP server: time logs — rendered hours and shift punch data — and
  attestations, the affirmations employees answer before or after each
  shift. Use when the user asks for time logs, hours worked, who worked on
  a date or date range, clock-in/clock-out or shift records, attestation
  logs, or who missed an attestation. Also covers time-log data-model
  terminology and what to do when a host's MCP tool catalog is stale.
---

# Ranyan time logs & attestations

The trap in this module is vocabulary, not arithmetic: "time log" means two
different things, and attestation reasons must not be interchanged. A wrong
reading here misattributes payroll and blames employees for setup gaps.

**Prerequisite:** the Ranyan MCP server must be connected (endpoint and
credentials come from your Ranyan admin). Tool names below are bare MCP
names; most hosts prefix them (e.g. `mcp__ranyan__get_time_logs`). If the
tools are missing, say so and stop — never invent numbers.

## Data model

- A **time log is a collection of shifts**. Its items *are* the shifts —
  each carrying clock-in, clock-out and break punches.
- An **attestation is a set of custom questions defined by the management
  operating the system** (tenants differ — anything below is an example,
  never a standard), asked **before or after each shift**, at clock in and
  clock out. E.g. at start: "is the employee fit to work?" — at end: "was
  the job done right?". The employee is expected to **affirm** them:
  declarations, not surveys.
- So "time log" can mean the **rendered time** (costed hours) or the
  **punch-level shift data**. Be mindful of the term; when an ask could mean
  either, state which sense you are answering.

## Time-log tools — exactly TWO, do not confuse

1. `get_time_logs` — **tenant-wide or multiple employees.** `employeeId` is
   an optional array; omit it for everyone who worked in the period. Use for
   any "time logs for <date/period>" ask that does not name a person.
2. `get_employee_time_logs` — **one single employee** (`id`, required UUID).
   Resolve a name with `list_employees` first.

Otherwise identical: period via `month` (`YYYY-MM`) or `from`+`to`;
`timezone` (IANA — pass the branch's zone; the default US/Los Angeles can
push near-midnight work across a period boundary); `payOption` (default
'Flexible': 8h daily regular then overtime, plus sixth/seventh-day premiums
counted on days actually worked).

Reading the results:

- `totals` = approved + unapproved. **Unapproved = not yet cut off, still to
  be paid** — a normal mid-period state. Never subtract it from the total
  and never quote approved alone.
- `lines` are **costing units** split at pay-band changes — NOT punches.
  Never present them as clock in/out records, and never count lines as days.
- `warnings: no_pay_rate` — hours costed at $0; the money is UNDERSTATED.
  Report hours, not cost.
- Many employees have no data in a period. Quote what the tool returns for
  the person or period asked — never infer a tenant-wide truth from one
  site's zero.

## Attestation tools — `get_attestation_logs`, `get_missing_attestations`

Identical params on both: `employeeId` optional — a **named person** means a
single-employee record (resolve via `list_employees`); omitting it returns
**everything in the period, tenant-wide**. Period via `date` (a single day —
do NOT combine with `month`/`from`/`to`), `month`, or `from`+`to`. Pass
`timezone` when you know the branch zone.

- `get_attestation_logs` returns only shifts that HAVE answers: grouped
  shift → attestation → questions, each with the `answer` given, `clockType`
  (clock-in / clock-out), `answeredAt`, and `incorrect`.
- The entry `date` is the **time log's shift date** — the only thing the
  period filters on, and the day you report. `answeredAt` can cross midnight:
  a shift dated the 25th can carry clock-out answers typed on the 26th.
  Never present `answeredAt` as the day worked.
- `incorrect: true` = the answer matched the question's configured problem
  answers — the affirmation broke (unfit to work, job not done right, missed
  meal break). Surface these first, framed as declarations, not data noise.
- `get_missing_attestations` returns shifts with NO answers at all, each
  labelled with a `reason`. The two reasons are NOT interchangeable — they
  decide who to chase:
  - **"No Clock Out"** — the employee punched in and never punched out, so
    the clock-out questions were never reached. A TIME-KEEPING problem: chase
    the employee or fix the punch (`clockOut` is null on these).
  - **"Attestation Not Set Up"** — a clean in-and-out shift where nothing was
    asked: the project has no attestation wired into the mobile app. A SETUP
    problem — fix the configuration (`projects[]` says where the work was
    rendered). **Never report these as the employee failing to answer.**
- Break punches are excluded throughout: attestations are asked at the clock
  in and the clock out. Quote `totals` (`shifts`, `noClockOut`, `notSetUp`)
  rather than counting rows.

## Reporting

1. Crisp text first: the figures — state the period, the timezone, and the
   approved/unapproved split — then 1–2 watch-outs or action items.
2. **Offer — don't assume** — the deeper asks: another period, per-employee
   detail, a written report for the file (some hosts can also read the
   summary aloud on request).
3. Stay inside the documented tool shapes. A field not described here gets
   reported raw or called undocumented.

## Tool-ops pitfalls

- The server evolves; a host's MCP tool catalog can lag in BOTH directions —
  missing new tools, still listing removed ones. A server-side "tool not
  found" is **permanent**, not transient — do not retry it; verify against a
  live tools list where possible, answer with the current equivalent, and
  name the change.
- The old punch/shift-log module (list/get shift time logs, direct punch
  records) was **intentionally removed** by Ranyan. The tools above are the
  current path; shift-level punch data surfaces through the attestation
  tools and `get_shifts` (`clockIn`/`clockOut` per shift).
- If ALL Ranyan tools vanish mid-session, the host may have parked the
  server after an outage: probe the endpoint — 5xx = still down (report
  honestly); 401/403 = up but re-registration pending (reload or reconnect
  the MCP server per your host's flow). OAuth access tokens are short-lived
  (~1 h): on a 401 with direct API calls, try the refresh-token grant before
  assuming re-authentication is needed.

## Example flow

"time logs for Sep 25" (no person named) → `get_time_logs(from="2026-09-25",
to="2026-09-25")` →

> N employees across N sites, X h / $Y — a sliver of it overtime, all on
> unapproved lines: nothing in the day has reached its cut-off, so all of it
> is still to be paid. Attestations for the same day: shifts that were asked
> answered clean; one shift shows "Attestation Not Set Up" at its project —
> a configuration gap, not an employee failure. Want per-employee detail,
> or the attestation answers verbatim?

A named ask routes to the single-employee tool — "what did Riley Sands work
this month?" (fabricated example name, cross-checked against the live
employee roster; docs must always use made-up names, never real staff) →
`list_employees(q="Riley Sands")` to get the UUID →
`get_employee_time_logs(id, month="2026-09")`.
