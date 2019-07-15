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
        ('api/u.raml/_users_v1_{from_id}/GET/curl',
         'api/users/v1/{from_id}'),
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


def test_parents_and_child_sorting_simple(temp_files_factory):
    root_dir = temp_files_factory([
        'api/_parent/POST/curl',
        'api/_parent_{id}/DELETE/curl',
        'api/_parent_{id}_child/POST/curl',
        'api/_parent_{id}_child_{childId}/DELETE/curl',
    ])
    samples = load_code_samples(root_dir)
    sorted_names = [(sample.name, sample.http_method) for sample in samples]
    assert sorted_names == [
        ('api/parent', HttpMethod.post),
        ('api/parent/{id}/child', HttpMethod.post),
        ('api/parent/{id}/child/{childId}', HttpMethod.delete),
        ('api/parent/{id}', HttpMethod.delete),
    ]


def test_parents_and_child_sorting_all_methods(temp_files_factory):
    files_structure = [
        ('api/_parent', ('GET', 'POST')),
        ('api/_parent_{id}', ('GET', 'PUT', 'DELETE')),
        ('api/_parent_{id}_child', ('GET', 'POST')),
        ('api/_parent_{id}_child_{childId}', ('GET', 'PUT', 'DELETE')),
    ]
    resources = []
    for prefix, methods in files_structure:
        for method in methods:
            resources.append(f'{prefix}/{method}/curl')

    samples = load_code_samples(temp_files_factory(resources))
    sorted_names = [(sample.name, sample.http_method) for sample in samples]
    assert sorted_names == [
        ('api/parent', HttpMethod.post),
        ('api/parent', HttpMethod.get),
        ('api/parent/{id}', HttpMethod.get),
        ('api/parent/{id}', HttpMethod.put),
        ('api/parent/{id}/child', HttpMethod.post),
        ('api/parent/{id}/child', HttpMethod.get),
        ('api/parent/{id}/child/{childId}', HttpMethod.get),
        ('api/parent/{id}/child/{childId}', HttpMethod.put),
        ('api/parent/{id}/child/{childId}', HttpMethod.delete),
        ('api/parent/{id}', HttpMethod.delete),
    ]
