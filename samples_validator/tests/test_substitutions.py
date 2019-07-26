import pytest
from samples_validator.base import ALL_LANGUAGES
from samples_validator.conf import Config
from samples_validator.tests.data import edn_examples as edn
from samples_validator.utils import parse_edn_spec_file


@pytest.mark.parametrize('lang', ALL_LANGUAGES)
def test_substitutions_from_conf(lang, run_sys_cmd,
                                 monkeypatch, runner_sample_factory):
    runner, sample = runner_sample_factory(lang)
    sample.path.write_text('lib.get("url", token=<AUTH_TOKEN>)')
    monkeypatch.setattr(
        f'samples_validator.runner.base.conf.substitutions',
        {'<AUTH_TOKEN>': '"Token"'}
    )
    tmp_sample = runner.prepare_sample(sample.path)
    edited_source_code = tmp_sample.read_text()
    assert edited_source_code == 'lib.get("url", token="Token")'


def test_env_var_substitutions_in_config(monkeypatch):
    conf = Config(substitutions={'<TOKEN>': '$TOKEN'})
    with pytest.raises(ValueError):
        assert conf.validate_environment()

    monkeypatch.setenv('TOKEN', 'xxx')
    config = Config(substitutions={'<TOKEN>': '$TOKEN'})
    assert config.substitutions == {'<TOKEN>': 'xxx'}

    config = Config(substitutions={'<TOKEN>': 'TOKEN'})
    assert config.substitutions == {'<TOKEN>': 'TOKEN'}


@pytest.mark.parametrize('lang', ALL_LANGUAGES)
def test_replace_keywords_method(lang, runner_sample_factory):
    runner, sample = runner_sample_factory(lang)
    replace = runner.replace_keywords
    assert replace('{version}', {'version': 'v1'}) == 'v1'
    assert replace('{version}', {'{version}': 'v1'}) == 'v1'
    assert replace('<TOKEN>', {'<TOKEN>': 'xxx'}) == 'xxx'
    assert replace('[{"a": "b"}]', {'[{"a": "b"}]': '[]'}) == '[]'


@pytest.mark.parametrize('edn_example', [
    edn.simple_param_curl, edn.array_param_curl, edn.simple_param_curl_py,
    edn.array_param_py,
])
def test_get_substitutions_from_spec_method(
        edn_example, runner_sample_factory, tmp_path):
    edn_data, expected_dict, source_code, expected_subs, lang = edn_example()
    runner, sample = runner_sample_factory(lang)
    sample.path.write_text(source_code)
    edn_file = sample.path.parent / 'debug.edn'  # TODO: move it to sample
    edn_file.write_text(edn_data)
    assert parse_edn_spec_file(edn_file) == expected_dict
    assert runner.get_substitutions_from_spec(sample) == expected_subs
