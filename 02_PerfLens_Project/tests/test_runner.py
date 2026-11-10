"""Public runner contracts: paired completeness, correctness and failures."""
import json
from pathlib import Path
import tempfile
import unittest
import subprocess

from perflens import analyze_rows, observe, run, validate_config


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.config = dict(name='fixture', rounds=5, arms=[
            dict(name='A', command=['{python}', '-c', 'pass']),
            dict(name='B', command=['{python}', '-c', 'pass'])])

    def rows(self):
        return [dict(arm=arm, round=i, seconds=seconds, checksum='42')
                for i in range(1, 6) for arm, seconds in [('A', 1), ('B', 1.2)]]

    def test_known_regression_and_absolute_target_are_separate(self):
        self.config['target_seconds'] = 0.5
        result = analyze_rows(self.config, self.rows())
        self.assertEqual(result['comparison']['decision'], 'regression')
        self.assertEqual(result['target']['met'], {'A': False, 'B': False})

    def test_no_regression_can_still_miss_target(self):
        rows = self.rows()
        for row in rows:
            row['seconds'] = 1
        self.config['target_seconds'] = .5
        result = analyze_rows(self.config, rows)
        self.assertEqual(result['comparison']['decision'], 'within_threshold')
        self.assertFalse(result['target']['met']['A'])

    def test_incomplete_duplicate_and_wrong_results_refuse_inference(self):
        rows = self.rows()
        for invalid in [rows[:-1], rows + rows[:1]]:
            with self.assertRaises(ValueError):
                analyze_rows(self.config, invalid)
        rows[0]['checksum'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'Checksums differ'):
            analyze_rows(self.config, rows)

    def test_invalid_config(self):
        self.config['rounds'] = 4
        with self.assertRaises(ValueError):
            validate_config(self.config)

    def test_different_timing_boundaries_are_rejected(self):
        self.config['arms'][1]['metric'] = 'process'
        with self.assertRaisesRegex(ValueError, 'same timing boundary'):
            validate_config(self.config)

    def test_external_protocol_and_bad_payload(self):
        arm = dict(command=['{python}', '-c',
            'import json; print(json.dumps(dict(seconds=.01,checksum=42,valid=True)))'])
        self.assertEqual(observe(arm, {}, 10)['payload']['checksum'], 42)
        arm['command'][-1] = 'print("{}")'
        with self.assertRaisesRegex(ValueError, 'valid=true'):
            observe(arm, {}, 10)

    def test_failure_status_is_saved_without_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.config['arms'][0]['command'] = ['{python}', '-c', 'raise RuntimeError("fixture")']
            self.config['arms'][1]['command'] = self.config['arms'][0]['command']
            path = root / 'config.json'
            path.write_text(json.dumps(self.config))
            output = root / 'failed'
            with self.assertRaisesRegex(RuntimeError, 'Benchmark failed'):
                run(path, output)
            self.assertEqual(json.loads((output / 'metadata.json').read_text())['status'], 'failed')
            self.assertFalse((output / 'summary.json').exists())
            failure = json.loads((output / 'failures.jsonl').read_text().splitlines()[0])
            self.assertEqual(failure['status'], 'failed')
            self.assertIn('RuntimeError', failure['stderr'])
            self.assertTrue(Path(failure['command'][0]).name.startswith('python'))

    def test_java_setup_failure_is_recorded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / 'config.json'
            path.write_text(json.dumps(self.config))
            output = root / 'failed'
            with self.assertRaises(OSError):
                run(path, output, dict(java=str(root/'missing-java')))
            self.assertEqual(json.loads((output/'metadata.json').read_text())['status'], 'failed')

    def test_timeout_kills_descendant_and_retains_partial_output(self):
        import psutil
        with tempfile.TemporaryDirectory() as temp:
            pidfile = Path(temp) / 'pid.txt'
            nested = f'import os,time; open({str(pidfile)!r},"w").write(str(os.getpid())); time.sleep(60)'
            code = ('import subprocess,sys,time; '
                    f'subprocess.Popen([sys.executable,"-c",{nested!r}]); '
                    'print("started",flush=True); time.sleep(60)')
            arm = dict(command=['{python}','-c',code])
            with self.assertRaises(subprocess.TimeoutExpired) as caught:
                observe(arm, {}, 2)
            self.assertIn('started',caught.exception.evidence['stdout'])
            # Windows may briefly enumerate an already terminated process object.
            # A zombie on POSIX is also terminated; reaping belongs to its parent/init.
            try:
                process=psutil.Process(int(pidfile.read_text()))
                if process.status()!=psutil.STATUS_ZOMBIE:
                    process.wait(timeout=5)
            except psutil.NoSuchProcess:
                pass

    def test_exited_parent_does_not_leave_inherited_output_pipe_hanging(self):
        import psutil
        with tempfile.TemporaryDirectory() as temp:
            pidfile=Path(temp)/'orphan.txt'
            nested=f'import os,time; open({str(pidfile)!r},"w").write(str(os.getpid())); time.sleep(60)'
            code=('import subprocess,sys; '
                  f'subprocess.Popen([sys.executable,"-c",{nested!r}]); '
                  'print("parent exits",flush=True)')
            with self.assertRaises(subprocess.TimeoutExpired):
                observe(dict(command=['{python}','-c',code]),{},2)
            try:
                process=psutil.Process(int(pidfile.read_text()))
                if process.status()!=psutil.STATUS_ZOMBIE:
                    process.wait(timeout=5)
            except psutil.NoSuchProcess:
                pass


if __name__ == '__main__':
    unittest.main()
