import os
import stat
from pathlib import Path
from typing import Optional, Dict

import paramiko
import yaml

_CONFIGS = None


class Configs:
    private_key_file: Optional[str]
    username: Optional[str]
    hostname: Optional[str]
    password: Optional[str]
    private_key: Optional[paramiko.RSAKey]

    def __init__(self, configs: Dict[str, any]):
        self.hostname = configs.get('hostname')
        self.username = configs.get('username', 'ubuntu')
        self.password = configs.get('password', None)
        self.private_key_file = configs.get('private_key', None)
        if self.private_key_file is not None:
            os.chmod(str(self.private_key_file), stat.S_IRUSR | stat.S_IWUSR)
            self.private_key = paramiko.RSAKey.from_private_key_file(self.private_key_file)
        else:
            self.private_key = None
        self.name = configs.get('name', Path('..').parent.absolute().name)

        self.scripts_folder = Path(__file__).absolute().parent / 'scripts'

    @staticmethod
    def _create(path: str = '.remote/configs.yaml'):
        with open(path, 'r') as f:
            return Configs(yaml.load(f.read(), yaml.FullLoader))

    @staticmethod
    def get():
        global _CONFIGS
        if _CONFIGS is None:
            _CONFIGS = Configs._create()
        return _CONFIGS
