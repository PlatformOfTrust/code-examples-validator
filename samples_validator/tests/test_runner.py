import pytest

from samples_validator import errors
from samples_validator.base import SystemCmdResult, Language

ALL_LANGUAGES = [Language.python, Language.js, Language.shell]


@pytest.mark.parametrize('lang', ALL_LANGUAGES)
def test_non_zero_exit_code(lang, runner_sample_factory, run_sys_cmd):
    runner, sample = runner_sample_factory(lang)
    run_sys_cmd.return_value = SystemCmdResult(
        exit_code=1, stdout='', stderr=''
    )
    test_result = runner.run_sample(sample)
    assert not test_result.passed
    assert test_result.reason == errors.NonZeroExitCode


@pytest.mark.parametrize('lang', ALL_LANGUAGES)
def test_bad_request(lang, runner_sample_factory, run_sys_cmd,
                     mocked_parse_stdout):
    runner, sample = runner_sample_factory(lang)

    mocked_parse_stdout.return_value = ({}, 422)
    test_result = runner.run_sample(sample)
    assert not test_result.passed
    assert test_result.reason == errors.BadRequest
