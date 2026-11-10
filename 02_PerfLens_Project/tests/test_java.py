import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from perflens import ROOT


JAVA=os.environ.get('PERFLENS_JAVA') or shutil.which('java')


@unittest.skipUnless(JAVA,'Set PERFLENS_JAVA to a JDK executable for Java correctness tests')
class JavaTests(unittest.TestCase):
    def test_search_variants_and_runtime_modes_match_known_membership_count(self):
        with tempfile.TemporaryDirectory() as temp:
            javac=str(Path(JAVA).with_name('javac.exe' if os.name=='nt' else 'javac'))
            subprocess.run([javac,'-d',temp,str(ROOT/'workloads/SearchBench.java')],check=True,capture_output=True)
            for variant in ['baseline','optimized']:
                for flags in [[],['-Xint']]:
                    run=subprocess.run([JAVA,*flags,'-cp',temp,'SearchBench',variant,'3','7','1','0'],
                                       check=True,capture_output=True,text=True)
                    value=json.loads(run.stdout)
                    # Seven queries are [0,5,4,3,2,1,0], with four even members.
                    self.assertEqual(value['checksum'],4)
                    self.assertIs(value['valid'],True)
            bad=subprocess.run([JAVA,'-cp',temp,'SearchBench','unknown','3','7','1','0'],capture_output=True)
            self.assertNotEqual(bad.returncode,0)


if __name__=='__main__':
    unittest.main()
