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
        package = root / 'uav_ws/src/uav_control'
        init_repo(package, temp / 'control.git')
        (package / 'control.txt').write_text('control\n')
        bridge = root / 'uav_ws/src/uav_vio_bridge'
        init_repo(bridge, temp / 'bridge.git')
        (bridge / 'bridge.txt').write_text('bridge\n')
        bringup = root / 'uav_ws/src/uav_bringup'
        init_repo(bringup, temp / 'bringup.git')
        (bringup / 'bringup.txt').write_text('bringup\n')
        mission = root / 'uav_ws/src/uav_mission'
        init_repo(mission, temp / 'mission.git')
        (mission / 'mission.txt').write_text('mission\n')
        (package / 'uav_interfaces/msg').mkdir(parents=True)
        (package / 'uav_interfaces/msg/VehicleState.msg').write_text('string mode\n')
        for relative in ('uav_ws/src/thirdparty/mock/file', 'uav_ws/upstream/file',
                         'uav_ws/build/file', 'references/mock/file',
                         'docker/kalibr/source/file'):
            file = root / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('excluded\n')
        (root / 'README.md').write_text('root\n')
        (root / 'uav_ws/sim').mkdir(parents=True)
        (root / 'uav_ws/sim/README.md').write_text('simulation\n')
        for workspace in ('swarm_ws', 'ugv_ws'):
            repo = root / workspace
            init_repo(repo, temp / f'{workspace}.git')
            (repo / 'sim').mkdir()
            (repo / 'sim/README.md').write_text('workspace simulation\n')
        push = root / 'Scripts/push_git.sh'
        run('bash', str(push), 'main', 'root commit', cwd=temp)
        tracked = run('git', '-C', str(root), 'ls-files').splitlines()
        assert 'README.md' in tracked
        assert all(p in ('README.md', 'uav_ws/sim/README.md') or p.startswith('Scripts/') for p in tracked)
        root_head = run('git', '-C', str(root), 'rev-parse', 'HEAD')
        for workspace in ('swarm_ws', 'ugv_ws'):
            run('bash', str(push), workspace, 'workspace commit', cwd=temp)
            repo = root / workspace
            assert run('git', '-C', str(repo), 'status', '--porcelain') == ''
            run('git', '-C', str(root), 'add', workspace)
            before = run('git', '-C', str(root), 'diff', '--cached')
            run('bash', str(push), 'main', 'must reject workspace', ok=False)
            assert run('git', '-C', str(root), 'diff', '--cached') == before
            run('git', '-C', str(root), 'reset', 'HEAD', '--', workspace)
        run('bash', str(push), 'uav_control', 'control commit', cwd=temp)
        assert run('git', '-C', str(root), 'rev-parse', 'HEAD') == root_head
        assert run('git', '-C', str(package), 'status', '--porcelain') == ''
        head = run('git', '-C', str(package), 'rev-parse', 'HEAD')
        assert head in run('git', 'ls-remote', str(temp / 'control.git'), 'refs/heads/main')
        run('bash', str(push), 'uav_control', 'no changes')
        assert run('git', '-C', str(package), 'rev-parse', 'HEAD') == head
        run('bash', str(push), 'uav_vio_bridge', 'bridge commit', cwd=temp)
        bridge_head = run('git', '-C', str(bridge), 'rev-parse', 'HEAD')
        assert bridge_head in run('git', 'ls-remote', str(temp / 'bridge.git'),
                                  'refs/heads/main')
        assert run('git', '-C', str(root), 'rev-parse', 'HEAD') == root_head
        assert run('git', '-C', str(package), 'rev-parse', 'HEAD') == head
        assert run('git', '-C', str(bridge), 'status', '--porcelain') == ''
        run('bash', str(push), 'uav_vio_bridge', 'no changes')
        assert run('git', '-C', str(bridge), 'rev-parse', 'HEAD') == bridge_head
        run('bash', str(push), 'uav_bringup', 'bringup commit', cwd=temp)
        bringup_head = run('git', '-C', str(bringup), 'rev-parse', 'HEAD')
        assert bringup_head in run('git', 'ls-remote', str(temp / 'bringup.git'),
                                   'refs/heads/main')
        assert run('git', '-C', str(root), 'rev-parse', 'HEAD') == root_head
        run('bash', str(push), 'uav_bringup', 'no changes')
        assert run('git', '-C', str(bringup), 'rev-parse', 'HEAD') == bringup_head
        run('bash', str(push), 'uav_mission', 'mission commit', cwd=temp)
        mission_head = run('git', '-C', str(mission), 'rev-parse', 'HEAD')
        assert mission_head in run('git', 'ls-remote', str(temp / 'mission.git'),
                                   'refs/heads/main')
        assert run('git', '-C', str(root), 'rev-parse', 'HEAD') == root_head
        run('bash', str(push), 'uav_mission', 'no changes')
        assert run('git', '-C', str(mission), 'rev-parse', 'HEAD') == mission_head
        assert run('git', '-C', str(package), 'ls-tree', '-r', 'HEAD',
                   '--name-only').count('uav_interfaces/msg/VehicleState.msg') == 1
        run('git', '-C', str(root), 'add', 'uav_ws/src/uav_bringup')
        index_before = run('git', '-C', str(root), 'diff', '--cached')
        run('bash', str(push), 'main', 'must reject bringup', ok=False)
        assert run('git', '-C', str(root), 'diff', '--cached') == index_before
        run('git', '-C', str(root), 'reset', 'HEAD', '--', 'uav_ws/src/uav_bringup')
        run('git', '-C', str(root), 'add', 'uav_ws/src/uav_mission')
        index_before = run('git', '-C', str(root), 'diff', '--cached')
        run('bash', str(push), 'main', 'must reject mission', ok=False)
        assert run('git', '-C', str(root), 'diff', '--cached') == index_before
        run('git', '-C', str(root), 'reset', 'HEAD', '--', 'uav_ws/src/uav_mission')
        # 即使独立包误入主仓库暂存区，也必须停止并保留暂存内容。
        run('git', '-C', str(root), 'add', 'uav_ws/src/uav_vio_bridge')
        index_before = run('git', '-C', str(root), 'diff', '--cached')
        run('bash', str(push), 'main', 'must reject bridge', ok=False)
        assert run('git', '-C', str(root), 'diff', '--cached') == index_before
        run('git', '-C', str(root), 'reset', 'HEAD', '--', 'uav_ws/src/uav_vio_bridge')
        run('git', '-C', str(root), 'add', 'uav_ws/src/thirdparty/mock/file')
        index_before = run('git', '-C', str(root), 'diff', '--cached')
        run('bash', str(push), 'main', 'must reject', ok=False)
        assert run('git', '-C', str(root), 'diff', '--cached') == index_before
        # 使用实际 ignore 规则验证主仓库发布，sim 文件仍应纳入。
        run('git', '-C', str(root), 'reset', 'HEAD', '--', 'uav_ws/src/thirdparty/mock/file')
        shutil.copyfile(SCRIPTS.parent / '.gitignore', root / '.gitignore')
        (root / 'uav_ws/sim/README.md').write_text('updated simulation\n')
        run('bash', str(push), 'main', 'ignore-aware root commit')
        assert run('git', '-C', str(root), 'show', 'HEAD:uav_ws/sim/README.md') == 'updated simulation'
        run('bash', str(push), 'unknown', 'must reject', ok=False)
        run('bash', str(push), 'main', ' ', ok=False)
        run('git', '-C', str(package), 'checkout', '--detach')
        run('bash', str(push), 'uav_control', 'must reject', ok=False)
        run('git', '-C', str(package), 'checkout', 'main')
        # 远端新增提交后，同步脚本应只做快进。
        for remote in ('control.git', 'bridge.git', 'bringup.git', 'mission.git', 'swarm_ws.git', 'ugv_ws.git'):
            peer = temp / f'peer-{remote}'
            run('git', 'clone', '-b', 'main', str(temp / remote), str(peer))
            (peer / 'new.txt').write_text('remote update\n')
            run('git', '-C', str(peer), 'add', 'new.txt')
            run('git', '-C', str(peer), '-c', 'user.name=Test',
                '-c', 'user.email=test@example.invalid', 'commit', '-m', 'update')
            run('git', '-C', str(peer), 'push')
        sync = root / 'Scripts/sync_ros_packages.sh'
        run('bash', str(sync), cwd=temp)
        assert (package / 'new.txt').read_text() == 'remote update\n'
        assert (bridge / 'new.txt').read_text() == 'remote update\n'
        assert (bringup / 'new.txt').read_text() == 'remote update\n'
        assert (mission / 'new.txt').read_text() == 'remote update\n'
        # 首次 clone 通过 Git URL rewrite 转向本地 bare 仓库。
        shutil.rmtree(package)
        shutil.rmtree(bridge)
        shutil.rmtree(bringup)
        shutil.rmtree(mission)
        shutil.rmtree(root / 'swarm_ws')
        shutil.rmtree(root / 'ugv_ws')
        config = temp / 'gitconfig'
        for name, remote in (('uav_control', 'control.git'), ('uav_vio_bridge', 'bridge.git'),
                             ('uav_bringup', 'bringup.git'), ('uav_mission', 'mission.git'),
                             ('swarm_ws', 'swarm_ws.git'), ('ugv_ws', 'ugv_ws.git')):
            run('git', 'config', '--file', str(config),
                f'url.{temp / remote}.insteadOf',
                f'https://github.com/BoomBoomFly/{name}.git')
            run('git', '--git-dir', str(temp / remote),
                'symbolic-ref', 'HEAD', 'refs/heads/main')
        os.environ['GIT_CONFIG_GLOBAL'] = str(config)
        run('bash', str(sync), cwd=temp)
        assert (package / 'new.txt').exists()
        assert (package / 'uav_interfaces/msg/VehicleState.msg').exists()
        assert (bridge / 'new.txt').exists()
        assert (bringup / 'new.txt').exists()
        assert (mission / 'new.txt').exists()
        assert (root / 'swarm_ws/new.txt').exists()
        assert (root / 'ugv_ws/new.txt').exists()
        run('bash', str(sync), 'swarm_ws', 'ugv_ws', cwd=temp)
        run('bash', str(sync), 'unknown', ok=False)
        shutil.rmtree(bringup / '.git')
        run('bash', str(sync), ok=False)
        run('bash', str(push), 'uav_bringup', 'must reject', ok=False)
        assert (bringup / 'new.txt').exists()
        shutil.rmtree(bridge / '.git')
        run('bash', str(sync), ok=False)
        run('bash', str(push), 'uav_vio_bridge', 'must reject', ok=False)
        assert (bridge / 'new.txt').exists()
        shutil.rmtree(package / '.git')
        run('bash', str(sync), ok=False)
        run('bash', str(push), 'uav_control', 'must reject', ok=False)
        assert (package / 'new.txt').exists()
        shutil.rmtree(mission / '.git')
        run('bash', str(sync), ok=False)
        run('bash', str(push), 'uav_mission', 'must reject', ok=False)
        assert (mission / 'new.txt').exists()
        # 使用临时 overlay 验证环境工作区选择；不启动任何 ROS 节点。
        setup = root / 'Scripts/setup_ros_environment.bash'
        for workspace in ('uav_ws', 'ugv_ws', 'swarm_ws'):
            overlay = root / workspace / 'install/local_setup.bash'
            overlay.parent.mkdir(parents=True, exist_ok=True)
            overlay.write_text(f'export BBF_TEST_WORKSPACE={workspace}\n')
            if Path('/opt/ros/humble/setup.bash').exists():
                selected = run('bash', '-c', 'source "$1" "$2" && printf "%s" "$BBF_TEST_WORKSPACE"',
                               'test', str(setup), workspace)
                assert selected == workspace
        run('bash', '-c', 'source "$1" unknown', 'test', str(setup), ok=False)
    print('PASS: syntax, scope isolation, push, clone, fast-forward, refusal guards')


if __name__ == '__main__':
    main()
