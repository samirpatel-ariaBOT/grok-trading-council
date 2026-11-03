"""Read-only source inventory. Never imports code or claims trading readiness."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

EXCLUDED = {'.git', '.venv', 'venv', 'node_modules', '__pycache__'}
OMISSIONS = re.compile(r'\bplaceholder\b|full implementation would|full implementation in local copy', re.I)
MAX_FILE_BYTES = 2_000_000


def inspect_source(root: Path) -> dict:
    """Inventory Python bytes without executing them; absence is never a pass."""
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Source root must be a directory')
    files = []
    for path in sorted(root.rglob('*.py')):
        relative = path.relative_to(root)
        if any(part in EXCLUDED for part in relative.parts):
            continue
        entry = {'path': relative.as_posix(), 'sha256': None,
                 'syntax': 'NOT_CHECKED', 'test_definitions': 0, 'findings': []}
        files.append(entry)
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            entry['findings'].append({'code': 'LINK_NOT_READ'})
            continue
        try:
            with path.open('rb') as source:
                data = source.read(MAX_FILE_BYTES + 1)
            if len(data) > MAX_FILE_BYTES:
                entry['findings'].append({'code': 'FILE_TOO_LARGE'})
                continue
            entry['sha256'] = hashlib.sha256(data).hexdigest()
            # ast.parse(bytes) respects Python's declared source encoding.
            tree = ast.parse(data, filename=relative.as_posix())
            entry['syntax'] = 'VALID'
            entry['test_definitions'] = sum(
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name.startswith('test_') for node in ast.walk(tree)
            )
        except SyntaxError as exc:
            entry['syntax'] = 'INVALID'
            entry['findings'].append({'code': 'SYNTAX_ERROR', 'line': exc.lineno,
                                      'message': exc.msg})
            continue
        except (OSError, ValueError) as exc:
            entry['findings'].append({'code': 'READ_OR_PARSE_ERROR',
                                      'message': str(exc)})
            continue
        # These are review hints, not a proof that other files are complete.
        for line_number, line in enumerate(data.decode('utf-8', errors='replace').splitlines(), 1):
            if OMISSIONS.search(line):
                entry['findings'].append({'code': 'POSSIBLE_OMISSION', 'line': line_number})
        if path.name.startswith('test_') and entry['test_definitions'] == 0:
            entry['findings'].append({'code': 'NO_TEST_DEFINITIONS',
                                     'message': 'Manual/top-level checks need separate execution evidence.'})
    findings = sum(len(f['findings']) for f in files)
    return {'schema_version': 'source-audit-1',
            'status': 'EMPTY' if not files else ('REVIEW_REQUIRED' if findings else 'STATIC_CHECKS_PASSED'),
            'python_files': len(files), 'finding_count': findings,
            'tests_executed': 0, 'trading_readiness': 'NOT_ASSESSED',
            'note': 'Definitions are not executed tests. Valid syntax is not correct behavior. '
                    'This tool does not authenticate bots, run tests, measure performance or approve operation.',
            'files': files}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    try:
        result = inspect_source(args.root)
    except (OSError, ValueError) as exc:
        print(json.dumps({'status': 'INPUT_ERROR', 'message': str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'STATIC_CHECKS_PASSED' else 1


if __name__ == '__main__':
    sys.exit(main())
