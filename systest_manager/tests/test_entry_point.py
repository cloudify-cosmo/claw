from systest_manager import tests


class EntryPointTests(tests.BaseTest):

    def test_direct_script_execution(self):
        self.init()
        self.systest.generate(tests.STUB_CONFIGURATION)
        script_path = self.workdir / 'script.py'
        text_path = self.workdir / 'test.txt'
        text = 'TEXT'
        script_path.write_text('''from path import path
script = lambda: path('{0}').write_text('{1}')
'''.format(text_path, text))
        self.systest(script_path)
        self.assertEqual(text, text_path.text())
