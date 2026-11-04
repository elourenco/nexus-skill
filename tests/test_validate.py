"""Exercise portable skill discovery and dependency validation in copied packages."""

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_validate", REPO / "scripts/validate.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class SkillValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.write_skill("nexus")

    def write_skill(self, directory, name=None, description="Use when requested.", body=""):
        path = self.root / "skills" / directory / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"---\nname: {name if name is not None else directory}\n"
            f"description: {description}\n---\n{body}", encoding="utf-8"
        )
        return path

    def test_accepts_multiple_skills_with_shared_reference(self):
        self.write_skill("nexus-plan", body="[Core](../nexus/SKILL.md)")
        self.assertEqual(validator.validate_skills(self.root), [])

    def test_validates_metadata_of_specialized_entry(self):
        self.write_skill("nexus-plan", name="nexus", description="")
        errors = validator.validate_skills(self.root)
        self.assertTrue(any("skills/nexus-plan/SKILL.md" in e and "name" in e for e in errors), errors)
        self.assertTrue(any("skills/nexus-plan/SKILL.md" in e and "description" in e for e in errors), errors)

    def test_rejects_missing_specialized_frontmatter(self):
        path = self.write_skill("nexus-review")
        path.write_text("# Incomplete skill\n", encoding="utf-8")
        self.assertTrue(any("nexus-review" in e and "frontmatter" in e for e in validator.validate_skills(self.root)))

    def test_rejects_skill_directory_without_entrypoint(self):
        (self.root / "skills/nexus-build").mkdir()
        self.assertTrue(any("nexus-build" in e and "missing entrypoint" in e for e in validator.validate_skills(self.root)))

    def test_rejects_invalid_names_even_when_matching_directory(self):
        for name in ("Invalid-Skill", "-nexus", "nexus--plan", "n" * 65):
            with self.subTest(name=name):
                self.write_skill(name)
                self.assertTrue(any(name in e and "invalid skill name" in e for e in validator.validate_skills(self.root)))
                shutil.rmtree(self.root / "skills" / name)

    def test_rejects_duplicate_metadata_in_specialized_entry(self):
        path = self.write_skill("nexus-debug")
        path.write_text(path.read_text().replace("description:", "name: nexus-debug\ndescription:"), encoding="utf-8")
        self.assertTrue(any("nexus-debug" in e and "duplicate" in e for e in validator.validate_skills(self.root)))

    def test_reports_missing_shared_dependency(self):
        self.write_skill("nexus-plan", body="[Procedure](../nexus/references/plan.md)")
        errors = validator.validate_skills(self.root)
        self.assertTrue(any("nexus-plan" in e and "invalid local link" in e for e in errors), errors)

    def test_rejects_link_outside_package(self):
        self.write_skill("nexus-plan", body="[Outside](../../../outside.md)")
        self.assertTrue(any("invalid local link" in e for e in validator.validate_skills(self.root)))

    def test_rejects_missing_fragment_in_same_or_other_document(self):
        self.write_skill("nexus", body="# Existing\n[Local](#missing)\n[Other](guide.md#missing)")
        (self.root / "skills/nexus/guide.md").write_text("# Existing\n", encoding="utf-8")
        errors = validator.validate_skills(self.root)
        self.assertEqual(len(errors), 2, errors)
        self.assertTrue(all("invalid local anchor" in error for error in errors), errors)

    def test_accepts_unicode_encoded_paths_and_formatted_heading_fragments(self):
        self.write_skill("nexus", body="[Guide](guia%20a%C3%A7%C3%A3o.md#a%C3%A7%C3%A3o-api--retry)\n")
        (self.root / "skills/nexus/guia ação.md").write_text(
            "## Ação: **API** & `retry`!\n", encoding="utf-8"
        )
        self.assertEqual(validator.validate_skills(self.root), [])

    def test_duplicate_heading_suffixes_do_not_claim_nonexistent_anchors(self):
        self.write_skill("nexus", body=(
            "# Retry\n# Retry\n# Retry\n"
            "[First](#retry) [Second](#retry-1) [Third](#retry-2) [Missing](#retry-3)\n"
        ))
        errors = validator.validate_skills(self.root)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("#retry-3", errors[0])

    def test_accepts_explicit_html_ids_and_setext_headings(self):
        self.write_skill("nexus", body=(
            '<a id="custom-ID"></a>\n<span id=plain-anchor></span>\n'
            "Recovery &amp; retries\n---\n"
            "[Custom](#custom-ID) [Plain](#plain-anchor) [Setext](#recovery--retries)\n"
        ))
        self.assertEqual(validator.validate_skills(self.root), [])

    def test_heading_slug_preserves_literal_underscores_but_removes_emphasis(self):
        self.write_skill("nexus", body=(
            "# _Retry_ with __care__ and snake_case\n"
            "[Heading](#retry-with-care-and-snake_case)\n"
        ))
        self.assertEqual(validator.validate_skills(self.root), [])

    def test_html_data_attributes_do_not_define_ids(self):
        self.write_skill("nexus", body='<span data-id="absent"></span>\n[Missing](#absent)\n')
        errors = validator.validate_skills(self.root)
        self.assertEqual(len(errors), 1, errors)

    def test_heading_suffixes_avoid_collisions_with_existing_heading_slugs(self):
        self.write_skill("nexus", body=(
            "# Retry\n# Retry-1\n# Retry\n"
            "[Collision](#retry-2) [Missing](#retry-3)\n"
        ))
        errors = validator.validate_skills(self.root)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("#retry-3", errors[0])

    def test_ignores_example_links_inside_code(self):
        self.write_skill("nexus", body=(
            "```markdown\n[Absent](absent.md#missing)\n```\n"
            "~~~markdown\n[Absent](absent.md)\n~~~\n"
            "    [Absent](absent.md)\n`[Absent](absent.md)`\n"
        ))
        self.assertEqual(validator.validate_skills(self.root), [])

    def test_code_headings_and_ids_cannot_satisfy_links(self):
        self.write_skill("nexus", body=(
            '````markdown\n# Fenced\n```\n<a id="hidden"></a>\n````\n'
            "    # Indented\n[Heading](#fenced) [ID](#hidden) [Indented](#indented)\n"
        ))
        errors = validator.validate_skills(self.root)
        self.assertEqual(len(errors), 3, errors)

    def test_preserves_external_and_file_links_without_fragments(self):
        self.write_skill("nexus", body=(
            "[External](https://example.org/#absent) [Mail](mailto:test@example.org)\n"
            "[Root](#) [File](SKILL.md)\n"
        ))
        self.assertEqual(validator.validate_skills(self.root), [])

    def test_core_remains_portable_alone(self):
        shutil.rmtree(self.root / "skills/nexus")
        shutil.copytree(REPO / "skills/nexus", self.root / "skills/nexus")
        self.assertEqual(validator.validate_skills(self.root), [])

    def test_complete_package_is_relocatable(self):
        shutil.rmtree(self.root / "skills")
        shutil.copytree(REPO / "skills", self.root / "skills")
        self.assertEqual(
            {path.parent.name for path in (self.root / "skills").glob("*/SKILL.md")},
            {"nexus", "nexus-brainstorm", "nexus-plan", "nexus-build", "nexus-debug", "nexus-review"},
        )
        self.assertEqual(validator.validate_skills(self.root), [])

    def test_relocated_package_detects_removed_policy_anchor(self):
        shutil.rmtree(self.root / "skills")
        shutil.copytree(REPO / "skills", self.root / "skills")
        probe = self.root / "skills/nexus/references/navigation-probe.md"
        probe.write_text(
            "[Authority](policies.md#policy-authority)\n"
            "[Engineering](policies.md#princípios-de-engenharia)\n", encoding="utf-8"
        )
        self.assertEqual(validator.validate_skills(self.root), [])

        policies = probe.parent / "policies.md"
        policies.write_text(
            policies.read_text(encoding="utf-8").replace('<a id="policy-authority"></a>', ""),
            encoding="utf-8",
        )
        errors = validator.validate_skills(self.root)
        self.assertIn(
            "skills/nexus/references/navigation-probe.md: invalid local anchor: "
            "policies.md#policy-authority", errors
        )
        self.assertFalse(any("princípios-de-engenharia" in error for error in errors), errors)

    def test_specialized_entry_without_core_is_incomplete(self):
        shutil.rmtree(self.root / "skills/nexus")
        shutil.copytree(REPO / "skills/nexus-review", self.root / "skills/nexus-review")
        self.assertEqual(validator.validate_skills(self.root), ["skills/nexus/SKILL.md: missing entrypoint"])

    def test_symlinked_package_root_is_valid(self):
        link = self.root / "package-alias"
        link.symlink_to(self.root, target_is_directory=True)
        self.assertEqual(validator.validate_skills(link), [])


if __name__ == "__main__":
    unittest.main()
