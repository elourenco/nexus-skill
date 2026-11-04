#!/usr/bin/env python3
"""Validate NEXUS skill metadata, local links and its skills-only plugin package."""

import json
import re
import sys
import unicodedata
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlsplit


def markdown_prose(content: str) -> str:
    """Exclude frontmatter and code blocks from this package's Markdown checks.

    This is a bounded Markdown check, not a renderer. Preserve blank lines so a
    setext underline cannot accidentally attach to text across a code block.
    """
    content = re.sub(r"\A---\n.*?\n---(?:\n|$)", "\n", content, count=1, flags=re.DOTALL)
    lines = []
    fence = None
    for line in content.splitlines():
        if fence:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}\s*", line):
                fence = None
            lines.append("")
            continue
        opening = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", line)
        if opening and not (opening[1][0] == "`" and "`" in opening[2]):
            fence = (opening[1][0], len(opening[1]))
            lines.append("")
        elif line.startswith(("    ", "\t")):
            lines.append("")
        else:
            lines.append(line)
    return "\n".join(lines)


def markdown_anchors(content: str) -> set[str]:
    """Collect common GitHub heading slugs and explicit HTML IDs in prose."""
    # Inline code contributes text to headings, but cannot define an HTML ID.
    without_code = re.sub(r"(`+).*?\1", "", content)
    anchors = {
        unescape(match[1] or match[2] or match[3])
        for match in re.finditer(
            r"<[^>]+\sid\s*=\s*(?:\"([^\"]+)\"|'([^']+)'|([^\s>]+))[^>]*>",
            without_code, re.IGNORECASE,
        )
    }
    slugs = set()
    previous = ""
    for line in content.splitlines():
        atx = re.match(r" {0,3}#{1,6}(?:[ \t]+(.*?)|[ \t]*)$", line)
        heading = None
        if atx:
            heading = re.sub(r"[ \t]+#+[ \t]*$", "", atx[1] or "").strip()
        elif previous.strip() and re.fullmatch(r" {0,3}(?:=+|-+)[ \t]*", line):
            heading = previous.strip()
        if heading is not None:
            # Formatting markers/tags disappear; code and link labels remain.
            heading = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", heading)
            heading = "".join(
                part if index % 2 else re.sub(
                    r"(?<!\w)(_+)(?=\S)(.+?)(?<=\S)\1(?!\w)", r"\2", part
                )
                for index, part in enumerate(re.split(r"(`+.*?`+)", heading))
            )
            heading = unescape(re.sub(r"<[^>]*>", "", heading)).lower()
            slug = "".join(
                char for char in heading
                if char in "-_ " or not unicodedata.category(char).startswith(("P", "S", "C"))
            ).replace(" ", "-")
            candidate = slug
            suffix = 0
            while candidate in slugs:
                suffix += 1
                candidate = f"{slug}-{suffix}"
            slugs.add(candidate)
        previous = line
    return anchors | slugs


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
        expected = {"name": "nexus", "source": "./build/claude"}
        if host == "claude":
            owner = catalog.get("owner")
            if not isinstance(owner, dict) or not isinstance(owner.get("name"), str) or not owner["name"].strip():
                errors.append(f"{relative}: owner.name is required")
        else:
            expected.update(source={"source": "local", "path": "./"},
                            policy={"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                            category="Developer Tools")
        remote = {**expected, "source": {"source": "url",
                  "url": "https://github.com/elourenco/nexus-skill.git", "ref": "plugins"}}
        if host == "claude":
            remote["source"].update(source="git-subdir", path="build/claude")
        if catalog.get("plugins") not in ([expected], [remote]):
            errors.append(f"{relative}: expected one nexus entry at ./ or the published plugins ref with no component overrides")

    # Hosts also auto-discover components that are not declared in a manifest.
    for relative in ("hooks", "agents", "commands", ".mcp.json", "mcp.json", ".app.json", ".lsp.json", "plugin.json"):
        path = root / relative
        if path.is_file() or (path.is_dir() and any(p.is_file() for p in path.rglob("*"))):
            errors.append(f"{relative}: outside the skills-only plugin scope")
    return errors


def validate_skills(root: Path, core_entry: str = "nexus", reference_only: set[str] | frozenset[str] = frozenset()) -> list[str]:
    """Validate standalone skills and references without requiring plugin manifests."""
    root = root.resolve()
    errors = []
    skills = root / "skills"
    if not (skills / core_entry / "SKILL.md").is_file():
        return [f"skills/{core_entry}/SKILL.md: missing entrypoint"]
    for directory in sorted(skills.iterdir()):
        if not directory.is_dir() or directory.name.startswith(".") or directory.name in reference_only:
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

    documents = {}

    def read_document(path):
        if path not in documents:
            prose = markdown_prose(path.read_text(encoding="utf-8"))
            documents[path] = (prose, markdown_anchors(prose))
        return documents[path]

    for path in sorted(root.rglob("*.md")):
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        content, _ = read_document(path)
        content = re.sub(r"(`+).*?\1", "", content)
        for target in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", content):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                continue
            destination = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not destination.is_relative_to(root) or not destination.exists():
                errors.append(f"{path.relative_to(root)}: invalid local link: {target}")
            elif parsed.fragment and destination.suffix.lower() == ".md":
                if unquote(parsed.fragment) not in read_document(destination)[1]:
                    errors.append(f"{path.relative_to(root)}: invalid local anchor: {target}")
    return errors


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors = validate_plugins(root) + validate_skills(root)
    claude = root / 'build/claude'
    if claude.exists():
        errors += validate_skills(claude, core_entry='start', reference_only={'nexus'})
        entries = {p.parent.name for p in (claude / 'skills').glob('*/SKILL.md')}
        if entries != {'start', 'brainstorm', 'plan', 'build', 'debug', 'review'}:
            errors.append('build/claude: expected exactly six short Claude entrypoints')
    return errors


if __name__ == "__main__":
    repository = Path(__file__).resolve().parents[1]
    failures = validate(repository)
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        sys.exit(1)
    print("OK: skill metadata, local Markdown links and skills-only plugin package")
