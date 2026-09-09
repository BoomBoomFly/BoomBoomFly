"""本地 Git 远端验证按范围提交，不访问网络。"""
import shutil
import subprocess
import tempfile
from pathlib import Path


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.STDOUT).decode().strip()


def test_scopes():
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        root = base / 'workspace'
        scripts = root / 'Scripts'
        scripts.mkdir(parents=True)
        shutil.copyfile(Path(__file__).resolve().parents[2] / 'push_git.sh', scripts / 'push_git.sh')
        child = root / 'px4/px4_ws/src/boomboom/example'
        child.mkdir(parents=True)
        (root / '.gitignore').write_text('px4/\n')
        for i, repo in enumerate((root, child)):
            remote = base / f'{i}.git'
            subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
            git(repo, 'init', '-b', 'main')
            git(repo, 'config', 'user.name', 'Test')
            git(repo, 'config', 'user.email', 'test@example.com')
            git(repo, 'add', '-A')
            git(repo, 'commit', '--allow-empty', '-m', 'baseline')
            git(repo, 'remote', 'add', 'origin', str(remote))
            git(repo, 'push', '-u', 'origin', 'main')
        for repo in (root, child):
            (repo / 'new').write_text('changes')
        def run(scope, message):
            return subprocess.run(['bash', str(scripts / 'push_git.sh'), scope, message], capture_output=True)
        root_head = git(root, 'rev-parse', 'HEAD')
        assert run('boomboom', '更新自研功能包').returncode == 0
        assert git(root, 'rev-parse', 'HEAD') == root_head
        assert git(root, 'status', '--porcelain') == '?? new'
        assert git(child, 'log', '-1', '--format=%s') == '更新自研功能包'
        child_head = git(child, 'rev-parse', 'HEAD')
        assert run('main', '更新脚本与文档').returncode == 0
        assert git(child, 'rev-parse', 'HEAD') == child_head
        assert git(root, 'log', '-1', '--format=%s') == '更新脚本与文档'
        heads = [git(repo, 'rev-parse', 'HEAD') for repo in (root, child)]
        assert run('all', '无改动').returncode == 0
        assert heads == [git(repo, 'rev-parse', 'HEAD') for repo in (root, child)]
        for i, repo in enumerate((root, child)):
            assert git(base / f'{i}.git', 'rev-parse', 'main') == git(repo, 'rev-parse', 'HEAD')
        assert run('invalid', '说明').returncode == 2
        assert run('main', ' ').returncode == 2


if __name__ == '__main__':
    test_scopes()
    print('PASS: scope isolation, commit messages, local push, clean rerun, invalid arguments')
