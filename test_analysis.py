"""Small correctness checks; run before, never during, timing experiments."""
import csv
import json
from pathlib import Path
import tempfile
import unittest
from analyze import compare, analyze_experiment


class AnalysisTests(unittest.TestCase):
    def test_known_effect_and_shared_drift(self):
        old = list(range(1, 21))
        result = compare(old, [x * 1.2 for x in old])
        self.assertAlmostEqual(result['change_percent'], 20)
        self.assertAlmostEqual(result['ci95_percent'][0], 20)
        self.assertEqual(result['decision'], 'regression')
        self.assertEqual(compare(old, [x * 0.8 for x in old])['decision'], 'improvement')

    def test_statistical_and_practical_are_different(self):
        result = compare([1] * 20, [1.01] * 20)
        self.assertEqual(result['statistical_direction'], 'slower')
        self.assertEqual(result['decision'], 'within_threshold')
        self.assertEqual(compare([1] * 20, [1] * 20)['statistical_direction'], 'uncertain')

    def test_uncertainty_and_reproducibility(self):
        result = compare([1] * 20, [0.8, 1.3] * 10)
        self.assertEqual(result['decision'], 'inconclusive')
        self.assertEqual(result, compare([1] * 20, [0.8, 1.3] * 10))

    def test_invalid_timings(self):
        for new in [[1] * 4, [0] * 20, [float('nan')] * 20]:
            with self.assertRaises(ValueError):
                compare([1] * 20, new)

    def test_partial_and_failed_runs_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            metadata = dict(status='measured', commits=['old', 'new'], config={'repeats': 5})
            (folder / 'metadata.json').write_text(json.dumps(metadata))
            with (folder / 'raw.csv').open('w', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(['commit', 'repeat', 'seconds'])
                writer.writerow(['old', 1, 1.0])
            with self.assertRaisesRegex(ValueError, 'Missing observations'):
                analyze_experiment(folder)
            metadata['status'] = 'failed'
            (folder / 'metadata.json').write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError, 'incomplete or failed'):
                analyze_experiment(folder)


if __name__ == '__main__':
    unittest.main()
