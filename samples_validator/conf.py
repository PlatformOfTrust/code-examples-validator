import os
from pathlib import Path
from typing import Dict

import yaml
from pydantic import BaseModel


class Config(BaseModel):
    sample_timeout: int = 1
    virtualenv_creation_timeout: int = 120
    virtualenv_name: str = '.pot-svt-env'
    js_project_dir_name: str = '.pot-node'
    substitutions: Dict[str, str] = {}
    resp_attr_replacements: Dict[str, Dict[str, str]] = {}
    always_create_environments: bool = False
    debug: bool = False

    def reload(self, path: Path):
        new_conf = load_config(path)
        for name, value in new_conf:
            setattr(self, name, value)
        self._replace_env_vars()

    def __init__(self, **data):
        super().__init__(**data)
        self._replace_env_vars()

    def _replace_env_vars(self):
        if self.substitutions is None:
            return
        for key, value in self.substitutions.items():
            if value.startswith('$'):
                var_name = value[1:]
                real_value = os.environ.get(var_name)
                if real_value is not None:
                    self.substitutions[key] = real_value
                else:
                    raise ValueError(
                        f'Failed to find {var_name} in the environment')


def load_config(path: Path):
    conf_path = path.as_posix()
    try:
        with open(conf_path) as fd:
            conf_data = yaml.safe_load(fd) or {}
    except FileNotFoundError:
        raise ValueError(f'Config file is missing: {conf_path}')

    return Config(**conf_data)


conf = load_config(Path(__file__).absolute().parent.parent / 'conf.yaml')
