from typing import List

from loguru import logger

from samples_validator import errors
from samples_validator.base import ApiTestResult, CodeSample, Language


def debug(message: str):
    logger.debug(message)


def log(message: str):
    logger.log('regular', message)  # TODO: move to consts


def log_red(message: str):
    logger.log('red', message)


def log_green(message: str):
    logger.log('green', message)


class Reporter:

    @staticmethod
    def _explain_non_zero_code(test_result: ApiTestResult):
        if not test_result.cmd_result:
            return
        code = test_result.cmd_result.exit_code
        stdout = test_result.cmd_result.stdout
        stderr = test_result.cmd_result.stderr
        stdout_desc = f'STDOUT:\n{stdout}' if stdout else 'NO STDOUT'
        stderr_desc = f'STDERR:\n{stderr}' if stderr else 'NO STDERR'
        log(
            f'Command returned non-zero exit code: {code}\n'
            f'{stdout_desc}\n{stderr_desc}',
        )

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
    def _explain_bad_request(test_result: ApiTestResult):
        log('Bad request')

    @staticmethod
    def _explain_timeout_error(test_result: ApiTestResult):
        log('Timeout error')

    def _explain_in_details(self, test_result: ApiTestResult):
        if test_result.passed:
            return
        describe_reason = {
            errors.NonZeroExitCode: self._explain_non_zero_code,
            errors.OutputParsingError: self._explain_stdout_parsing,
            errors.BadRequest: self._explain_bad_request,
            errors.ExecutionTimeout: self._explain_timeout_error,
        }.get(test_result.reason)
        if describe_reason is None:
            logger.info(f'Unknown reason for {test_result}')
            return
        log(f'======= Test: {test_result.sample.name} =======')
        log(f'Path: {test_result.sample.path.as_posix()}')
        log(f'Method: {test_result.sample.http_method.value}')
        describe_reason(test_result)
        log('')

    @staticmethod
    def show_short_test_status(test_result: ApiTestResult):
        if test_result.passed:
            log_green(' [PASSED]')
        else:
            log_red(' [FAILED]')

    def print_test_session_report(self, test_results: List[ApiTestResult]):
        passed_count = 0
        failed_count = 0
        log_fn = log_green
        log('')
        for test_result in test_results:
            if test_result.passed:
                passed_count += 1
            else:
                failed_count += 1
                log_fn = log_red
                self._explain_in_details(test_result)
        if failed_count:
            conclusion = 'Test session failed'
        else:
            conclusion = 'Test session passed'
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
        log('{:>6}: {}'.format(sample.http_method.value, sample.name))