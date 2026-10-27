import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('desktop', Path(__file__).parents[1] / 'scripts/desktop.py')
desktop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desktop)


class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root, self.config, self.state = base / 'repo', base / 'config', base / 'state'
        self.root.mkdir()
        self.config.mkdir()
        self.cstate = self.state / 'caelestia'
        self.cstate.mkdir(parents=True)
        self.write('manifest.toml', '''[[components]]
name = "app"
[[components.entries]]
src = "app"
dest = "$XDG_CONFIG_HOME/app"
[[components]]
name = "disabled"
[[components.entries]]
src = "disabled"
dest = "$XDG_CONFIG_HOME/disabled"
''')
        self.write('app/settings.json', '{"value":1}')
        self.write('app/sub/extra.conf', 'extra')
        self.write('disabled/config', 'disabled')
        self.write('config/caelestia/shell.json', '{}')
        self.write('shell/shell.qml', 'ShellRoot {}')
        self.write('shell/services/Example.qml', 'Item {}')
        self.write('docs/shell-source.json', '{"tag":"v2.5.0"}')
        (self.cstate / 'dots-state.json').write_text(json.dumps({'enabled_components': ['app']}))
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', '-C', str(self.root), 'add', '.'], check=True)
        self.settings = self.config / 'app/settings.json'
        self.settings.parent.mkdir()
        self.settings.write_text('original')
        for name, value in [('ROOT', self.root), ('CONFIG', self.config),
                            ('STATE', self.state / 'caelestia-management'), ('CAELESTIA_STATE', self.cstate)]:
            patcher = patch.object(desktop, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(desktop, 'verify_native_version')
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, name, value):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(value)
        return p

    def backups(self):
        return sorted((desktop.STATE / 'backups').iterdir())

    def test_apply_repeat_edit_and_restore(self):
        # Generated files are not part of the deployment.
        self.write('app/cache.log', 'cache')
        (self.root / '.gitignore').write_text('app/cache.log\n')
        desktop.apply(no_reload=True)
        self.assertEqual(self.settings.read_text(), '{"value":1}')
        self.assertFalse(self.settings.is_symlink())
        self.assertFalse((self.config / 'disabled').exists())
        self.assertFalse((self.config / 'app/cache.log').exists())
        shell_link = self.config / 'quickshell/caelestia'
        old_shell = shell_link.resolve()
        self.assertTrue(old_shell.is_relative_to(self.cstate / 'deployments'))
        desktop.apply(no_reload=True)
        self.assertEqual(len(self.backups()), 1)
        self.write('app/settings.json', '{"value":2}')
        desktop.apply(no_reload=True)
        self.assertEqual(self.settings.read_text(), '{"value":2}')
        self.assertNotEqual(shell_link.resolve(), old_shell)
        desktop.restore(self.backups()[-1])
        self.assertEqual(self.settings.read_text(), '{"value":1}')
        desktop.restore(self.backups()[0])
        self.assertEqual(self.settings.read_text(), 'original')
        self.assertFalse(shell_link.exists())
        self.assertFalse((self.config / 'app/sub/extra.conf').exists())

    def test_invalid_json_changes_nothing(self):
        self.write('app/settings.json', 'invalid')
        with self.assertRaises(ValueError):
            desktop.apply(no_reload=True)
        self.assertEqual(self.settings.read_text(), 'original')
        self.assertFalse((desktop.STATE / 'backups').exists())

    def test_restore_preserves_later_local_edit(self):
        desktop.apply(no_reload=True)
        self.settings.write_text('local edit')
        with self.assertRaises(SystemExit):
            desktop.restore(self.backups()[0])
        self.assertEqual(self.settings.read_text(), 'local edit')

    def test_failed_start_restores_originals_and_restarts_old_shell(self):
        real_run = desktop.run
        real_process = subprocess.run

        def command(*args):
            return real_run(*args) if args[0] == 'git' else ''

        def process(args, **kwargs):
            if args[0] == 'caelestia':
                return subprocess.CompletedProcess(args, 0)
            return real_process(args, **kwargs)

        with patch.object(desktop, 'run', side_effect=command), \
                patch.object(desktop, 'start_and_check', side_effect=[RuntimeError('failed startup'), None]) as start, \
                patch.object(desktop.subprocess, 'run', side_effect=process):
            with self.assertRaisesRegex(RuntimeError, 'failed startup'):
                desktop.apply()
            self.assertEqual(start.call_count, 2)
        self.assertEqual(self.settings.read_text(), 'original')
        self.assertFalse((self.config / 'quickshell/caelestia').exists())


if __name__ == '__main__':
    unittest.main()
