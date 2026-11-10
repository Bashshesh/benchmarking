"""Build/error/timeout public contracts; no benchmark observations in these fixtures."""
from pathlib import Path
import tempfile
import unittest
import json
from upgrade.adapter import build

class BuildAdapterTests(unittest.TestCase):
    def test_success_build_and_failed_build_receipts(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            values=build([['{python}','-c','print("built fixture")']],root/'success',{})
            self.assertEqual(values[0]['returncode'],0)
            self.assertIn('built fixture',values[0]['stdout'])
            with self.assertRaises(RuntimeError):
                build([['{python}','-c','raise SystemExit(7)']],root/'failure',{})
            receipt=json.loads((root/'failure/0.json').read_text())
            self.assertEqual(receipt['returncode'],7)
            self.assertEqual(receipt['status'],'failed')

    def test_build_timeout_is_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'timeout'
            with self.assertRaises(RuntimeError):
                build([['{python}','-c','import time; print("started",flush=True); time.sleep(30)']],target,{},timeout=.5)
            receipt=json.loads((target/'0.json').read_text())
            self.assertEqual(receipt['status'],'failed')
            self.assertIn('TimeoutExpired',receipt['error'])
