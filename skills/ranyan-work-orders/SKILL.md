---
name: ranyan-work-orders
description: >
  The work-order operation engine in Ranyan (a Janitorial Management
  System) via the Ranyan MCP server: what must be set up first (project,
  service types, work types and their links), the worker-vs-employee
  assignment model, the status lifecycle (open, inreview, completed,
  billed, system-managed past_due), Tag Jobs and the billing chain, and
  how complaints and inspection failures enter the system as work orders.
  Use when the user asks about work orders — creating, assigning,
  status flow, billing a tag job, complaints, or what setup a work order
  depends on. In Ranyan, "job site" and "project" are the same entity.
---

# Ranyan Work Orders — the operation engine

Work orders are how work actually gets done and tracked: anything requested
at a job site is a WO. There is **no priority field** — sites have dedicated
employees and not every job carries a hard deadline; the dates
(`beginDate`/`dueDate`) are the only urgency signal.

**Prerequisite:** the Ranyan MCP server must be connected (endpoint and
credentials come from your Ranyan admin). Tool names below are bare MCP
names; most hosts prefix them (e.g. `mcp__ranyan__list_work_types`).
Writes follow the confirmation rule: gather fields, never invent values,
echo the exact values back for approval, then call. After an ambiguous
failure, check with a read tool before retrying — duplicate work orders are
worse than a failed one.

## Roles — two assignment slots, different people

- **worker** = a Ranyan APPLICATION USER (office/management side). A work
  order may not need job-site work at all (an admin task, a client tour)
  and can be assigned to a worker alone.
- **employee** = the person who PERFORMS the work at the job site. Site
  work gets an `employeeId` (or `assign_employee_to_work_order`).

Never conflate the two — `list_work_orders(workerId=…)` and `employeeId`
filter different populations, and reports should say which one owns a WO.

## Setup chain (everything is user-defined — there are no system defaults)

1. **Project** — every WO binds to one; it must exist first.
2. **Service types** — the catalog of the actual work performed (Vacuum,
   Mop, Rest Rooms…). `create_service_type(name, code?)`: the name is
   unique tenant-wide. `code` is meant to be a 2-letter code for the TYPE
   of work (e.g. JL = Janitorial) — but bulk imports have been known to
   stamp creator initials into codes, so **treat codes as unreliable and
   always resolve services by name**. Omit the code on create and let it
   auto-generate if unsure.
3. **Work types** — kinds of work, created by the users themselves
   (`create_work_type(name, isActive, isPaidService, serviceTypeIds)`);
   name unique tenant-wide. Naming conventions carry operational meaning —
   e.g. a type whose name contains "Complaint" is how complaints are
   identified (see below), and types ending in a line of business
   ("Request - Engineering", "Complaint - <division>") are common shapes.
4. **Link services to work types** — at creation via `serviceTypeIds`, or
   later via `add_service_to_work_type` (duplicates are silently skipped).
   The relationship is many-to-many; `list_work_type_services` /
   `get_work_type` return the links.

Before creating a work order, walk this chain with READ tools first:
`list_projects` → `list_work_types` → `list_service_types`. If a needed
work type or service is missing, that is a setup task for the user —
creating catalog entries needs its own confirmation.

## Complaints are just a work type

Nothing is "filed" as a complaint — a complaint is any work order whose
**work type is the tenant's complaint type** (name-based configuration).
Complaints are raised by the client or a supervisor. `get_work_order_stats`
counts them and surfaces recurring service types.
**Failed inspections are NOT complaints** — they surface as actionable
items / reworks (see the inspection bridge).

## Record anatomy

Required on create (`create_work_order`): `request` (description of the
work), `projectId`, `wTypeId`, `dueDate` (epoch ms; `beginDate` defaults to
now). Optional: `buildingId`, `serviceIds`, `workerId`, `employeeId`,
`status`, `tz` (IANA — pass the user's timezone when known). The system
auto-assigns the `serialNumber`.

A full record (`get_work_order`) carries: status + statusLabel, archived
flag, begin/due dates (epoch ms) with the `tz` used, created/updated
timestamps, project, building, workType, services[], worker, employee,
images, comments.

`list_work_orders`: `q` searches serial number, request text, project name,
client, branch, work type; `from`/`to` filter the **BEGIN date** (epoch ms,
midnight-aligned); `status` accepts comma-separated values; order by
serial/begin/due/status/created/updated; paginated (default page ~20,
max 100).

## Status lifecycle (real workflow)

`open → inreview → completed → billed`, plus **`past_due` marked
automatically by the system** (due-date driven; cannot be set directly).

- The employee at the site reports the work done — the WO sits at
  **inreview**.
- **Management verifies the result and only then marks it completed.**
  This verification is a separate action from the Inspection module
  (the supervisor's routine on-site QA) — never conflate the two; see
  the `ranyan-inspections` skill.
- Change status with `change_work_order_status` (it triggers the correct
  notifications), never via `update_work_order`. Updates are for field
  edits only — and note `serviceIds` REPLACES the full set when provided;
  pass null to clear worker/building assignments.

## Tag Jobs & the billing chain

A work type with **`isPaidService: true`** makes its work orders
**Tag Jobs** — chargeable work outside the contract. Billing order:
`set_work_order_cost` first (a price is agreed before an invoice exists),
then `set_work_order_invoice`. Setting a cost on a routine contract WO is
rejected by design — it would inflate Tag Billing. In work-order stats,
`unbilled` + its `detail[]` is the ready-made worklist for this chain
(remember it is scoped to the queried month).

## Inspection bridge

Inspection setup (categories/areas/items/types) lives in the app UI — the
MCP server has no inspection CRUD. Failed items auto-generate remediation
work orders through the configured inspection/training TYPE's service
(e.g. one named "Needs Action"); the generated WO carries the failed
item's photos and notes, and **inherits the employee when one was
assigned to the failed item** (item assignment is optional — otherwise
the WO lands unassigned). If that work type/service was never
configured, remediation silently produces no work-order trail — which is
what `noRemediationReason: not-configured` means in inspection stats.
Details in the `ranyan-inspections` skill.

## Example flows

- "Anything open at <site> right now?" → resolve the project UUID →
  `list_work_orders(projectId, status="open")` → group by work type, flag
  overdue begin dates, name the owning employee/worker per WO.
- "Book the extra floor work as chargeable" → confirm project UUID, Tag-Job
  work type, serviceIds, dueDate, request text → echo → `create_work_order`
  → report the serial → later `set_work_order_cost` →
  `set_work_order_invoice`.
- "Who's handling the restroom complaint?" → `list_work_orders(q=…)`
  filtered to the complaint work type → check `employee` (site staff) vs
  `worker` (app user) on the record.

## Unverified details — do not assert, say "not documented"

- Whether `billed` is set automatically once an invoice reference exists
  or by manual status change.
- How stats tooling internally maps a custom-named work type to
  "complaint" (name match vs flag).
- The exact trigger window for `past_due` beyond "due-date driven".
