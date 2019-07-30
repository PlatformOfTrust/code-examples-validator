import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional

from samples_validator.conf import conf


class Language(Enum):
    js = 'js'
    python = 'python'
    shell = 'shell'


class HttpMethod(Enum):
    get = 'GET'
    post = 'POST'
    put = 'PUT'
    delete = 'DELETE'


@dataclass
class CodeSample(object):
    path: Path
    name: str
    http_method: HttpMethod

    @property
    def lang(self) -> Language:
        filename = str(self.path)
        if filename.endswith('.js'):
            return Language.js
        elif filename.endswith('.py'):
            return Language.python
        elif filename.endswith(('.sh', 'curl')):
            return Language.shell
        raise ValueError(f'Unknown language provided: {filename}')


@dataclass
class SystemCmdResult:
    exit_code: int
    stdout: str
    stderr: str


@dataclass
class ApiTestResult(object):
    sample: CodeSample
    passed: bool
    status_code: Optional[int] = None
    cmd_result: Optional[SystemCmdResult] = None
    # be careful, this is not 1:1 mapping from response, it's mutable
    json_body: Optional[dict] = None
    reason: Any = None  # add typing
    source_code: Optional[str] = None
    duration: float = 0.0


def run_shell_command(
        args: List[str],
        timeout: int = None,
        cwd: Path = None) -> SystemCmdResult:
    from samples_validator import errors

    proc = subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd,
    )
    timeout = timeout or conf.sample_timeout
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        raise errors.ExecutionTimeout
    return SystemCmdResult(
        exit_code=proc.returncode,
        stdout=str(stdout, 'utf8'),
        stderr=str(stderr, 'utf8'),
    )


ALL_LANGUAGES = [Language.python, Language.js, Language.shell]
