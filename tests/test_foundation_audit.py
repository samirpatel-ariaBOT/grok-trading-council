import tempfile
import unittest
from pathlib import Path
from tools.foundation_audit import inspect_source


class SourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def test_does_not_execute_or_import_supplied_code(self):
        self.write('danger.py', "raise RuntimeError('must never execute')\n")
        result = inspect_source(self.root)
        self.assertEqual(result['status'], 'STATIC_CHECKS_PASSED')
        self.assertEqual(result['tests_executed'], 0)
        self.assertEqual(result['trading_readiness'], 'NOT_ASSESSED')

    def test_prose_masquerading_as_code_is_rejected(self):
        self.write('test_fake.py', "Cumulative tests for canonical baseline.\nprint('All tests passed')\n")
        result = inspect_source(self.root)
        self.assertEqual(result['status'], 'REVIEW_REQUIRED')
        self.assertEqual(result['files'][0]['findings'][0]['code'], 'SYNTAX_ERROR')

    def test_success_print_is_not_counted_as_test(self):
        self.write('test_fake.py', "print('All tests passed')\n")
        result = inspect_source(self.root)
        self.assertEqual(result['files'][0]['test_definitions'], 0)
        self.assertEqual(result['status'], 'REVIEW_REQUIRED')

    def test_test_definitions_remain_unexecuted(self):
        self.write('test_real.py', 'def test_failure():\n    assert False\n')
        result = inspect_source(self.root)
        self.assertEqual(result['files'][0]['test_definitions'], 1)
        self.assertEqual(result['tests_executed'], 0)

    def test_unpublished_implementation_note_is_flagged(self):
        self.write('partial.py', '# Full implementation in local copy\nx = 1\n')
        result = inspect_source(self.root)
        self.assertEqual(result['files'][0]['findings'][0]['code'], 'POSSIBLE_OMISSION')

    def test_empty_directory_does_not_pass(self):
        self.assertEqual(inspect_source(self.root)['status'], 'EMPTY')

    def test_dependency_directories_are_excluded(self):
        self.write('.venv/broken.py', 'invalid python prose')
        self.write('app.py', 'x = 1\n')
        self.assertEqual(inspect_source(self.root)['python_files'], 1)

    def test_hash_changes_when_source_changes(self):
        path = self.write('app.py', 'x = 1\n')
        before = inspect_source(self.root)['files'][0]['sha256']
        path.write_text('x = 2\n')
        self.assertNotEqual(before, inspect_source(self.root)['files'][0]['sha256'])

    def test_missing_root_is_error(self):
        with self.assertRaises(FileNotFoundError):
            inspect_source(self.root / 'missing')


if __name__ == '__main__':
    unittest.main()
