#!/usr/bin/env python3
"""Validate NEXUS skill metadata, local links and its skills-only plugin package."""

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


def validate_plugins(root: Path) -> list[str]:
    """Check this package's narrow contract, not the full upstream host schemas."""
    errors = []

    def read_object(relative):
        try:
            value = json.loads((root / relative).read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("expected a JSON object")
            return value
        except (OSError, ValueError) as exc:
            errors.append(f"{relative}: {exc}")
            return {}

    manifests = [read_object(f".{host}-plugin/plugin.json") for host in ("claude", "codex")]
    allowed = {"name", "version", "description", "skills", "author", "homepage",
               "repository", "license", "keywords", "interface"}
    for host, manifest in zip(("claude", "codex"), manifests):
        label = f".{host}-plugin/plugin.json"
        host_allowed = allowed | (
            {"icon", "displayName", "documentationUrl", "supportUrl"}
            if host == "claude" else set()
        )
        if set(manifest) - host_allowed:
            errors.append(f"{label}: unsupported fields for this skills-only package")
        if manifest.get("name") != "nexus":
            errors.append(f"{label}: name must be nexus")
        version = manifest.get("version")
        if not isinstance(version, str) or not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", version):
            errors.append(f"{label}: version must be a numeric major.minor.patch release")
        if not isinstance(manifest.get("description"), str) or not manifest["description"].strip():
            errors.append(f"{label}: description is required")
        if manifest.get("skills") != "./skills/":
            errors.append(f"{label}: skills must use the shared ./skills/ directory")
    if manifests[0].get("version") != manifests[1].get("version"):
        errors.append("plugin versions differ between hosts")
    skills = root / "skills"
    if not skills.is_dir() or not skills.resolve().is_relative_to(root.resolve()):
        errors.append("skills directory must exist inside the plugin root")

    for host, relative in (("claude", ".claude-plugin/marketplace.json"),
                           ("codex", ".agents/plugins/marketplace.json")):
        catalog = read_object(relative)
        if catalog.get("name") != "nexus-local":
            errors.append(f"{relative}: marketplace name must be nexus-local")
        expected = {"name": "nexus", "source": "./"}
        if host == "claude":
            owner = catalog.get("owner")
            if not isinstance(owner, dict) or not isinstance(owner.get("name"), str) or not owner["name"].strip():
                errors.append(f"{relative}: owner.name is required")
        else:
            expected.update(source={"source": "local", "path": "./"},
                            policy={"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                            category="Developer Tools")
        if catalog.get("plugins") != [expected]:
            errors.append(f"{relative}: expected one local nexus entry at ./ with no component overrides")

    # Hosts also auto-discover components that are not declared in a manifest.
    for relative in ("hooks", "agents", "commands", ".mcp.json", "mcp.json", ".app.json", ".lsp.json", "plugin.json"):
        path = root / relative
        if path.is_file() or (path.is_dir() and any(p.is_file() for p in path.rglob("*"))):
            errors.append(f"{relative}: outside the skills-only plugin scope")
    return errors


def validate_skills(root: Path) -> list[str]:
    """Validate standalone skills and references without requiring plugin manifests."""
    root = root.resolve()
    errors = []
    skills = root / "skills"
    if not (skills / "nexus/SKILL.md").is_file():
        return ["skills/nexus/SKILL.md: missing entrypoint"]
    for directory in sorted(skills.iterdir()):
        if not directory.is_dir() or directory.name.startswith("."):
            continue
        entry = directory / "SKILL.md"
        label = entry.relative_to(root)
        if not entry.is_file():
            errors.append(f"{label}: missing entrypoint")
            continue
        text = entry.read_text(encoding="utf-8")
        frontmatter = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
        if frontmatter is None:
            errors.append(f"{label}: missing frontmatter")
            continue
        # Deliberately limited to the two plain scalar fields used by this package.
        fields = {}
        for line in frontmatter.group(1).splitlines():
            key, separator, value = line.partition(":")
            if not separator or key in fields or key not in {"name", "description"}:
                errors.append(f"{label}: unsupported or duplicate metadata: {line}")
            fields[key] = value.strip()
        name = fields.get("name", "")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
            errors.append(f"{label}: invalid skill name")
        if name != directory.name:
            errors.append(f"{label}: name must match its directory")
        description = fields.get("description", "")
        if not 1 <= len(description) <= 1024:
            errors.append(f"{label}: description must contain 1–1024 characters")

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


def validate(root: Path) -> list[str]:
    root = root.resolve()
    return validate_plugins(root) + validate_skills(root)


if __name__ == "__main__":
    repository = Path(__file__).resolve().parents[1]
    failures = validate(repository)
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        sys.exit(1)
    print("OK: skill metadata, local Markdown links and skills-only plugin package")
