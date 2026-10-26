"""Distribution notices, localized entry points and executable README examples."""
import importlib.util
from pathlib import Path
import re
import unittest

spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

class ReleasePolicy(base.Evolution):
    def test_readme_examples_execute_with_canonical_syntax(self):
        for name in ['README.md','README.en.md','README.pt-BR.md','README.es.md']:
            text=(base.ROOT/name).read_text(encoding='utf-8')
            examples=re.findall(r'```assis\n([\s\S]*?)```',text)
            self.assertTrue(examples,name)
            for example in examples:self.accepted(example,'2\n4\n6\n')
            for link in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)',text):
                if '://' not in link:self.assertTrue((base.ROOT/link).is_file(),(name,link))

    def test_license_and_notices_are_in_the_native_install_manifest(self):
        self.assertEqual((base.ROOT/'LICENSE').read_bytes(),(base.ROOT/'docs/LICENSE').read_bytes())
        manifest=(base.ROOT/'src/install_files.inc').read_text(encoding='utf-8')
        required=['LICENSE','THIRD_PARTY_NOTICES.md','README.en.md','README.pt-BR.md','README.es.md','docs/LICENSE',
                  'docs/third-party/GCC-RUNTIME-EXCEPTION.txt','docs/third-party/GPL-3.0.txt','docs/third-party/MinGW-w64-NOTICES.txt']
        for name in required:
            self.assertTrue((base.ROOT/name).is_file(),name)
            self.assertIn('L"'+name.replace('/','\\\\')+'",',manifest,name)

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)
