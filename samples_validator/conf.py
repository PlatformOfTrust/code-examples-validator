from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseModel


class Config(BaseModel):
    sample_timeout: int
    virtualenv_creation_timeout: int = 120
    virtualenv_name: str = '.pot-svt-env'
    js_project_dir_name: str = '.pot-node'
    substitutions: Optional[Dict[str, str]] = None
    always_create_environments: bool = False

    def reload(self, path: Path):
        new_conf = load_config(path)
        for name, value in new_conf:
            setattr(self, name, value)


def load_config(path: Path):
    conf_path = path.as_posix()
    try:
        with open(conf_path) as fd:
            conf_data = yaml.safe_load(fd) or {}
    except FileNotFoundError:
        raise ValueError(f'Config file is missing: {conf_path}')

    return Config(**conf_data)


conf = load_config(Path(__file__).absolute().parent.parent / 'conf.yaml')
