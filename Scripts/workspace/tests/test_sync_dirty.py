"""固定提交允许保留本地文件，分支更新仍拒绝脏工作树。"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sync_repos


class DirtySyncTest(unittest.TestCase):
    def test_fixed_commit_fetch_preserves_dirty_tree(self):
        def git(*args):
            return subprocess.check_output(['git', *map(str, args)], stderr=subprocess.STDOUT).decode().strip()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            origin, repo = root / 'origin', root / 'repo'
            git('init', '-b', 'main', origin)
            git('-C', origin, '-c', 'user.name=Test', '-c', 'user.email=test@example.com',
                'commit', '--allow-empty', '-m', 'baseline')
            git('clone', origin, repo)
            head = git('-C', repo, 'rev-parse', 'HEAD')
            (repo / 'build-output').write_text('keep')
            spec = {'url': str(origin), 'version': head}
            with patch.object(sync_repos, 'CORE_MANIFEST_ROOTS', [(root / 'manifest', root)]), \
                 patch.object(sync_repos, 'PERCEPTION_DEPS_MANIFEST_ROOT', (root / 'optional', root)), \
                 patch.object(sync_repos, 'load_manifest', side_effect=lambda p: {'repo': spec} if p.name == 'manifest' else {}), \
                 patch.object(sys, 'argv', ['sync_repos.py', 'update']):
                sync_repos.main()
                self.assertTrue((repo / '.git/FETCH_HEAD').is_file())
                self.assertEqual(git('-C', repo, 'rev-parse', 'HEAD'), head)
                self.assertEqual((repo / 'build-output').read_text(), 'keep')
                spec['version'] = 'main'
                with self.assertRaisesRegex(SystemExit, 'dirty repository'):
                    sync_repos.main()


if __name__ == '__main__':
    unittest.main()
