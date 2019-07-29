from unittest.mock import MagicMock

import pytest

from samples_validator import errors
from samples_validator.base import SystemCmdResult, ALL_LANGUAGES, Language, \
    HttpMethod, ApiTestResult
from samples_validator.conf import conf
from samples_validator.loader import load_code_samples
from samples_validator.session import TestSession, TestExecutionResultMap


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


@pytest.mark.parametrize('status_codes,expected_failures', [
    ([200, 200], 0), ([500, 500], 2), ([200, 500], 1),
])
def test_test_session_return_value(
        status_codes, expected_failures,
        runner_sample_factory, run_sys_cmd, mocked_parse_stdout, reporter,
        temp_files_factory):
    root_dir = temp_files_factory([
        'api/user/POST/curl', 'api/user/GET/curl'
    ])
    session = TestSession(load_code_samples(root_dir))
    mocked_parse_stdout.side_effect = [({}, code) for code in status_codes]
    failed_count = session.run()
    assert failed_count == expected_failures


def test_reusing_response_from_prev_requests(
        run_sys_cmd, mocked_parse_stdout, temp_files_factory, reporter,
        no_cleanup):
    root_dir = temp_files_factory([
        'api/user/POST/curl',
        'api/user/{id}/GET/curl'
    ])
    samples = load_code_samples(root_dir)
    assert samples[-1].http_method == HttpMethod.get

    mocked_parse_stdout.return_value = ({'id': 1}, 200)
    original_source_code = 'curl website/api/user/{id}'
    expected_source_code = 'curl website/api/user/1'
    samples[-1].path.write_text(original_source_code)

    session = TestSession(samples)
    session.run()
    actual_code = session.runners[Language.shell].tmp_sample_path.read_text()
    assert actual_code == expected_source_code


def test_save_and_load_test_result_to_map(temp_files_factory):
    root_dir = temp_files_factory([
        'api/user/POST/curl',
        'api/user/{id}/GET/curl',
        'api/user/{id}/friend/POST/curl',
        'api/user/{id}/friend/{fid}/GET/curl',
    ])
    samples = load_code_samples(root_dir)
    parent_sample = samples[0]
    child_sample = samples[1]
    child_sample_post = samples[2]
    grand_child_sample = samples[3]

    result_map = TestExecutionResultMap()

    result_map.put(ApiTestResult(parent_sample, passed=True, json_body={1: 2}))
    result_map.put(ApiTestResult(child_sample, passed=True))
    result_map.put(
        ApiTestResult(child_sample_post, passed=True, json_body={3: 4})
    )

    assert result_map.get_parent_result(parent_sample) is None
    assert result_map.get_parent_result(child_sample).sample == parent_sample

    assert result_map.get_parent_body(parent_sample) == {}
    assert result_map.get_parent_body(child_sample) == {1: 2}

    assert result_map.get_parent_body(grand_child_sample) == {1: 2, 3: 4}


def test_reusing_response_from_prev_requests_with_replacements(
        run_sys_cmd, mocked_parse_stdout, temp_files_factory, reporter,
        no_cleanup, monkeypatch):
    root_dir = temp_files_factory([
        'api/user/POST/curl',
        'api/user/{id}/GET/curl'
    ])
    samples = load_code_samples(root_dir)
    assert samples[-1].http_method == HttpMethod.get

    mocked_parse_stdout.return_value = ({'@id': 1}, 200)
    conf.resp_attr_replacements = {'api/user': [{'@id': 'id'}]}
    original_source_code = 'curl website/api/user/{id}'
    expected_source_code = 'curl website/api/user/1'
    samples[-1].path.write_text(original_source_code)

    session = TestSession(samples)
    session.run()
    actual_code = session.runners[Language.shell].tmp_sample_path.read_text()
    assert actual_code == expected_source_code


def test_reusing_response_from_prev_requests_nested(
        run_sys_cmd, mocked_parse_stdout, temp_files_factory, reporter,
        no_cleanup, monkeypatch):
    root_dir = temp_files_factory([
        'api/users/POST/curl',
        'api/users/{from}/link/{to}/POST/curl',
        'api/users/{from}/link/{to}/{type}/GET/curl',
    ])
    samples = load_code_samples(root_dir)

    mocked_parse_stdout.side_effect = [
        ({'id': 'uuid'}, 200), ({}, 200), ({}, 200)
    ]
    conf.resp_attr_replacements = {
        'api/users': [{'id': 'from'}]
    }

    original_source_code = 'curl /users/{from}/link/{to}/{type}'
    expected_source_code = 'curl /users/uuid/link/{to}/{type}'
    samples[-1].path.write_text(original_source_code)

    session = TestSession(samples)
    session.run()
    actual_code = session.runners[Language.shell].tmp_sample_path.read_text()
    assert actual_code == expected_source_code


def test_before_sample_replacements(
        run_sys_cmd, mocked_parse_stdout, temp_files_factory, reporter,
        no_cleanup, monkeypatch):
    root_dir = temp_files_factory([
        'api/users/POST/curl',
    ])
    sample = load_code_samples(root_dir)[0]

    original_source_code = 'curl url --data {"name": "<username>"}'
    expected_source_code = 'curl url --data {"name": "John"}'
    sample.path.write_text(original_source_code)

    _post = MagicMock(status_code=200, json=lambda: {'@id': 'John'})
    monkeypatch.setattr(
        'samples_validator.prerequisites.base.requests', MagicMock(
            post=MagicMock(return_value=_post)
        )
    )
    mocked_parse_stdout.return_value = ({}, 200)

    conf.before_sample = {
        sample.name: {
            'resource': 'Identity',
            'subs': {'@id': '<username>'},
        }
    }

    session = TestSession([sample])
    session.run()
    actual_code = session.runners[Language.shell].tmp_sample_path.read_text()
    assert actual_code == expected_source_code


def test_before_sample_replacements_nested_path(
        run_sys_cmd, mocked_parse_stdout, temp_files_factory, reporter,
        no_cleanup, monkeypatch):
    root_dir = temp_files_factory([
        'api/users/{id}/link/POST/curl',
        'api/users/{id}/link/linkID/GET/curl',
    ])
    samples = load_code_samples(root_dir)

    original_source_code = 'curl api/users/{id}/link/linkID'
    expected_source_code = 'curl api/users/John/link/linkID'
    samples[-1].path.write_text(original_source_code)

    _post = MagicMock(status_code=200, json=lambda: {'@id': 'John'})
    monkeypatch.setattr(
        'samples_validator.prerequisites.base.requests', MagicMock(
            post=MagicMock(return_value=_post)
        )
    )
    mocked_parse_stdout.return_value = ({'stub': 'data'}, 200)

    conf.before_sample = {
        samples[0].name: {
            'resource': 'Identity',
            'subs': {'@id': 'id'},
        }
    }

    session = TestSession(samples)
    session.run()
    actual_code = session.runners[Language.shell].tmp_sample_path.read_text()
    assert actual_code == expected_source_code
