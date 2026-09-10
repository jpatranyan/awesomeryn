#!/usr/bin/env python3
"""Validate the plugin manifests and every SKILL.md before publishing.

Run from the repo root:  python3 skills/awesomeryn/scripts/validate.py
Self-check:              python3 skills/awesomeryn/scripts/validate.py --test
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]


def parse_frontmatter(text):
    """Minimal YAML frontmatter reader: top-level `key: value` and `key: >` blocks.

    ponytail: hand-rolled instead of pulling in PyYAML — skill frontmatter is
    two flat keys. Swap to yaml.safe_load if it ever grows nesting.
    """
    if not text.startswith("---\n"):
        raise ValueError("missing --- frontmatter block")
    body = text[4:].split("\n---", 1)
    if len(body) < 2:
        raise ValueError("unterminated frontmatter block")
    out, key = {}, None
    for line in body[0].splitlines():
        if line[:1] not in (" ", "\t") and ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            out[key] = val.strip().lstrip(">|").strip()
        elif key and line.strip():
            out[key] = (out[key] + " " + line.strip()).strip()
    return out


def check(root):
    errors = []
    for rel in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
        path = root / rel
        if not path.exists():
            errors.append(f"{rel}: missing")
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{rel}: invalid JSON ({e})")
            continue
        if not data.get("name"):
            errors.append(f"{rel}: missing 'name'")
        if not data.get("description"):
            errors.append(f"{rel}: missing 'description'")

    skills = sorted((root / "skills").glob("*/SKILL.md"))
    if not skills:
        errors.append("skills/: no SKILL.md found")
    for path in skills:
        rel = path.relative_to(root)
        try:
            fm = parse_frontmatter(path.read_text())
        except ValueError as e:
            errors.append(f"{rel}: {e}")
            continue
        if fm.get("name") != path.parent.name:
            errors.append(f"{rel}: name '{fm.get('name')}' != directory '{path.parent.name}'")
        desc = fm.get("description", "")
        if not desc:
            errors.append(f"{rel}: missing 'description' (Claude cannot discover the skill)")
        elif len(desc) > 1024:
            errors.append(f"{rel}: description is {len(desc)} chars (max 1024)")
        if "TODO" in desc:
            errors.append(f"{rel}: description still contains TODO")
    return errors


def _test():
    good = "---\nname: x\ndescription: >\n  a\n  b\n---\nbody"
    assert parse_frontmatter(good) == {"name": "x", "description": "a b"}, parse_frontmatter(good)
    assert parse_frontmatter("---\nname: x\n---\n")["name"] == "x"
    for bad in ("no frontmatter", "---\nname: x\n"):
        try:
            parse_frontmatter(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected failure on {bad!r}")
    print("self-check ok")


if __name__ == "__main__":
    if "--test" in sys.argv:
        _test()
        sys.exit(0)
    problems = check(ROOT)
    for p in problems:
        print(f"✗ {p}")
    print(f"\n{len(problems)} problem(s)" if problems else "✓ all checks passed")
    sys.exit(1 if problems else 0)
