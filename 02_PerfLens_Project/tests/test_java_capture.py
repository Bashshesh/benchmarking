"""A command receipt must retain UTF-8 JMH output on non-UTF-8 Windows hosts."""
import json,sys,tempfile,unittest
from pathlib import Path
from upgrade.java.reproduce import command
class CaptureTests(unittest.TestCase):
    def test_utf8_stdout_and_stderr_are_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            log=Path(tmp)/'receipt.json'
            expected='JMH \u2264 1 ns/op'
            code='import sys; sys.stdout.buffer.write('+repr(expected.encode('utf-8'))+'); sys.stderr.buffer.write(b"ok")'
            self.assertEqual(command([sys.executable,'-c',code],log),expected)
            self.assertEqual(json.loads(log.read_text())['stderr'],'ok')
