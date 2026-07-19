import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
WORKFLOW_PATH = ROOT / ".github/workflows/iac.yml"


class IacWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    def test_iac_scan_context_runs_for_every_pull_request_and_main_push(self):
        self.assertRegex(
            self.workflow,
            r"(?m)^on:\n  pull_request:\n  push:\n    branches: \[main\]$",
        )
        self.assertIn("  iac-scan:\n    name: iac-scan\n", self.workflow)

    def test_changed_iac_detection_is_fail_closed(self):
        for contract in (
            "fetch-depth: 0",
            "BASE_SHA:",
            "HEAD_SHA:",
            'git cat-file -e "$BASE_SHA^{commit}"',
            'git cat-file -e "$HEAD_SHA^{commit}"',
            'changed_files="$(git diff --name-only "$BASE_SHA" "$HEAD_SHA" --)"',
            r"(^|/)[^/]+\.tf(vars)?$|^infra/|^k8s/|^helm/",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, self.workflow)
        self.assertEqual(self.workflow.count('echo "iac=true" >> "$GITHUB_OUTPUT"'), 2)
        self.assertEqual(self.workflow.count('echo "iac=false" >> "$GITHUB_OUTPUT"'), 1)

    def test_scanners_remain_strict_and_run_only_for_iac_changes(self):
        self.assertEqual(
            self.workflow.count("if: steps.changes.outputs.iac == 'true'"),
            2,
        )
        self.assertIn("severity: MEDIUM,HIGH,CRITICAL", self.workflow)
        self.assertIn('exit-code: "1"', self.workflow)
        self.assertIn("soft_fail: false", self.workflow)
        self.assertNotIn("continue-on-error", self.workflow)

    def test_job_keeps_least_privilege_and_explains_non_iac_success(self):
        permissions = re.search(r"(?ms)^permissions:\n(.*?)\n\njobs:", self.workflow)
        self.assertIsNotNone(permissions)
        self.assertEqual(permissions.group(1), "  contents: read")
        self.assertIn("if: steps.changes.outputs.iac == 'false'", self.workflow)
        self.assertIn("No IaC changes detected", self.workflow)


if __name__ == "__main__":
    unittest.main()
