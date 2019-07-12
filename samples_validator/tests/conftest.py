from pathlib import Path
from typing import List
from unittest.mock import MagicMock

import pytest

from samples_validator.base import CodeSample, HttpMethod, Language, \
    SystemCmdResult
from samples_validator.loader import load_code_samples
from samples_validator.runner import CurlRunner, PythonRunner, NodeRunner, \
    CodeRunner


@pytest.fixture
def run_sys_cmd(monkeypatch):
    mocked_fn = MagicMock(return_value=SystemCmdResult(0, '', ''))
    monkeypatch.setattr('samples_validator.runner.run_shell_command', mocked_fn)
    return mocked_fn


@pytest.fixture
def python_sample():
    return CodeSample(
        path=Path('/tmp/sample.py'),
        name='sample.py',
        http_method=HttpMethod.get
    )


@pytest.fixture
def js_sample():
    return CodeSample(
        path=Path('/tmp/sample.js'),
        name='sample.js',
        http_method=HttpMethod.get
    )


@pytest.fixture
def runner_sample_factory(temp_files_factory):
    def factory(lang: Language) -> (CodeRunner, CodeSample):
        if lang == Language.shell:
            runner = CurlRunner()
            name = 'curl'
        elif lang == Language.python:
            runner = PythonRunner()  # type: ignore
            name = 'sample.py'
        elif lang == Language.js:
            runner = NodeRunner()  # type: ignore
            name = 'sample.js'
        else:
            raise ValueError('Unknown language')
        root_dir = temp_files_factory([f'api/GET/{name}'])
        sample = load_code_samples(root_dir)[0]
        return runner, sample

    return factory


@pytest.fixture
def mocked_parse_stdout(monkeypatch):
    mocked_method = MagicMock()
    for name in ('NodeRunner', 'CurlRunner', 'PythonRunner'):
        monkeypatch.setattr(f'samples_validator.runner.{name}._parse_stdout',
                            mocked_method)
    return mocked_method


@pytest.fixture
def temp_files_factory(tmp_path):
    def factory(rel_paths: List[str]):
        for rel_path in rel_paths:
            dir_path = tmp_path / Path(rel_path).parent
            dir_path.mkdir(parents=True, exist_ok=True)
            tmp_path / Path(rel_path)
            f_path = tmp_path / rel_path
            f_path.touch()
        return tmp_path

    return factory
