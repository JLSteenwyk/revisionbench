import unittest
from scripts.compare_precision import compare


class PrecisionTests(unittest.TestCase):
    def test_extra_primary_generation_does_not_contaminate_pair(self):
        def row(seed, outcome):
            return {"task": "one", "seed": seed, "condition": "peer_facts", "status": "finished",
                    "unauthorized_attempt": outcome, "unauthorized_change": outcome, "task_complete": True}
        report = compare([row(0, False), row(100, True)], [row(0, True)])
        result = report["comparisons"]["peer_facts_unauthorized_attempt"]
        self.assertEqual(result["risk_difference"], 1)
        self.assertEqual(result["complete_blocks"], 1)
        self.assertEqual(result["incomplete_blocks"], 0)
