import sh

from systest import tests


class EntryPointTests(tests.BaseTest):

    configuration = tests.STUB_CONFIGURATION

    def test_command_error(self):
        self.init()
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.systest.script('I DONT EXIST', 'STUB_PATH')
        self.assertIn('error: Not initialized', c.exception.stderr)

    def test_direct_script_execution(self):
        text = 'TEXT'
        script = '''
from systest import conf
def script(arg):
    print arg + ':' + conf.configuration
'''
        p = self._run_script(script, text)
        self.assertEqual('{0}:{1}'.format(text, self.configuration),
                         p.stdout.strip())

    def test_direct_script_execution_error(self):
        script = '''
def script(arg):
    raise RuntimeError(arg)
'''
        message = 'MESSAGE'
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self._run_script(script, message)
        self.assertIn('RuntimeError: {0}'.format(message), c.exception.stderr)

    def test_direct_script_execution_command_error(self):
        self.init()
        script_path = self.workdir / 'script.py'
        script_path.touch()
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.systest(script_path)
        self.assertIn('error: Not initialized', c.exception.stderr)

    def _run_script(self, script, *args):
        self.init()
        self.systest.generate(self.configuration)
        script_path = self.workdir / 'script.py'
        script_path.write_text(script)
        return self.systest(script_path, *args)
