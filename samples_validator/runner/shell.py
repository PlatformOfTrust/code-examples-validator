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
        status_code = None
        try:
            match = re.match(r'HTTP.*? (?P<code>\d+) ', stdout.strip())
            if match:
                status_code = int(match.group('code'))
            meta_info, body = stdout.strip().replace('\r', '').split('\n\n')
        except (IndexError, ValueError):
            if status_code == 204:
                return None, status_code
            raise errors.OutputParsingError
        try:
            json_body = json.loads(body)
        except json.JSONDecodeError:
            raise errors.OutputParsingError
        return json_body, status_code
