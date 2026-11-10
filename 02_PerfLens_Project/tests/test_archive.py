import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from audit_original import verify_originals


class ArchiveTests(unittest.TestCase):
    def test_missing_and_modified_originals_do_not_pass_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'archive').mkdir()
            with zipfile.ZipFile(root/'archive/misc.zip','w') as archive:
                archive.writestr('misc/code.py','original')
            digest=hashlib.sha256((root/'archive/misc.zip').read_bytes()).hexdigest()
            (root/'archive/SHA256.json').write_text(json.dumps({'misc.zip':digest}))
            with self.assertRaisesRegex(ValueError,'missing'):
                verify_originals(root)
            file=root/'original/misc/code.py'
            file.parent.mkdir(parents=True)
            file.write_text('original')
            self.assertEqual(verify_originals(root),1)
            file.write_text('changed')
            with self.assertRaisesRegex(ValueError,'changed'):
                verify_originals(root)


if __name__=='__main__':
    unittest.main()
