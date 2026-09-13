import json
import os
from pathlib import Path
import tempfile
import unittest

from revisionbench import regression
from revisionbench.branches import STRATEGIES, prepare_branches
from revisionbench.fixtures import source


class RegressionOracleTests(unittest.TestCase):
    def test_hand_calculated_linear_fit(self):
        data = 'species,flipper_length_mm,body_mass_g\nA,1,5\nA,2,7\nB,3,9\nB,NA,11\n'
        result = regression.expected(data, 'mm')
        self.assertEqual(result['fit'], {'n': 3, 'slope': 2.0, 'intercept': 3.0, 'r_squared': 1.0})
        self.assertEqual(result['predictions'], [(180., 363.), (200., 403.), (220., 443.)])
        self.assertEqual(result['counts'], {'A': 2, 'B': 2})

    def test_unit_change_transforms_slope_preserves_predictions_and_counts(self):
        baseline = regression.expected(source(), 'mm')
        data, unit = regression.correction('flipper_cm')
        corrected = regression.expected(data, unit)
        self.assertAlmostEqual(corrected['fit']['slope'], baseline['fit']['slope']*10)
        self.assertAlmostEqual(corrected['fit']['intercept'], baseline['fit']['intercept'])
        self.assertAlmostEqual(corrected['fit']['r_squared'], baseline['fit']['r_squared'])
        self.assertEqual(corrected['counts'], baseline['counts'])
        for (x, y), (cx, cy) in zip(baseline['predictions'], corrected['predictions']):
            self.assertEqual(cx, x/10)
            self.assertAlmostEqual(cy, y)


@unittest.skipUnless(os.environ.get('REVISIONBENCH_DOCKER_TESTS') == '1', 'Opt-in Docker integration checks')
class MatchedBranchTests(unittest.TestCase):
    def test_repair_rebuild_information_and_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'branches'
            plan = prepare_branches(root, ['summary', 'regression'])
            self.assertEqual(len(plan['jobs']), 18)
            for workflow in ('summary', 'regression'):
                jobs = [j for j in plan['jobs'] if j['workflow']==workflow]
                for case in {j['case'] for j in jobs}:
                    by = {j['strategy']: j for j in jobs if j['case']==case}
                    self.assertEqual(set(by), set(STRATEGIES))
                    self.assertEqual(len({j['corrected_input_sha256'] for j in by.values()}), 1)
                    roots = {s: root/j['workspace'] for s,j in by.items()}
                    for name in ('CORRECTION.txt', 'CONTRACT.json', 'prior/analyze.py'):
                        self.assertEqual(len({(p/name).read_bytes() for p in roots.values()}), 1)
                    self.assertFalse((roots['rebuild']/'analyze.py').exists())
                    self.assertFalse((roots['rebuild']/'outputs').exists())
                    self.assertTrue((roots['repair']/'analyze.py').exists())
                    self.assertTrue((roots['repair']/'outputs').is_dir())
                    self.assertTrue((roots['dependency_repair']/'DEPENDENCIES.json').exists())
                    self.assertFalse((roots['repair']/'DEPENDENCIES.json').exists())


if __name__ == '__main__':
    unittest.main()
