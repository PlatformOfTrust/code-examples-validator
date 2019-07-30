from contextlib import contextmanager
from shutil import get_terminal_size
from typing import List

from loguru import logger

from samples_validator import errors
from samples_validator.base import ApiTestResult, CodeSample, Language
from samples_validator.conf import conf
from samples_validator.runner.base import APP_LOG_HANDLER


def debug(message: str):
    logger.debug(message)


@contextmanager
def patch_stream_handler_terminator(enabled=False):
    if enabled:
        APP_LOG_HANDLER.terminator = ''
    yield
    if enabled:
        APP_LOG_HANDLER.terminator = '\n'


def log(message: str, no_new_line: bool = False):
    with patch_stream_handler_terminator(no_new_line):
        logger.log('regular', message)  # TODO: move to consts


def log_red(message: str):
    logger.log('red', message)


def log_green(message: str):
    logger.log('green', message)


class Reporter:

    def _explain_non_zero_code(self, test_result: ApiTestResult):
        if not test_result.cmd_result:
            return
        code = test_result.cmd_result.exit_code
        log(f'Command returned non-zero exit code: {code}')
        self._print_stdout_and_stderr(test_result)

    @staticmethod
    def _explain_stdout_parsing(test_result: ApiTestResult):
        if not test_result.cmd_result:
            return
        stdout = test_result.cmd_result.stdout
        stderr = test_result.cmd_result.stderr
        if stdout.strip():
            log(f'Incorrect sample output:\n{stdout}')
        else:
            log('No stdout captured')
            if stderr:
                log(f'STDERR:\n{stderr}')

    @staticmethod
    def _print_stdout_and_stderr(test_result: ApiTestResult):
        if test_result.cmd_result:
            stdout = test_result.cmd_result.stdout.strip()
            stderr = test_result.cmd_result.stderr.strip()
            stdout_desc = f'STDOUT:\n{stdout}' if stdout else 'NO STDOUT'
            stderr_desc = f'STDERR:\n{stderr}' if stderr else 'NO STDERR'
        else:
            stdout_desc = 'NO STDOUT'
            stderr_desc = 'NO STDERR'
        log(f'{stdout_desc}\n{stderr_desc}')

    def _explain_bad_request(self, test_result: ApiTestResult):
        log(f'Bad request: {test_result.status_code}')
        self._print_stdout_and_stderr(test_result)

    @staticmethod
    def _explain_timeout_error(test_result: ApiTestResult):
        log(f'Timeout error: {conf.sample_timeout}s')

    @staticmethod
    def _print_sample_source_code(test_result: ApiTestResult):
        code = test_result.source_code
        log(f'Sample source code (with substitutions):\n{code}')

    @staticmethod
    def _explain_conforming_to_schema(test_result: ApiTestResult):
        if test_result.sample.lang in (Language.python, Language.js):
            log('Resulted JSON must contain "raw_body" and "code" fields')
        Reporter._explain_stdout_parsing(test_result)

    @staticmethod
    def _explain_unknown_reason(test_result: ApiTestResult):
        log('Unknown reason..')

    def _explain_in_details(self, test_result: ApiTestResult):
        if test_result.passed and not conf.debug:
            return
        error_reason = {
            errors.NonZeroExitCode: self._explain_non_zero_code,
            errors.OutputParsingError: self._explain_stdout_parsing,
            errors.BadRequest: self._explain_bad_request,
            errors.ExecutionTimeout: self._explain_timeout_error,
            errors.ConformToSchemaError: self._explain_conforming_to_schema,
        }.get(test_result.reason, self._explain_unknown_reason)

        divider = '=' * 20
        log(f'{divider} Test: {test_result.sample.name} {divider}')
        log(f'Path: {test_result.sample.path.as_posix()}')
        log(f'Method: {test_result.sample.http_method.value}')
        log('Duration: {:.1f}'.format(test_result.duration))
        if not test_result.passed:
            error_reason(test_result)
        if test_result.passed and conf.debug:
            self._print_stdout_and_stderr(test_result)
        self._print_sample_source_code(test_result)
        log('')

    @staticmethod
    def show_short_test_status(test_result: ApiTestResult):
        if test_result.passed:
            log_green('[PASSED]')
        else:
            log_red('[FAILED]')

    def print_test_session_report(self, test_results: List[ApiTestResult]):
        passed_count = 0
        failed_count = 0
        overall_time = 0.0
        log_fn = log_green
        log('')
        for test_result in test_results:
            overall_time += test_result.duration
            if test_result.passed:
                passed_count += 1
            else:
                failed_count += 1
                log_fn = log_red
            self._explain_in_details(test_result)
        if failed_count:
            conclusion = 'Test session failed'
            log('== List of failed tests ==')
            for test_result in test_results:
                if not test_result.passed:
                    log((
                        f'{test_result.sample.lang.value} - '
                        f'{test_result.sample.name} - '
                        f'{test_result.sample.http_method.value}'
                    ))
        else:
            conclusion = 'Test session passed'
        log('Time spent: {:.1f}s'.format(overall_time))
        description = '{} total, {} passed, {} failed'.format(
            len(test_results), passed_count, failed_count,
        )
        log_fn(f'== {conclusion} ==\n{description}')

    @staticmethod
    def show_language_scope_run(lang: Language):
        pretty_name = {
            Language.js: 'JavaScript',
            Language.python: 'Python',
            Language.shell: 'cURL',
        }
        log(f'======== {pretty_name[lang]} ========')

    @staticmethod
    def show_test_is_running(sample: CodeSample):
        message = '{:>6}: {}'.format(sample.http_method.value, sample.name)
        terminal_width = get_terminal_size((100, 20)).columns
        spaces = 2
        status_len = 8
        dots_count = terminal_width - len(message) - spaces - status_len
        dots = '.' * dots_count if dots_count > 0 else ''
        log(f'{message} {dots} ', no_new_line=True)
