import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
DEV_MAIN = ROOT / "infra/envs/dev/main.tf"


class NetworkModulePinTest(unittest.TestCase):
    def test_scaffold_pins_flow_log_enabled_network_release(self):
        source = DEV_MAIN.read_text(encoding="utf-8")

        self.assertIn(
            "terraform-gcp-modules.git//modules/network?ref=v0.5.0",
            source,
        )
        self.assertNotIn("modules/network?ref=v0.1.0", source)


if __name__ == "__main__":
    unittest.main()
