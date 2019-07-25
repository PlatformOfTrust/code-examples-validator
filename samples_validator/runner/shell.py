import json
import re
import tempfile
from pathlib import Path
from typing import Dict, Optional

from samples_validator import errors
from samples_validator.base import run_shell_command
from .base import CodeRunner


class CurlRunner(CodeRunner):

    def prepare_sample(
            self,
            path: Path,
            substitutions: Optional[Dict[str, str]] = None) -> Path:
        tmp_sample_path = Path(tempfile.gettempdir()) / 'curl'
        sample_code = path.read_text()
        prepared_code = self.replace_keywords(sample_code, substitutions)
        tmp_sample_path.write_text(prepared_code)
        return tmp_sample_path

    def _run_sample(self, sample_path: str):
        bash_bin = '/bin/bash'
        return run_shell_command([bash_bin, sample_path])

    def _parse_stdout(self, stdout: str):
        try:
            meta_info, body = stdout.strip().replace('\r', '').split('\n\n')
            match = re.match(r'HTTP.*? (?P<code>\d+) ', meta_info)
            if match:
                status_code = int(match.group('code'))
            else:
                raise ValueError('Could not match HTTP status code')
        except (IndexError, ValueError):
            raise errors.OutputParsingError
        try:
            json_body = json.loads(body)
        except json.JSONDecodeError:
            raise errors.OutputParsingError
        return json_body, status_code
