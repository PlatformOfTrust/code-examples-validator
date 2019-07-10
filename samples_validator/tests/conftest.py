from pathlib import Path
from typing import List
from unittest.mock import MagicMock

import pytest

from samples_validator.base import CodeSample, HttpMethod, Language, \
    SystemCmdResult
from samples_validator.runner import CurlRunner, PythonRunner, NodeRunner, \
    CodeRunner


@pytest.fixture
def run_sys_cmd(monkeypatch):
    mocked_fn = MagicMock(return_value=SystemCmdResult(0, '', ''))
    monkeypatch.setattr('samples_validator.runner.run_shell_command', mocked_fn)
    return mocked_fn


@pytest.fixture
def curl_runner(run_sys_cmd):
    return CurlRunner()


@pytest.fixture
def node_runner(run_sys_cmd, monkeypatch):
    monkeypatch.setattr(
        'samples_validator.runner.NodeRunner._prepare_sample',
        MagicMock(return_value=Path('/tmp/sample.js'))
    )
    monkeypatch.setattr(
        'samples_validator.runner.NodeRunner._cleanup',
        MagicMock()
    )
    return NodeRunner()


@pytest.fixture
def python_runner(run_sys_cmd):
    return PythonRunner()


@pytest.fixture
def curl_sample():
    return CodeSample(
        path=Path('/tmp/sample.sh'),
        name='sample.sh',
        http_method=HttpMethod.get
    )


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
def runner_sample_factory(curl_runner, curl_sample, python_runner,
                          python_sample, js_sample, node_runner):
    def factory(lang: Language) -> (CodeRunner, CodeSample):
        if lang == Language.shell:
            return curl_runner, curl_sample
        elif lang == Language.python:
            return python_runner, python_sample
        elif lang == Language.js:
            return node_runner, js_sample
        raise ValueError('Unknown lang')

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
