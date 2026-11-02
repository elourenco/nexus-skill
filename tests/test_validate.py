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

    def test_core_remains_portable_alone(self):
        shutil.rmtree(self.root / "skills/nexus")
        shutil.copytree(REPO / "skills/nexus", self.root / "skills/nexus")
        self.assertEqual(validator.validate_skills(self.root), [])

    def test_complete_package_is_relocatable(self):
        shutil.rmtree(self.root / "skills")
        shutil.copytree(REPO / "skills", self.root / "skills")
        self.assertEqual(
            {path.parent.name for path in (self.root / "skills").glob("*/SKILL.md")},
            {"nexus", "nexus-brainstorming", "nexus-plan", "nexus-build", "nexus-debug", "nexus-review"},
        )
        self.assertEqual(validator.validate_skills(self.root), [])

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
