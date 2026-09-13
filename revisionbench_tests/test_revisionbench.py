import json
import os
from pathlib import Path
import tempfile
import unittest

from revisionbench.fixtures import apply_correction, correction, prepare, source
from revisionbench.oracle import evaluate, expected, safe_text
from revisionbench.sandbox import run


class OracleTests(unittest.TestCase):
    def test_mean_median_missingness_and_counts(self):
        data = 'species,body_mass_g\nA,10\nA,20\nA,90\nA,NA\nB,30\n'
        self.assertEqual(expected(data, 'mean')['summary']['A'], {'n': 3, 'mass_g': 40.0})
        self.assertEqual(expected(data, 'median')['summary']['A'], {'n': 3, 'mass_g': 20.0})
        self.assertEqual(expected(data, 'mean')['counts'], {'A': 4, 'B': 1})
        self.assertEqual(expected(data, 'mean')['conclusions']['largest_species'], 'A')
        self.assertEqual(expected(data, 'median')['conclusions']['largest_species'], 'B')

    def test_corrected_data_and_requirement_are_distinct(self):
        data, stat = correction('exclude_2007')
        self.assertNotEqual(data, source())
        self.assertEqual(stat, 'mean')
        self.assertEqual(correction('median_requirement'), (source(), 'median'))
        self.assertEqual(correction('unchanged'), (source(), 'mean'))

    def test_symlinks_and_special_files_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'linked').symlink_to('/etc/passwd')
            with self.assertRaises(ValueError):
                safe_text(root, 'linked')
            os.mkfifo(root/'fifo')
            with self.assertRaises(ValueError):
                safe_text(root, 'fifo')

    def test_missing_outputs_are_failures(self):
        with tempfile.TemporaryDirectory() as temp:
            score = evaluate(Path(temp), source(), 'mean')
            self.assertFalse(score['complete'])
            self.assertFalse(any(score['checks'].values()))


@unittest.skipUnless(os.environ.get('REVISIONBENCH_DOCKER_TESTS') == '1', 'Opt-in Docker integration checks')
class DockerIntegrationTests(unittest.TestCase):
    def test_stale_figure_is_not_hidden_by_correct_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)/'task'
            prepare(workspace)
            result = run(workspace)
            self.assertEqual(result['exit_code'], 0, result)
            self.assertTrue(evaluate(workspace, source(), 'mean')['complete'])
            stale_figure = (workspace/'outputs/figure.svg').read_text()
            data, statistic = apply_correction(workspace, 'exclude_2007')
            self.assertEqual(run(workspace)['exit_code'], 0)
            self.assertTrue(evaluate(workspace, data, statistic)['complete'])
            (workspace/'outputs/figure.svg').write_text(stale_figure)
            score = evaluate(workspace, data, statistic)
            self.assertTrue(score['checks']['summary'])
            self.assertFalse(score['checks']['figure_data_and_title'])
            self.assertFalse(score['complete'])

    def test_wrong_claim_and_unaffected_count_damage_are_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)/'task'
            prepare(workspace)
            self.assertEqual(run(workspace)['exit_code'], 0)
            (workspace/'outputs/conclusions.json').write_text('{"statistic":"median"}')
            (workspace/'outputs/sample_counts.json').write_text('{}')
            score = evaluate(workspace, source(), 'mean')
            self.assertTrue(score['checks']['summary'])
            self.assertFalse(score['checks']['conclusions'])
            self.assertFalse(score['checks']['sample_counts'])

    def test_sandbox_has_no_host_mount_or_network(self):
        with tempfile.TemporaryDirectory() as temp:
            script = ('import os,pathlib,socket; '
                      'assert os.getuid()!=0; '
                      'assert not pathlib.Path("/home/bizon").exists(); '
                      'assert not pathlib.Path("/var/run/docker.sock").exists(); '
                      'assert not any("TOKEN" in k or "API_KEY" in k for k in os.environ); '
                      'assert [name for _,name in socket.if_nameindex()]==["lo"]; '
                      'print("isolation_checks_pass")')
            result = run(Path(temp), ('python', '-I', '-c', script))
            self.assertEqual(result['exit_code'], 0, result)
            self.assertIn('isolation_checks_pass', result['stdout'])

    def test_timeout_and_output_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run(Path(temp), ('python', '-I', '-c', 'import time; time.sleep(20)'), timeout=1)
            self.assertEqual(result['termination'], 'timeout')
            result = run(Path(temp), ('python', '-I', '-c', 'print("x"*100000)'), output_limit=1000)
            self.assertEqual(result['termination'], 'output_limit')
            self.assertLessEqual(len(result['stdout']), 1000)


if __name__ == '__main__':
    unittest.main()
