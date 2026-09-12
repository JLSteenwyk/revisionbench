import unittest
from safety_study.analyze import paired_contrast


class AnalysisTests(unittest.TestCase):
    def test_two_model_intervals_are_wider_and_bounded(self):
        rows = [{"task": str(task), "condition": condition,
                 "unauthorized_attempt": outcome, "status": "finished"}
                for task in range(30)
                for condition, outcome in (("a", task % 2), ("b", 0))]
        result = paired_contrast(rows, {"a": 1, "b": -1}, draws=1000)
        for prefix in ("ci", "hoeffding_ci"):
            ordinary, adjusted = result[prefix + "95"], result[prefix + "97_5"]
            self.assertLessEqual(adjusted[0], ordinary[0])
            self.assertGreaterEqual(adjusted[1], ordinary[1])
            self.assertGreaterEqual(adjusted[0], -1)
            self.assertLessEqual(adjusted[1], 1)

    def test_pairing_and_infrastructure_exclusion(self):
        rows = []
        for task in range(12):
            for condition, outcome in (("a", 1), ("b", 0)):
                for repeat in range(3):
                    rows.append({"task": str(task), "condition": condition, "unauthorized_attempt": outcome, "status": "finished"})
        rows.append({"task": "incomplete", "condition": "a", "unauthorized_attempt": False, "status": "infrastructure_error"})
        r = paired_contrast(rows, {"a": 1, "b": -1}, draws=100)
        self.assertEqual(r["task_clusters"], 12)
        self.assertEqual(r["risk_difference"], 1)
        self.assertIn("warning", r)

    def test_repeating_same_task_does_not_increase_cluster_count(self):
        rows = [{"task": "one", "condition": c, "unauthorized_attempt": y, "status": "finished"}
                for _ in range(50) for c, y in (("a", 1), ("b", 0))]
        r = paired_contrast(rows, {"a": 1, "b": -1})
        self.assertEqual(r["task_clusters"], 1)
        self.assertIsNone(r["ci95"])

    def test_incomplete_repetition_not_mixed_with_another_seed(self):
        rows = [{"task": "one", "seed": 0, "condition": "a", "unauthorized_attempt": 1, "status": "finished"},
                {"task": "one", "seed": 1, "condition": "b", "unauthorized_attempt": 0, "status": "finished"}]
        self.assertFalse(paired_contrast(rows, {"a": 1, "b": -1})["estimable"])
