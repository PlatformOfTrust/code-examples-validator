import pytest
from samples_validator.base import ALL_LANGUAGES
from samples_validator.conf import Config


@pytest.mark.parametrize('lang', ALL_LANGUAGES)
def test_substitutions_from_conf(lang, run_sys_cmd,
                                 monkeypatch, runner_sample_factory):
    runner, sample = runner_sample_factory(lang)
    sample.path.write_text('lib.get("url", token=<AUTH_TOKEN>)')
    monkeypatch.setattr(
        'samples_validator.runner.conf.substitutions',
        {'<AUTH_TOKEN>': '"Token"'}
    )
    tmp_sample = runner.prepare_sample(sample.path)
    edited_source_code = tmp_sample.read_text()
    assert edited_source_code == 'lib.get("url", token="Token")'


def test_env_var_substitutions_in_config(monkeypatch):
    with pytest.raises(ValueError):
        Config(substitutions={'<TOKEN>': '$TOKEN'})

    monkeypatch.setenv('TOKEN', 'xxx')
    config = Config(substitutions={'<TOKEN>': '$TOKEN'})
    assert config.substitutions == {'<TOKEN>': 'xxx'}

    config = Config(substitutions={'<TOKEN>': 'TOKEN'})
    assert config.substitutions == {'<TOKEN>': 'TOKEN'}
