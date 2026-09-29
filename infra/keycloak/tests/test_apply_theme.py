"""Поведение настройки существующего realm без сети и реальных секретов."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'apply-theme.sh'


class ApplyThemeTest(unittest.TestCase):
    def run_script(self, fail=''):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cli = root / 'kcadm.sh'
            cli.write_text('''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['CALLS'], 'a') as f:
    f.write(json.dumps(args) + '\\n')
config = Path(args[args.index('--config') + 1])
config.write_text('synthetic-session')
if os.environ.get('FAIL') in ('auth', 'update'):
    if ('credentials' in args and os.environ['FAIL'] == 'auth') or ('update' in args and os.environ['FAIL'] == 'update'):
        print('synthetic-secret-that-must-not-leak', file=sys.stderr)
        sys.exit(1)
''')
            cli.chmod(0o700)
            env = dict(os.environ, KEYCLOAK_BIN_DIR=folder, TMPDIR=folder,
                       KC_BOOTSTRAP_ADMIN_USERNAME='test-admin',
                       KC_BOOTSTRAP_ADMIN_PASSWORD='synthetic-secret-that-must-not-leak',
                       RADAR_THEME_ATTEMPTS='2', RADAR_THEME_RETRY_SECONDS='0',
                       CALLS=str(root / 'calls'), FAIL=fail)
            result = subprocess.run(['bash', str(SCRIPT)], env=env, capture_output=True, text=True)
            calls = [json.loads(line) for line in (root / 'calls').read_text().splitlines()]
            self.assertNotIn(env['KC_BOOTSTRAP_ADMIN_PASSWORD'], result.stdout + result.stderr)
            self.assertFalse(list(root.glob('radar-kcadm.*')))
            return result, calls

    def test_updates_only_theme_and_locale(self):
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        update = next(call for call in calls if 'update' in call)
        self.assertIn('realms/radar-vuzov', update)
        self.assertIn('--no-merge', update)
        values = [update[i + 1] for i, arg in enumerate(update) if arg == '-s']
        self.assertEqual(set(values), {'loginTheme=radar', 'internationalizationEnabled=true',
                                     'supportedLocales=["ru"]', 'defaultLocale=ru'})
        self.assertNotIn('--password', calls[0])

    def test_auth_failure_is_bounded_and_does_not_update(self):
        result, calls = self.run_script('auth')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(calls), 2)
        self.assertFalse(any('update' in call for call in calls))

    def test_update_failure_fails_deployment(self):
        result, _ = self.run_script('update')
        self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
