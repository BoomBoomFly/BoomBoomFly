"""用本地 Git 仓库验证恢复脚本，不访问网络或真实工作区。"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

SCRIPT = Path(__file__).resolve().parents[1] / 'pull_repos.sh'


@unittest.skipUnless(shutil.which('vcs') and shutil.which('git'), 'requires vcstool and git')
class PullReposTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='boomboom-import-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.origin = self.root / 'origin'
        self.origin.mkdir()
        self.git(self.origin, 'init', '-q')
        (self.origin / 'content').write_text('baseline\n')
        self.git(self.origin, 'add', 'content')
        self.git(self.origin, '-c', 'user.name=Test', '-c', 'user.email=test@example.com',
                 'commit', '-qm', 'baseline')
        self.sha = self.git(self.origin, 'rev-parse', 'HEAD').stdout.strip()
        self.workspace = self.root / 'workspace with spaces'
        scripts = self.workspace / 'Scripts/workspace'
        scripts.mkdir(parents=True)
        shutil.copy2(SCRIPT, scripts / SCRIPT.name)
        manifests = self.workspace / 'manifests'
        manifests.mkdir()
        for name, relative in [('boomboom', 'boomboom/common'),
                               ('upstream', 'Agent'),
                               ('perception_deps', 'external/camera')]:
            (manifests / (name + '.repos')).write_text(yaml.safe_dump({
                'repositories': {relative: {'type': 'git', 'url': str(self.origin),
                                            'version': self.sha}}}))
        self.core = self.workspace / 'px4/px4_ws/src/boomboom/common'
        self.upstream = self.workspace / 'px4/upstream/Agent'
        self.optional = self.workspace / 'px4/px4_ws/src/external/camera'

    def git(self, path, *args):
        return subprocess.run(['git', '-C', str(path), *args], text=True,
                              capture_output=True, check=True)

    def run_import(self, *args):
        return subprocess.run(['bash', str(self.workspace / 'Scripts/workspace/pull_repos.sh'),
                               *args], text=True, capture_output=True)

    def assert_imported(self, path):
        self.assertEqual(self.git(path, 'rev-parse', 'HEAD').stdout.strip(), self.sha)
        self.assertEqual((path / 'content').read_text(), 'baseline\n')

    def test_empty_core_and_upstream_import_and_repeat_preserves_changes(self):
        for path in (self.core, self.upstream, self.optional):
            path.mkdir(parents=True)
        result = self.run_import()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for path in (self.core, self.upstream):
            self.assert_imported(path)
        self.assertEqual(list(self.optional.iterdir()), [])
        (self.core / 'content').write_text('local change\n')
        result = self.run_import()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.core / 'content').read_text(), 'local change\n')
        self.assertEqual(self.git(self.core, 'rev-parse', 'HEAD').stdout.strip(), self.sha)

    def test_optional_flags_import_empty_directory(self):
        for flag in ('--with-perception-deps', '--with-perception'):
            with self.subTest(flag=flag):
                if self.optional.exists():
                    shutil.rmtree(self.optional)
                self.optional.mkdir(parents=True)
                result = self.run_import(flag)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assert_imported(self.optional)

    def test_nonempty_nonrepository_blocks_before_removing_placeholders(self):
        self.core.mkdir(parents=True)
        self.upstream.mkdir(parents=True)
        (self.upstream / '.keep').write_text('user data')
        result = self.run_import()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(str(self.upstream), result.stderr)
        self.assertEqual((self.upstream / '.keep').read_text(), 'user data')
        self.assertTrue(self.core.is_dir())
        self.assertEqual(list(self.core.iterdir()), [])

    def test_symlink_is_not_removed_or_imported_through(self):
        self.core.parent.mkdir(parents=True)
        self.core.symlink_to(self.origin, target_is_directory=True)
        result = self.run_import()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('symlink', result.stderr)
        self.assertTrue(self.core.is_symlink())
        self.assert_imported(self.origin)


if __name__ == '__main__':
    unittest.main()
