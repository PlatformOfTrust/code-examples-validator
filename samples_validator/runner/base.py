import json
import os
import re
import sys
import time
from abc import abstractmethod
from logging import StreamHandler
from pathlib import Path
from typing import Dict, Optional, Tuple

from samples_validator import errors
from samples_validator.base import ApiTestResult, CodeSample, SystemCmdResult
from samples_validator.conf import conf
from samples_validator.utils import parse_edn_spec_file

APP_LOG_HANDLER = StreamHandler(sys.stdout)


class CodeRunner(object):

    def __init__(self):
        self.tmp_sample_path: Optional[Path] = None

    @abstractmethod
    def _run_sample(
            self,
            sample_path: str) -> SystemCmdResult:
        """Language-specific method which runs corresponding system command
        :returns Wrapper over system command result
        """

    @abstractmethod
    def _parse_stdout(self, stdout: str) -> Tuple[dict, int]:
        """Parse stdout of system command
        :returns JSON response of HTTP request and status code
        """

    @abstractmethod
    def prepare_sample(
            self,
            path: Path,
            substitutions: Optional[Dict[str, str]] = None) -> Path:
        """Sample preparation"""

    def _cleanup(self, sample: CodeSample):
        if (self.tmp_sample_path
                and self.tmp_sample_path.exists()
                and self.tmp_sample_path != sample.path):
            os.remove(self.tmp_sample_path.as_posix())

    def run_sample(
            self,
            sample: CodeSample,
            substitutions: Optional[Dict[str, str]] = None) -> ApiTestResult:
        _substitutions = self.get_substitutions_from_spec(sample)
        _substitutions.update(substitutions or {})
        self.tmp_sample_path = self.prepare_sample(sample.path, _substitutions)
        try:
            api_test_result = self.analyze_result(sample)
            api_test_result.source_code = self.tmp_sample_path.read_text()
            return api_test_result
        finally:
            self._cleanup(sample)

    def analyze_result(self, sample: CodeSample) -> ApiTestResult:
        start_time = time.time()
        try:
            cmd_result = self._run_sample(str(self.tmp_sample_path))
        except errors.ExecutionTimeout:
            return ApiTestResult(
                sample, passed=False, reason=errors.ExecutionTimeout,
                duration=conf.sample_timeout,
            )
        duration = time.time() - start_time

        if cmd_result.exit_code != 0:
            return ApiTestResult(
                sample, passed=False, reason=errors.NonZeroExitCode,
                cmd_result=cmd_result, duration=duration,
            )

        try:
            json_body, status_code = self._parse_stdout(cmd_result.stdout)
        except errors.OutputParsingError as exc:
            return ApiTestResult(
                sample, passed=False, reason=exc.__class__,
                cmd_result=cmd_result, duration=duration,
            )

        if status_code >= 400:
            return ApiTestResult(
                sample, passed=False, reason=errors.BadRequest,
                cmd_result=cmd_result, json_body=json_body,
                status_code=status_code, duration=duration,
            )

        return ApiTestResult(
            json_body=json_body,
            status_code=status_code,
            passed=True,
            reason=None,
            sample=sample,
            cmd_result=cmd_result,
            duration=duration,
        )

    @staticmethod
    def replace_keywords(
            text: str,
            subs: Optional[Dict[str, str]] = None) -> str:
        if subs is None:
            subs = conf.substitutions.copy() or {}
        else:
            subs.update(conf.substitutions or {})

        for replace_from, replace_to in subs.items():
            text = text.replace(replace_from, str(replace_to))
        return text

    @staticmethod
    def get_substitutions_from_spec(sample: CodeSample) -> dict:
        edn_path = sample.path.parent / 'debug.edn'
        source_code = sample.path.read_text()
        examples = parse_edn_spec_file(edn_path)
        substitutions = {}
        re_json_curl = r'\\"(\w+?)\\": ?\\"<(.+?)>\\"'
        re_arrays_curl = r'\\"(\w+?)\\": ?(\[.+?\])'
        re_json_py = r'"(\w+?)": ?"<(.+?)>"'
        re_arrays_py = r'"(\w+?)": ?(\[.+?\])'

        for name, param_value in re.findall(re_json_curl, source_code):
            if name in examples:
                substitutions[f'<{param_value}>'] = examples[name]
        for name, param_value in re.findall(re_arrays_curl, source_code):
            json_array = json.dumps(examples[name])
            escaped_json_array = json_array.replace('"', '\\"')
            substitutions[param_value] = escaped_json_array

        for name, param_value in re.findall(re_json_py, source_code):
            if name in examples:
                substitutions[f'<{param_value}>'] = examples[name]
        for name, param_value in re.findall(re_arrays_py, source_code):
            substitutions[param_value] = json.dumps(examples[name])

        return substitutions
