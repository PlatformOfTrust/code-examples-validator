import json
import os
import re
import shutil
import tempfile
from abc import abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple

import virtualenv

from samples_validator import errors
from samples_validator.base import (
    ApiTestResult, CodeSample, Language, run_shell_command, SystemCmdResult,
)
from samples_validator.conf import conf
from samples_validator.loader import load_code_samples
from samples_validator.reporter import debug, Reporter


class CodeRunner(object):

    def __init__(self):
        self.tmp_sample_path: Optional[Path] = None

    @abstractmethod
    def _run_sample(
            self,
            sample: CodeSample) -> SystemCmdResult:
        """Language-specific method which runs corresponding system command
        :returns Wrapper over system command result
        """

    @abstractmethod
    def _parse_stdout(self, stdout: str) -> Tuple[dict, int]:
        """Parse stdout of system command
        :returns JSON response of HTTP request and status code
        """

    @abstractmethod
    def _prepare_sample(self, path: Path) -> Path:
        """Sample preparation"""

    def _cleanup(self, sample: CodeSample):
        if (self.tmp_sample_path
                and self.tmp_sample_path.exists()
                and self.tmp_sample_path != sample.path):
            os.remove(self.tmp_sample_path.as_posix())

    def run_sample(self, sample: CodeSample) -> ApiTestResult:
        self.tmp_sample_path = self._prepare_sample(sample.path)
        try:
            return self.analyze_result(sample)
        finally:
            self._cleanup(sample)

    def analyze_result(self, sample: CodeSample) -> ApiTestResult:
        try:
            cmd_result = self._run_sample(sample)
        except errors.ExecutionTimeout:
            return ApiTestResult(
                sample, passed=False, reason=errors.ExecutionTimeout,
            )

        if cmd_result.exit_code != 0:
            return ApiTestResult(
                sample, passed=False, reason=errors.NonZeroExitCode,
                cmd_result=cmd_result,
            )

        try:
            json_body, status_code = self._parse_stdout(cmd_result.stdout)
        except errors.OutputParsingError:
            return ApiTestResult(
                sample, passed=False, reason=errors.OutputParsingError,
                cmd_result=cmd_result,
            )

        if status_code >= 400:
            return ApiTestResult(
                sample, passed=False, reason=errors.BadRequest,
                cmd_result=cmd_result, json_body=json_body,
                status_code=status_code,
            )

        return ApiTestResult(
            json_body=json_body,
            status_code=status_code,
            passed=True,
            reason=None,
            sample=sample,
            cmd_result=cmd_result,
        )

    @staticmethod
    def _parse_json_like_stdout(stdout: str):
        try:
            raw_result = json.loads(stdout, encoding='utf8')
        except json.JSONDecodeError:
            raise errors.OutputParsingError
        try:
            return raw_result['raw_body'], raw_result['code']
        except KeyError:
            raise errors.OutputParsingError


class NodeRunner(CodeRunner):

    def __init__(self):
        super().__init__()
        tmp_path = Path(tempfile.gettempdir())
        self._project_dir_path = tmp_path / conf.js_project_dir_name
        self._node_modules_path = self._project_dir_path / 'node_modules'
        self._install_node_modules_if_needed()

    def _prepare_sample(self, path: Path) -> Path:
        tmp_sample_path: Path = self._project_dir_path / 'sample.js'
        shutil.copy(path.as_posix(), tmp_sample_path.as_posix())
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

    def _run_sample(self, sample: CodeSample):
        if self.tmp_sample_path is None:
            raise ValueError('Temporary sample was not created')
        node_bin = 'node'
        return run_shell_command(
            [node_bin, self.tmp_sample_path.as_posix()],
            cwd=self._project_dir_path,
        )

    def _parse_stdout(self, stdout: str):
        return self._parse_json_like_stdout(stdout.strip())


class PythonRunner(CodeRunner):

    def _prepare_sample(self, path: Path) -> Path:
        return path

    def __init__(self):
        super().__init__()
        tmp_path = Path(tempfile.gettempdir())
        self._virtualenv_path = tmp_path / conf.virtualenv_name
        self._python_path = self._virtualenv_path / 'bin' / 'python'
        self._create_virtualenv_if_needed()

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

    def _run_sample(self, sample: CodeSample):
        return run_shell_command([
            self._python_path.as_posix(), sample.path.as_posix(),
        ])

    def _parse_stdout(self, stdout: str):
        return self._parse_json_like_stdout(stdout.strip())


class CurlRunner(CodeRunner):

    def _prepare_sample(self, path: Path) -> Path:
        return path

    def _run_sample(self, sample: CodeSample):
        bash_bin = '/bin/bash'
        return run_shell_command([bash_bin, sample.path.as_posix()])

    def _parse_stdout(self, stdout: str):
        try:
            meta_info, body = stdout.strip().replace('\r', '').split('\n\n')
            match = re.match(r'HTTP.*? (?P<code>\d+) .*', meta_info)
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


class TestSession:

    def __init__(self, samples: List[CodeSample]):
        self.runners = {
            Language.js: NodeRunner(),
            Language.python: PythonRunner(),
            Language.shell: CurlRunner(),
        }
        self.samples = samples

    def run(self):
        reporter = Reporter()
        samples_by_lang = {
            Language.js: [],
            Language.python: [],
            Language.shell: [],
        }
        results = []
        for sample in self.samples:
            samples_by_lang[sample.lang].append(sample)

        for lang in Language:
            results.extend(
                self.run_api_tests_for_lang(samples_by_lang[lang], lang),
            )

        reporter.print_test_session_report(results)

    def run_api_tests_for_lang(self, samples: List[CodeSample], lang: Language):
        reporter = Reporter()
        reporter.show_language_scope_run(lang)
        test_results = []

        for sample in samples:
            reporter.show_test_is_running(sample)
            test_result = self.runners[lang].run_sample(sample)
            test_results.append(test_result)
            reporter.show_short_test_status(test_result)
        return test_results


def make_session_from_dir(path: Path) -> TestSession:
    all_samples = load_code_samples(path, [Language.js, Language.shell])
    return TestSession(all_samples)
