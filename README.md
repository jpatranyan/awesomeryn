# awesomeryn

The Ranyan knowledge base, as an installable Claude Code skill. Ask `/ryn`
anything about getting started with Ranyan.

## Install

```
/plugin marketplace add jpatranyan/awesomeryn
/plugin install awesomeryn@awesomeryn
```

## Layout

```
.claude-plugin/
  marketplace.json     # what `/plugin marketplace add` reads
  plugin.json          # plugin identity + version
skills/ryn/
  SKILL.md             # routing rules + topic index; the slash command is /ryn
  FAQ.md               # short common questions
  references/          # the knowledge base — one file per topic, loaded on demand
  assets/              # onboarding checklist handed to new users
  scripts/validate.py  # pre-publish check
skills/ranyan-work-orders/
  SKILL.md             # the work-order operation engine — setup chain,
                       # worker vs employee, status flow, Tag Job billing
                       # via the Ranyan MCP server — needs the server connected
skills/ranyan/
  SKILL.md             # time logs & attestations via the Ranyan MCP server —
                       # hours, punch data, shift affirmations; needs the server connected
skills/ranyan-project-stats/
  SKILL.md             # job-site stats reports (budget + work orders +
                       # inspections), project health, inspection coverage
                       # via the Ranyan MCP server — needs the server connected
```

## Adding knowledge

Answers live in `skills/ryn/references/`, one file per topic, indexed by the
table in `SKILL.md`. To document something new: add a section to the matching
reference file. Add a _new_ file only for a genuinely new topic — and then add
its row to the index, or the skill will never read it.

`SKILL.md` tells Claude to answer only from these files and to say "not
documented" otherwise, so an unwritten doc produces an honest gap rather than
an invented answer.

## Before publishing

```
python3 skills/ryn/scripts/validate.py
```

## Release

Bump `version` in `.claude-plugin/plugin.json`, commit, push. Users pick it up
with `/plugin marketplace update awesomeryn`.
