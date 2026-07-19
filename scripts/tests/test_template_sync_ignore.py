import json
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]
IGNORE_FILE = REPOSITORY_ROOT / ".templatesyncignore"
MANIFEST_FILE = REPOSITORY_ROOT / ".github/inheritance/manifest.json"


class TemplateSyncIgnoreTest(unittest.TestCase):
    def test_foundation_docs_use_git_pathspec_exclusions(self):
        entries = {
            line.strip()
            for line in IGNORE_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        self.assertIn("docs/**", entries)
        self.assertIn(":!docs/foundation/", entries)
        self.assertIn(":!docs/foundation/**", entries)
        self.assertNotIn("!docs/foundation/", entries)
        self.assertNotIn("!docs/foundation/**", entries)

    def test_foundation_docs_are_inherited_without_owning_all_project_docs(self):
        manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))

        self.assertIn("docs/foundation/", manifest["inherited_paths"])
        self.assertNotIn("docs/", manifest["protected_paths"])

    def test_legacy_sync_protects_child_owned_contract(self):
        entries = {
            line.strip()
            for line in IGNORE_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        required_exclusions = {
            ".gitignore",
            ".github/inheritance/lock.json",
            ".github/inheritance/manifest.json",
            ".github/workflows/template-sync.yml",
            "secure-ai-controls.md",
        }
        inherited_transport_paths = {"Makefile", "profiles/**", "tests/**"}

        self.assertLessEqual(required_exclusions, entries)
        self.assertTrue(inherited_transport_paths.isdisjoint(entries))


if __name__ == "__main__":
    unittest.main()
