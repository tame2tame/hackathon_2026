"""Проверка подключения темы: python3 -m unittest discover -s infra/keycloak/tests."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
THEME = ROOT / 'infra/keycloak/themes/radar/login'


class LoginThemeTest(unittest.TestCase):
    def test_realm_uses_russian_brand_theme(self):
        realm = json.loads((ROOT / 'infra/keycloak/realm-radar-vuzov.json').read_text())
        self.assertEqual(realm.get('loginTheme'), 'radar')
        self.assertTrue(realm.get('internationalizationEnabled'))
        self.assertEqual(realm.get('defaultLocale'), 'ru')
        self.assertEqual(realm.get('supportedLocales'), ['ru'])

    def test_theme_is_available_in_both_environments(self):
        for name in ('docker-compose.yml', 'docker-compose.prod.yml'):
            with self.subTest(name=name):
                config = (ROOT / 'infra' / name).read_text()
                for expected in (
                    './keycloak/themes/radar:/opt/keycloak/themes/radar:ro',
                    './keycloak/apply-theme.sh:/opt/keycloak/radar/apply-theme.sh:ro',
                    './keycloak/start-with-theme.sh:/opt/keycloak/radar/start-with-theme.sh:ro',
                    'entrypoint: ["bash", "/opt/keycloak/radar/start-with-theme.sh"]',
                    'test: ["CMD", "test", "-f", "/tmp/radar-theme-ready"]',
                ):
                    self.assertTrue(expected in config, expected)

    def test_native_auth_templates_are_inherited(self):
        properties = (THEME / 'theme.properties').read_text()
        self.assertIn('parent=keycloak', properties)
        self.assertIn('css/radar.css', properties)
        # Сохраняем штатные формы, обработку ошибок, смену пароля и OIDC.
        self.assertFalse((THEME / 'login.ftl').exists())
        self.assertFalse((THEME / 'template.ftl').exists())
        for weight in ('Regular', 'Medium', 'Bold'):
            asset = THEME / 'resources/fonts' / f'RostelecomBasis-{weight}.woff2'
            self.assertEqual(asset.read_bytes()[:4], b'wOF2')
        messages = (THEME / 'messages/messages_ru.properties').read_text()
        self.assertIn('doLogIn=Войти', messages)
        self.assertIn('invalidUserMessage=Неверный логин или пароль.', messages)


if __name__ == '__main__':
    unittest.main()
