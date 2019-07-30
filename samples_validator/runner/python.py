import ast
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Optional

import virtualenv

from samples_validator import errors
from samples_validator.base import run_shell_command
from samples_validator.conf import conf
from samples_validator.reporter import debug
from .base import CodeRunner


class PythonRunner(CodeRunner):

    def __init__(self):
        super().__init__()
        tmp_path = Path(tempfile.gettempdir())
        self._virtualenv_path = tmp_path / conf.virtualenv_name
        self._python_path = self._virtualenv_path / 'bin' / 'python'
        self._create_virtualenv_if_needed()

    def prepare_sample(
            self,
            path: Path,
            substitutions: Optional[Dict[str, str]] = None) -> Path:
        tmp_sample_path = Path(tempfile.gettempdir()) / 'sample.py'
        sample_code = path.read_text()
        prepared_code = self.replace_keywords(sample_code, substitutions)
        tmp_sample_path.write_text(prepared_code)
        return tmp_sample_path

    def _create_virtualenv_if_needed(self):
        if conf.always_create_environments and self._virtualenv_path.exists():
            debug(f'Removing virtualenv: {self._virtualenv_path}')
            shutil.rmtree(self._virtualenv_path.as_posix())
        if not self._python_path.exists():
            debug(f'Creating virtualenv: {self._virtualenv_path}')
            virtualenv.create_environment(self._virtualenv_path.as_posix())
            self._install_python_packages()

    def _install_python_packages(self):
        packages = ['requests']
        pip_path = self._virtualenv_path / 'bin' / 'pip'
        run_shell_command(
            [pip_path.as_posix(), 'install', ' '.join(packages)],
            timeout=conf.virtualenv_creation_timeout,
        )

    def _run_sample(self, sample_path: str):
        return run_shell_command([
            self._python_path.as_posix(), sample_path,
        ])

    def _parse_stdout(self, stdout: str):
        try:
            raw_result = ast.literal_eval(stdout.strip())
            status_code = raw_result['code']
            if status_code == 204:
                return None, status_code
        except (IndexError, KeyError):
            raise errors.ConformToSchemaError
        except (SyntaxError, ValueError):
            raise errors.OutputParsingError
        try:
            raw_body = raw_result['raw_body']
            if isinstance(raw_body, dict):
                return raw_result['raw_body'], status_code
            else:
                return json.loads(raw_body), status_code
        except (KeyError, json.JSONDecodeError):
            raise errors.ConformToSchemaError
