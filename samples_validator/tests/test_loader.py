import pytest

from samples_validator.base import CodeSample, HttpMethod
from samples_validator.loader import load_code_samples


@pytest.mark.parametrize(
    'sample_filename', ['sample.js', 'sample.py', 'curl']
)
def test_base_loading(sample_filename, temp_files_factory, run_sys_cmd):
    root_dir = temp_files_factory([
        'api/POST/sample.js',
        'api/POST/sample.py',
        'api/POST/curl',
        'api/POST/trash'
    ])
    samples = load_code_samples(root_dir)
    assert len(samples) == 3
    sample = CodeSample(
        path=root_dir / f'api/POST/{sample_filename}',
        name='api',
        http_method=HttpMethod.post
    )
    assert sample in samples


@pytest.mark.parametrize(
    'sample_path,expected_name', [
        ('api/u.raml/_users_v1/GET/curl',
         'api/users/v1'),
        ('api/u.raml/_users_v1_{from}_link_{to}/GET/curl',
         'api/users/v1/{from}/link/{to}'),
        ('api/u.raml/_users_v1_{from}_link_{to}_{type}/GET/curl',
         'api/users/v1/{from}/link/{to}/{type}'),
    ])
def test_correct_name_is_loaded(sample_path, expected_name,
                                temp_files_factory, run_sys_cmd):
    root_dir = temp_files_factory([sample_path])
    samples = load_code_samples(root_dir)
    assert samples
    assert samples[0].name == expected_name


@pytest.mark.parametrize(
    'dir_name,expected_method', [
        ('POST', HttpMethod.post), ('GET', HttpMethod.get),
        ('DELETE', HttpMethod.delete), ('PUT', HttpMethod.put),
    ]
)
def test_http_methods_parsing(dir_name, expected_method,
                              temp_files_factory, run_sys_cmd):
    root_dir = temp_files_factory([f'api/{dir_name}/sample.js'])
    samples = load_code_samples(root_dir)
    assert samples
    assert samples[0].http_method == expected_method


def test_sorting_by_endpoint(temp_files_factory, run_sys_cmd):
    root_dir = temp_files_factory([
        f'api/endpoint/{method}/curl'
        for method in ('GET', 'POST', 'PUT', 'DELETE')
    ])
    samples = load_code_samples(root_dir)
    methods = [sample.http_method for sample in samples]
    assert methods == [
        HttpMethod.post, HttpMethod.get, HttpMethod.put, HttpMethod.delete
    ]
