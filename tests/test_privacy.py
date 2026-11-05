import unittest
from scripts.check_privacy import content_issues, path_issue


class PrivacyTests(unittest.TestCase):
    def test_private_paths_are_rejected(self):
        for name in ['private/rules.json', 'data/export.json', 'statement.csv', '.env', 'backup.pdf', '.codex/state.json']:
            self.assertTrue(path_issue(name), name)
        for name in ['config/rules.example.json', '.env.example', 'README.md']:
            self.assertFalse(path_issue(name), name)

    def test_identifiers_are_detected_without_echoing_values(self):
        synthetic_account = '12' * 13
        self.assertIn('bank account', content_issues(synthetic_account.encode(), 'example.py'))
        synthetic_phone = '48' + '1' * 9
        self.assertIn('long numeric identifier', content_issues(synthetic_phone.encode(), 'example.py'))

    def test_synthetic_and_noreply_emails_are_allowed(self):
        self.assertFalse(content_issues(b'demo@example.invalid', 'README.md'))
        self.assertFalse(content_issues(b'account@users.noreply.github.com', 'commit metadata'))


if __name__ == '__main__':
    unittest.main()
