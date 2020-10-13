import argparse
from pathlib import Path
from typing import List

import yaml
from labml import monit, logger
from labml.logger import Text

from labml_remote import connect, execute, setup_server, rsync_project, update_packages, run_command


def fail(msg: str):
    logger.log(msg, Text.danger)
    logger.log("Please open an issue on https://github.com/lab-ml/remote with details")


def run(command: List[str]):
    client = connect()
    _, home_path = execute(client, 'pwd')

    with monit.section("Setup server"):
        logger.log()
        if setup_server(client, home_path) != 0:
            monit.fail()
            fail("Failed to setup server")
            return

    logger.log()
    with monit.section("RSync"):
        logger.log()
        if rsync_project() != 0:
            monit.fail()
            fail("Failed to run rsync")
            return

    logger.log()
    with monit.section("Update python packages"):
        logger.log()
        if update_packages(client, home_path) != 0:
            monit.fail()
            fail("Failed to update packages")
            return

    logger.log('\n\n' + '-' * 40 + '\n\n')

    with monit.section("Run command"):
        logger.log()
        if run_command(client, home_path, command) != 0:
            monit.fail()
            fail("Failed to run command")
            return


def init_project():
    dot_remote = Path('.') / '.remote'
    if not dot_remote.exists():
        with monit.section(f"Creating {dot_remote}"):
            dot_remote.mkdir()

    configs_file = dot_remote / 'configs.yaml'
    configs = {}
    if not configs_file.exists():
        with monit.section(f"Generating configurations"):
            logger.log()
            configs['name'] = input("Project name: ").strip()
            configs['hostname'] = input("Hostname or public ip of the remote computer: ").strip()
            configs['username'] = input("Username of the remote computer (ubuntu): ").strip()
            if configs['username'] == '':
                configs['username'] = 'ubuntu'
            configs['private_key'] = input("Path to the private key file (.remote/private_key): ").strip()
            if configs['private_key'] == '':
                configs['private_key'] = '.remote/private_key'

            with open(str(configs_file), 'w') as f:
                f.write(yaml.dump(configs, default_flow_style=False))

    exclude_file = dot_remote / 'exclude.txt'
    if not exclude_file.exists():
        with monit.section(f"Creating boilerplate exclude file"):
            with open(str(exclude_file), 'w') as f:
                f.write('\n'.join([
                    '.remote',
                    '.git',
                    '__pycache__',
                    '.ipynb_checkpoints',
                    'logs',
                    '.DS_Store',
                    '.*.swp',
                    '*.egg-info/',
                    '.idea'
                ]))

    logger.log(["We have created a standard configurations file and"
                " exclude list specifying files and folders that shouldn't be copied to server."
                " You can edit them at ",
                ('.remote/configs.yaml', Text.meta),
                ' and ',
                ('.remote/exclude.txt', Text.meta)])


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--init', action='store_true',
                            default=False,
                            help='Whether to initialize a the folder with a remote project configurations')

    arg_parser.add_argument('command', nargs='*')

    args = arg_parser.parse_args()

    if args.init:
        if args.command:
            logger.log(["Use --init only to initialize the project.\n",
                        "It should be called without any other arguments from your project folder:\n",
                        ("labml_remote --init\n\n", Text.meta),
                        "Visit https://github.com/lab-ml/remote for details"])

            return

        init_project()
        return

    if not args.command:
        logger.log(["You need to provide a command to run remotely. Example:\n",
                    ("labml_remote python hello_world.py\n\n", Text.meta),
                    "Visit https://github.com/lab-ml/remote for details"])
    else:
        run(args.command)


if __name__ == '__main__':
    main()
