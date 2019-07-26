import textwrap
from typing import Tuple

import pytest

from samples_validator import errors
from samples_validator.base import SystemCmdResult, Language


def test_curl_404(run_sys_cmd, runner_sample_factory):
    runner, sample = runner_sample_factory(Language.shell)
    stdout = textwrap.dedent("""
    HTTP/1.1 404 Not Found
    Content-Type: application/json
    Content-Length: 61
    Strict-Transport-Security: max-age=31536000; includeSubDomains; preload;
    
    {"error": {"status": 404, "message": "Not found: '/status'"}}
    """)
    run_sys_cmd.return_value = SystemCmdResult(
        exit_code=0, stdout=stdout, stderr=''
    )
    test_result = runner.run_sample(sample)
    assert not test_result.passed
    assert test_result.status_code == 404
    assert test_result.json_body == {
        "error": {"status": 404, "message": "Not found: '/status'"}
    }


def test_curl_200(run_sys_cmd, runner_sample_factory):
    runner, sample = runner_sample_factory(Language.shell)
    stdout = textwrap.dedent("""
    HTTP/1.1 200 OK
    Content-Type: application/json
    Content-Length: 2
    Strict-Transport-Security: max-age=31536000; includeSubDomains; preload;
    
    {}
    """)
    run_sys_cmd.return_value = SystemCmdResult(
        exit_code=0, stdout=stdout, stderr=''
    )
    test_result = runner.run_sample(sample)
    assert test_result.passed
    assert test_result.status_code == 200
    assert test_result.json_body == {}


def test_curl_200_rn_rn(run_sys_cmd, runner_sample_factory):
    runner, sample = runner_sample_factory(Language.shell)
    stdout = textwrap.dedent("""
    HTTP/1.1 200 OK
    Content-Type: application/json
    Content-Length: 2
    Strict-Transport-Security: max-age=31536000; includeSubDomains; preload;\r
    \r
    {}
    """)
    run_sys_cmd.return_value = SystemCmdResult(
        exit_code=0, stdout=stdout, stderr=''
    )
    test_result = runner.run_sample(sample)
    assert test_result.passed
    assert test_result.status_code == 200
    assert test_result.json_body == {}


def test_curl_not_json(run_sys_cmd, runner_sample_factory):
    runner, sample = runner_sample_factory(Language.shell)
    stdout = textwrap.dedent("""
    HTTP/1.0 400 Bad request
    Cache-Control: no-cache
    Connection: close
    Content-Type: text/html
    
    <html><body><h1>400 Bad request</h1>
    Your browser sent an invalid request.
    </body></html>
    """)
    run_sys_cmd.return_value = SystemCmdResult(
        exit_code=0, stdout=stdout, stderr=''
    )
    test_result = runner.run_sample(sample)
    assert not test_result.passed
    assert test_result.status_code is None
    assert test_result.json_body is None
    assert test_result.reason == errors.OutputParsingError


def test_curl_204_response(run_sys_cmd, runner_sample_factory):
    runner, sample = runner_sample_factory(Language.shell)
    stdout = """
    HTTP/1.1 204 No Content
    Content-Length: 2
    Strict-Transport-Security: max-age=31536000; includeSubDomains; preload;
    
    
    """
    run_sys_cmd.return_value = SystemCmdResult(
        exit_code=0, stdout=stdout, stderr=''
    )
    test_result = runner.run_sample(sample)
    assert test_result.passed
    assert test_result.status_code == 204
    assert test_result.json_body is None


def test_curl_non_valid_stdout(run_sys_cmd, runner_sample_factory):
    runner, sample = runner_sample_factory(Language.shell)
    run_sys_cmd.return_value = SystemCmdResult(
        exit_code=0, stdout='', stderr=''
    )
    test_result = runner.run_sample(sample)
    assert not test_result.passed
    assert test_result.status_code is None
    assert test_result.json_body is None
    assert test_result.reason == errors.OutputParsingError


_json_resp_200 = {
    Language.python: '{"raw_body": {"status": "ok"}, "code": 200}',
    Language.js: '{"raw_body": "{\\"status\\": \\"ok\\"}", "code": 200}',
}
_json_resp_200_rv = ({'status': 'ok'}, 200)
_json_resp_empty_dict = {
    Language.python: '{"raw_body": {}, "code": 201}',
    Language.js: '{"raw_body": "{}", "code": 201}',
}
_json_resp_empty_dict_rv: Tuple[dict, int] = ({}, 201)


@pytest.mark.parametrize('lang', [Language.js, Language.python])
@pytest.mark.parametrize('stdout, expected', [
    (_json_resp_200, _json_resp_200_rv),
    (_json_resp_empty_dict, _json_resp_empty_dict_rv)
])
def test_valid_json_parsing(lang, stdout, expected, run_sys_cmd,
                            runner_sample_factory):
    runner, sample = runner_sample_factory(lang)

    run_sys_cmd.return_value = SystemCmdResult(
        exit_code=0, stdout=stdout[lang], stderr=''
    )
    json_body, status_code = expected
    test_result = runner.run_sample(sample)
    assert test_result.passed
    assert test_result.json_body == json_body
    assert test_result.status_code == status_code


_json_missing_keys = '{"code": {}}'
_json_empty = '{}'
_json_corrupted = ''


@pytest.mark.parametrize('lang', [Language.js, Language.python])
@pytest.mark.parametrize('stdout, expected_err', [
    (_json_missing_keys, errors.ConformToSchemaError),
    (_json_empty, errors.ConformToSchemaError),
    (_json_corrupted, errors.OutputParsingError),
])
def test_invalid_json_parsing(lang, stdout, expected_err, run_sys_cmd,
                              runner_sample_factory):
    runner, sample = runner_sample_factory(lang)
    run_sys_cmd.return_value = SystemCmdResult(
        exit_code=0, stdout=stdout, stderr=''
    )
    test_result = runner.run_sample(sample)
    assert not test_result.passed
    assert test_result.reason == expected_err


def test_python_single_quoted_json_load(run_sys_cmd, runner_sample_factory):
    runner, sample = runner_sample_factory(Language.python)
    stdout = "{'raw_body': {}, 'code': 200}"
    run_sys_cmd.return_value = SystemCmdResult(
        exit_code=0, stdout=stdout, stderr=''
    )
    test_result = runner.run_sample(sample)
    assert test_result.passed
    assert test_result.status_code == 200
