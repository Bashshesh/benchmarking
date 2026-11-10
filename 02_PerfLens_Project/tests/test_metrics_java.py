"""Correctness of the project-owned resource/latency protocol, not timing claims."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from perflens import ROOT
JAVA=os.environ.get('PERFLENS_JAVA') or shutil.which('java')

@unittest.skipUnless(JAVA,'Full JDK21 required')
class MetricsJavaTests(unittest.TestCase):
    def test_metrics_and_latency_trace_keep_independent_membership_result(self):
        with tempfile.TemporaryDirectory() as temp:
            javac=str(Path(JAVA).with_name('javac.exe' if os.name=='nt' else 'javac'))
            subprocess.run([javac,'-d',temp,str(ROOT/'workloads/SearchBench.java'),str(ROOT/'upgrade/workloads/MetricsBench.java')],capture_output=True,check=True)
            for variant in ['baseline','optimized']:
                result=subprocess.run([JAVA,'-cp',temp,'MetricsBench',variant,'3','1','latency'],text=True,capture_output=True,check=True)
                payload=json.loads(result.stdout)
                self.assertEqual(payload['checksum'],1000)
                self.assertTrue(payload['valid'])
                self.assertEqual(len(payload['latency_nanoseconds']),3)
                self.assertGreater(payload['latencies']['p99_seconds'],0)
                self.assertGreater(payload['throughput_ops_per_second'],0)
            invalid=subprocess.run([JAVA,'-cp',temp,'MetricsBench','unknown','3','1'],capture_output=True)
            self.assertNotEqual(invalid.returncode,0)
