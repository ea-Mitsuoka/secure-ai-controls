import json
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]
MANIFEST_FILE = REPOSITORY_ROOT / ".github" / "inheritance" / "manifest.json"
IGNORE_FILE = REPOSITORY_ROOT / ".templatesyncignore"


class SecureInheritanceContractTest(unittest.TestCase):
    def test_foundation_docs_are_inherited_without_owning_all_project_docs(self):
        manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))

        self.assertIn("docs/foundation/", manifest["inherited_paths"])
        self.assertNotIn("docs/", manifest["protected_paths"])

    def test_local_claude_security_controls_are_protected(self):
        manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        inherited = set(manifest["inherited_paths"])
        protected = set(manifest["protected_paths"])

        self.assertNotIn(".claude/", inherited)
        self.assertLessEqual(
            {
                ".claude/agents/",
                ".claude/hooks/post-edit-quality.sh",
                ".claude/skills/",
            },
            inherited,
        )
        self.assertLessEqual(
            {
                ".claude/hooks/guard-bash.sh",
                ".claude/hooks/tests/",
                ".claude/settings.json",
                ".devcontainer/",
            },
            protected,
        )
        self.assertNotIn(".devcontainer/", inherited)

    def test_legacy_sync_protects_child_owned_contract(self):
        entries = {
            line.strip()
            for line in IGNORE_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        required_exclusions = {
            ".gitignore",
            ".claude/hooks/guard-bash.sh",
            ".claude/hooks/tests/**",
            ".claude/settings.json",
            ".devcontainer/**",
            ".github/inheritance/lock.json",
            ".github/inheritance/manifest.json",
            ".github/workflows/template-sync.yml",
            "secure-ai-controls.md",
            "tests/governance/test_secure_inheritance_contract.py",
            "tests/governance/test_terraform_profile.py",
        }
        inherited_transport_paths = {"Makefile", "profiles/**", "tests/**"}

        self.assertLessEqual(required_exclusions, entries)
        self.assertTrue(inherited_transport_paths.isdisjoint(entries))


if __name__ == "__main__":
    unittest.main()
