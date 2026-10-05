# oss-pocket health tests
# Author: Mourad.Soltani

import json
import unittest

from oss_pocket.cli import health_payload, main


class HealthTests(unittest.TestCase):
    def test_health_payload_shape(self):
        payload = health_payload()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "oss-pocket")
        self.assertEqual(payload["signature"], "Mourad.Soltani")
        self.assertTrue(payload["version"])

    def test_health_command_exits_zero(self):
        self.assertEqual(main(["health"]), 0)

    def test_health_json_roundtrip(self):
        encoded = json.dumps(health_payload())
        decoded = json.loads(encoded)
        self.assertEqual(decoded["signature"], "Mourad.Soltani")


if __name__ == "__main__":
    unittest.main()
