#!/usr/bin/env python3
"""仅在临时目录和本地 bare 仓库验证脚本行为。"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile


SCRIPTS = Path(__file__).resolve().parent


def run(*args, cwd=None, ok=True):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    assert (result.returncode == 0) == ok, (args, result.stdout, result.stderr)
    return result.stdout.strip()


def init_repo(path, remote):
    path.mkdir(parents=True, exist_ok=True)
    run('git', 'init', '--bare', str(remote))
    run('git', 'init', '-b', 'main', str(path))
    run('git', '-C', str(path), 'config', 'user.name', 'Script Test')
    run('git', '-C', str(path), 'config', 'user.email', 'test@example.invalid')
    run('git', '-C', str(path), 'remote', 'add', 'origin', str(remote))


def main():
    for script in SCRIPTS.glob('*.sh'):
        run('bash', '-n', str(script))
    run('bash', '-n', str(SCRIPTS / 'setup_ros_environment.bash'))
    run('bash', str(SCRIPTS / 'setup_ros_environment.bash'), ok=False)
    with tempfile.TemporaryDirectory(prefix='boomboomfly-scripts-') as directory:
        temp = Path(directory)
        # 防止用户的全局 Git 配置或 hook 影响本地检查。
        os.environ['GIT_CONFIG_GLOBAL'] = os.devnull
        os.environ['GIT_CONFIG_NOSYSTEM'] = '1'
        root = temp / 'project'
        init_repo(root, temp / 'main.git')
        shutil.copytree(SCRIPTS, root / 'Scripts')
        package = root / 'ros_ws/src/uav_control'
        init_repo(package, temp / 'control.git')
        (package / 'control.txt').write_text('control\n')
        for relative in ('ros_ws/src/thirdparty/mock/file', 'ros_ws/upstream/file',
                         'ros_ws/build/file', 'references/mock/file',
                         'docker/kalibr/source/file'):
            file = root / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('excluded\n')
        (root / 'README.md').write_text('root\n')
        push = root / 'Scripts/push_git.sh'
        run('bash', str(push), 'main', 'root commit', cwd=temp)
        tracked = run('git', '-C', str(root), 'ls-files').splitlines()
        assert 'README.md' in tracked
        assert all(p == 'README.md' or p.startswith('Scripts/') for p in tracked)
        root_head = run('git', '-C', str(root), 'rev-parse', 'HEAD')
        run('bash', str(push), 'uav_control', 'control commit', cwd=temp)
        assert run('git', '-C', str(root), 'rev-parse', 'HEAD') == root_head
        assert run('git', '-C', str(package), 'status', '--porcelain') == ''
        head = run('git', '-C', str(package), 'rev-parse', 'HEAD')
        assert head in run('git', 'ls-remote', str(temp / 'control.git'), 'refs/heads/main')
        run('bash', str(push), 'uav_control', 'no changes')
        assert run('git', '-C', str(package), 'rev-parse', 'HEAD') == head
        run('git', '-C', str(root), 'add', 'ros_ws/src/thirdparty/mock/file')
        index_before = run('git', '-C', str(root), 'diff', '--cached')
        run('bash', str(push), 'main', 'must reject', ok=False)
        assert run('git', '-C', str(root), 'diff', '--cached') == index_before
        run('bash', str(push), 'unknown', 'must reject', ok=False)
        run('bash', str(push), 'main', ' ', ok=False)
        run('git', '-C', str(package), 'checkout', '--detach')
        run('bash', str(push), 'uav_control', 'must reject', ok=False)
        run('git', '-C', str(package), 'checkout', 'main')
        # 远端新增提交后，同步脚本应只做快进。
        peer = temp / 'peer'
        run('git', 'clone', '-b', 'main', str(temp / 'control.git'), str(peer))
        (peer / 'new.txt').write_text('remote update\n')
        run('git', '-C', str(peer), 'add', 'new.txt')
        run('git', '-C', str(peer), '-c', 'user.name=Test',
            '-c', 'user.email=test@example.invalid', 'commit', '-m', 'update')
        run('git', '-C', str(peer), 'push')
        sync = root / 'Scripts/sync_ros_packages.sh'
        run('bash', str(sync), cwd=temp)
        assert (package / 'new.txt').read_text() == 'remote update\n'
        # 首次 clone 通过 Git URL rewrite 转向本地 bare 仓库。
        shutil.rmtree(package)
        config = temp / 'gitconfig'
        run('git', 'config', '--file', str(config),
            f'url.{temp / "control.git"}.insteadOf',
            'https://github.com/BoomBoomFly/uav_control.git')
        run('git', '--git-dir', str(temp / 'control.git'), 'symbolic-ref', 'HEAD', 'refs/heads/main')
        os.environ['GIT_CONFIG_GLOBAL'] = str(config)
        run('bash', str(sync), cwd=temp)
        assert (package / 'new.txt').exists()
        shutil.rmtree(package / '.git')
        run('bash', str(sync), ok=False)
        run('bash', str(push), 'uav_control', 'must reject', ok=False)
        assert (package / 'new.txt').exists()
    print('PASS: syntax, scope isolation, push, clone, fast-forward, refusal guards')


if __name__ == '__main__':
    main()
