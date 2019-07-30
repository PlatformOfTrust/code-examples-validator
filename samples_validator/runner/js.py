import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Optional

from samples_validator import errors
from samples_validator.base import run_shell_command
from samples_validator.conf import conf
from samples_validator.reporter import debug
from .base import CodeRunner


class NodeRunner(CodeRunner):

    def __init__(self):
        super().__init__()
        tmp_path = Path(tempfile.gettempdir())
        self._project_dir_path = tmp_path / conf.js_project_dir_name
        self._node_modules_path = self._project_dir_path / 'node_modules'
        self._install_node_modules_if_needed()

    def prepare_sample(
            self,
            path: Path,
            substitutions: Optional[Dict[str, str]] = None) -> Path:
        tmp_sample_path: Path = self._project_dir_path / 'sample.js'
        sample_code = path.read_text()
        prepared_code = self.replace_keywords(sample_code, substitutions)
        tmp_sample_path.write_text(prepared_code)
        return tmp_sample_path

    def _install_node_modules_if_needed(self):
        packages = ['unirest']
        if conf.always_create_environments and self._project_dir_path.exists():
            debug(f'Removing {self._project_dir_path}')
            shutil.rmtree(self._project_dir_path.as_posix())
        if not self._project_dir_path.exists():
            os.makedirs(self._project_dir_path.as_posix())
            debug(f'Installing node modules to {self._project_dir_path}')
            run_shell_command(
                ['npm', 'install', ' '.join(packages)],
                timeout=conf.virtualenv_creation_timeout,
                cwd=self._project_dir_path,
            )

    def _run_sample(self, sample_path: str):
        if self.tmp_sample_path is None:
            raise ValueError('Temporary sample was not created')
        node_bin = 'node'
        return run_shell_command(
            [node_bin, sample_path],
            cwd=self._project_dir_path,
        )

    def _parse_stdout(self, stdout: str):
        try:
            raw_result = json.loads(stdout.strip(), encoding='utf8')
            status_code = raw_result['code']
            if status_code == 204:
                return None, status_code
            elif isinstance(raw_result['raw_body'], dict):
                return raw_result['raw_body'], status_code
            else:
                return json.loads(raw_result['raw_body']), status_code
        except json.JSONDecodeError:
            raise errors.OutputParsingError
        except KeyError:
            raise errors.ConformToSchemaError
