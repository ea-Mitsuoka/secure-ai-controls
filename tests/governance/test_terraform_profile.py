import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


class TerraformGovernanceProfileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/github_governance.py"),
                "validate",
                "--root",
                str(ROOT),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        cls.report = json.loads(result.stdout)
        cls.repository = json.loads(
            (ROOT / ".github/governance/repository.json").read_text(encoding="utf-8")
        )
        cls.manifest = json.loads(
            (ROOT / ".github/inheritance/manifest.json").read_text(encoding="utf-8")
        )

    def test_profile_adds_only_the_always_reported_iac_check(self):
        self.assertEqual(
            self.report["profiles"],
            [
                {
                    "schema_version": 1,
                    "id": "terraform-gcp",
                    "parent": "ai-dev-foundation",
                    "required_checks": ["iac-scan"],
                }
            ],
        )
        self.assertEqual(
            self.report["settings"]["required_checks"],
            [
                "lint",
                "test",
                "build",
                "doctor",
                "link-check",
                "pr-quality",
                "secret-scan",
                "dependency-scan",
                "license-check",
                "iac-scan",
            ],
        )
        self.assertNotIn("scan", self.report["settings"]["required_checks"])

    def test_repository_policy_does_not_duplicate_family_checks(self):
        self.assertNotIn("required_checks", self.repository["overrides"])

    def test_profile_directory_is_inherited_from_the_template_family(self):
        profile_directory = ".github/governance/profiles/"
        self.assertIn(profile_directory, self.manifest["inherited_paths"])
        self.assertNotIn(profile_directory, self.manifest["protected_paths"])


if __name__ == "__main__":
    unittest.main()
