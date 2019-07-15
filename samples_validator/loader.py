import os
from collections import defaultdict
from pathlib import Path
from typing import List, Optional

from samples_validator.base import CodeSample, HttpMethod, Language


def get_http_method_from_path(path: Path) -> HttpMethod:
    return HttpMethod(path.parent.name.upper())


def make_sample_name_from_path(path: Path) -> str:
    str_path = str(path.parent.parent)
    path_parts = str_path.split(os.sep)

    # a_{x_y}_b -> a/{x_y}/b
    inside_placeholder = False
    endpoint = ''
    for char in path_parts[-1]:
        if char == '_' and not inside_placeholder:
            endpoint += '/'
            continue
        if char == '{':
            inside_placeholder = True
        elif char == '}':
            inside_placeholder = False
        endpoint += char

    parents = os.sep.join(
        name for name in path_parts[:-1] if not name.endswith('raml')
    )
    return parents + endpoint


def load_code_samples(
        root: Path,
        languages: Optional[List[Language]] = None) -> List[CodeSample]:
    if languages is None:
        languages = [Language.js, Language.python, Language.shell]
    samples = []
    valid_extensions = ('.js', '.py', 'curl')
    for file_path in root.glob('**/*'):
        if str(file_path).endswith(valid_extensions):
            http_method = get_http_method_from_path(file_path)
            name = make_sample_name_from_path(file_path.relative_to(root))
            sample = CodeSample(
                file_path,
                http_method=http_method,
                name=name,
            )
            if sample.lang in languages:
                samples.append(sample)

    return sort_code_samples(samples)


def sort_code_samples(samples: List[CodeSample]) -> List[CodeSample]:
    endpoints_tree: dict = {}
    for sample in samples:
        place_deeply(
            endpoints_tree,
            f'{sample.lang.value}/{sample.name}',
            sample,
        )
    result_list: List[CodeSample] = []
    load_samples_from_nested_dict(endpoints_tree, result_list)

    return result_list


def place_deeply(current_dict: dict,
                 path: str,
                 sample: CodeSample) -> dict:
    """
    Place code sample in the maximum nested structure based on its path

    :param current_dict: Dict on current nesting level
    :param path: Path of the sample relative to current nesting level
    :param sample: Code sample to put
    :return: Modified version of original dict containing the code sample

    For example, sample's path is 'a/b/c', then resulted dict will look like
    {'a': {'b': {'c': {'methods': {<HttpMethod.get: 'GET'>: CodeSample(..)}}}}}
    """

    separator = '/'
    path_parts = path.split(separator)
    current_path = path_parts[0]
    further_path = separator.join(path_parts[1:])

    if not current_dict.get(current_path):
        current_dict[current_path] = defaultdict(dict)

    if not further_path:
        current_dict[current_path]['methods'][sample.http_method] = sample
    else:
        current_dict[current_path] = place_deeply(
            current_dict[current_path], further_path, sample,
        )
    return current_dict


def load_samples_from_nested_dict(
        endpoints: dict,
        result_list: List[CodeSample]):
    """
    DFS implementation for loading code samples from nested structure
    created by place_deeply function. It takes into account child-parent
    relations and sorting HTTP methods in logical order, e.g create parent,
    create child, delete child, delete parent.

    :param endpoints: Result of place_deeply function
    :param result_list: List to put sorted samples into
    :return: None. This function is mutate the result_list argument
    """

    methods = endpoints.get('methods', {})
    for method in (HttpMethod.post, HttpMethod.get, HttpMethod.put):
        if method in methods:
            result_list.append(methods[method])

    further_paths = [name for name in endpoints.keys() if name != 'methods']
    deepest_level = not further_paths

    if not deepest_level:
        for value in further_paths:
            load_samples_from_nested_dict(endpoints[value], result_list)

    if HttpMethod.delete in methods:
        result_list.append(methods[HttpMethod.delete])
