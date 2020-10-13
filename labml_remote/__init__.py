import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import paramiko
from labml import monit, logger
from labml.logger import Text
from paramiko import SSHClient
from scp import SCPClient

from labml_remote.configs import Configs


def connect() -> paramiko.SSHClient:
    conf = Configs.get()
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    with monit.section(f'Connecting to {conf.hostname}'):
        c.connect(hostname=conf.hostname,
                  username=conf.username,
                  pkey=conf.private_key,
                  password=conf.password)

    return c


def execute_stream(client: SSHClient, command: str, *, is_silent=True):
    with monit.section(f'Exec: {command}', is_silent=is_silent):
        channel = client.get_transport().open_session()
        channel.exec_command(command)

        while True:
            while channel.recv_ready():
                sys.stdout.write(channel.recv(1024).decode('utf-8'))
            while channel.recv_stderr_ready():
                sys.stderr.write(channel.recv_stderr(1024).decode('utf-8'))
            if channel.exit_status_ready():
                break
        exit_code = channel.recv_exit_status()

        if exit_code != 0:
            monit.fail()

        return exit_code


def execute(client: SSHClient, command: str, *, is_silent=True):
    with monit.section(f'Exec: {command}', is_silent=is_silent):
        stdin, stdout, stderr = client.exec_command(command)
        out = stdout.read().decode('utf-8').strip()
        err = stderr.read().decode('utf-8').strip()
        exit_code = stdout.channel.recv_exit_status()
        if err != '':
            logger.log("Errors:", Text.warning)
            print(err)

        if exit_code != 0:
            monit.fail()

        return exit_code, out


def template(file: Path, replace: Dict[str, str]):
    with open(str(file), 'r') as f:
        content = f.read()
        for k, v in replace.items():
            content = content.replace(f'%%{k.upper()}%%', v)

    return content


def run_script(client: SSHClient, script: str, script_name: str, home_path: str):
    conf = Configs.get()
    scripts_path = Path('./.remote/scripts')
    if not scripts_path.exists():
        scripts_path.mkdir()

    script_file = scripts_path / f'{script_name}.sh'
    with open(str(script_file), 'w') as f:
        f.write(script)

    os.chmod(str(script_file), stat.S_IRWXU | stat.S_IRWXG)
    scp = SCPClient(client.get_transport())
    scp.put(str(script_file), f'{home_path}/{conf.name}/.remote-scripts/{script_name}.sh')

    return execute_stream(client, f'{home_path}/{conf.name}/.remote-scripts/{script_name}.sh')


def setup_server(client: SSHClient, home_path: str):
    conf = Configs.get()

    has_folder, _ = execute(client, f'test -d {conf.name}')
    if has_folder != 0:
        print(has_folder)
        execute(client, f'mkdir {conf.name}')
    has_folder, _ = execute(client, f'test -d {conf.name}/.remote-scripts')
    if has_folder != 0:
        execute(client, f'mkdir {conf.name}/.remote-scripts')

    python_version = f'{sys.version_info.major}.{sys.version_info.minor}'

    script = template(conf.scripts_folder / 'setup.sh', {
        'name': conf.name,
        'python_version': python_version,
        'home': home_path
    })

    return run_script(client, script, 'setup', home_path)


def rsync_project():
    conf = Configs.get()

    exclude_path = Path('.') / '.remote' / 'exclude.txt'
    exclude_path = exclude_path.absolute()
    rsync_cmd = ['rsync', '-ravuKLt', '--perms', '--executability']
    if conf.password is not None or conf.private_key_file is None:
        raise NotImplementedError('TODO: Not implemented to handle connections with password')
    rsync_cmd += ['-e']
    rsync_cmd += [f'"ssh -o StrictHostKeyChecking=no -i {conf.private_key_file}"']
    if exclude_path.exists():
        rsync_cmd += [f"--exclude-from='{str(exclude_path)}'"]
    rsync_cmd += ['./']  # source
    rsync_cmd += [f'{conf.username}@{conf.hostname}:~/{conf.name}/']  # destination

    # print(' '.join(rsync_cmd))
    try:
        process = subprocess.run(' '.join(rsync_cmd), shell=True)
    except FileNotFoundError as e:
        logger.log('rsync not found', Text.danger)
        print(e)
        return 1

    return process.returncode


def update_packages(client: SSHClient, home_path: str):
    conf = Configs.get()

    pipfile = Path('.') / 'Pipfile'
    requirements = Path('.') / 'requirements.txt'

    script = template(conf.scripts_folder / 'update.sh', {
        'name': conf.name,
        'home': home_path,
        'has_pipfile': str(pipfile.exists()),
        'has_requirements': str(requirements.exists())
    })

    return run_script(client, script, 'update', home_path)


def run_command(client: SSHClient, home_path: str, command: List[str]):
    conf = Configs.get()

    pipfile = Path('.') / 'Pipfile'
    requirements = Path('.') / 'requirements.txt'

    script = template(conf.scripts_folder / 'run.sh', {
        'name': conf.name,
        'home': home_path,
        'has_pipfile': str(pipfile.exists()),
        'has_requirements': str(requirements.exists()),
        'run_command': ' '.join(command)
    })

    return run_script(client, script, 'run', home_path)
