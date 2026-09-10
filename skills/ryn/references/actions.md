# Doing things in Ranyan (MCP tools)

The Ranyan MCP server exposes tools that write to the real system. This file
is the judgment layer: when to use them, and what to confirm first.

> These are real records in a live business system. A wrong work order is not
> a wrong answer — someone acts on it.

## The confirmation rule

Never call a create/update tool until the user has seen the actual field
values you're about to send.

1. **Gather** the required fields. Ask for any that are missing — one message,
   all of them, not a round trip per field.
2. **Never invent a value.** Not a due date, not a priority, not a customer.
   "Reasonable default" is how a wrong work order gets filed. If the API has a
   real default, say the field is being left to the default.
3. **Echo it back** as a short list, then ask to proceed.
4. **Call the tool**, then report what was created with its ID and link.

Skip the echo only if the user pre-approved the exact values ("create a work
order titled X for customer Y, due Friday" — that's already the confirmation).

Read tools (list, search, get) need no confirmation. Call them freely,
including to resolve a name to an ID before a write.

## Tools

### `list_projects` - Get the list of Projects

**Optional** - q, branchId, clientId, archived, page, limit

### `get_project` - Get a single Project by ID

**Required** - id

### `create_project` - Create a Project

**Required:** name

**Before calling:** use the tool `list_projects` passing the name to the `q` parameter of the list to check if the project already exist.

### `create_work_order` - Create a Work Order

**Required:** beginDate, dueDate, projectId, wTypeId, request
**Optional:** tz

**Before calling:** resolve the project, work type and services name to an ID with the
lookup tool rather than passing a free-text name. Get the current timezone of the
user and put it to tz if not provided.

## When the tool fails

| Error      | Means                                                 | Do                                      |
| ---------- | ----------------------------------------------------- | --------------------------------------- |
| Auth / 401 | You need to be authenticated before calling the tools | Connect or Re-connect to the MCP Server |

Never retry a create after an ambiguous failure — check with a read tool
whether the first attempt actually landed. Duplicate work orders are worse
than a failed one.

## Falling back

If the MCP server isn't connected, don't stall — give the manual steps from
[how-to.md](how-to.md) and mention the tool would have done it in one step.

## Setup

Add a Custom MCP Connector using the following URL: `https://mcp.ranyan.com/mcp`.
Provide the OAuth Client and Secret to connect to the server.
