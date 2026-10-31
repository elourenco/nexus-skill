#!/usr/bin/env python3
"""Validate this repository's simple skill metadata and local Markdown links."""

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


def validate(root: Path) -> list[str]:
    errors = []
    entry = root / "skills/nexus/SKILL.md"
    if not entry.is_file():
        return ["skills/nexus/SKILL.md: missing entrypoint"]
    text = entry.read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if frontmatter is None:
        errors.append("SKILL.md: missing frontmatter")
    else:
        # Deliberately limited to the two plain scalar fields used by this package.
        fields = {}
        for line in frontmatter.group(1).splitlines():
            key, separator, value = line.partition(":")
            if not separator or key in fields or key not in {"name", "description"}:
                errors.append(f"SKILL.md: unsupported or duplicate metadata: {line}")
            fields[key] = value.strip()
        if fields.get("name") != entry.parent.name:
            errors.append("SKILL.md: name must match its directory")
        description = fields.get("description", "")
        if not 1 <= len(description) <= 1024:
            errors.append("SKILL.md: description must contain 1–1024 characters")

    for path in sorted(root.rglob("*.md")):
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        content = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", content):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            destination = (path.parent / unquote(parsed.path)).resolve()
            if not destination.is_relative_to(root) or not destination.exists():
                errors.append(f"{path.relative_to(root)}: invalid local link: {target}")
    return errors


if __name__ == "__main__":
    repository = Path(__file__).resolve().parents[1]
    failures = validate(repository)
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        sys.exit(1)
    print("OK: skill metadata and local Markdown link destinations")
