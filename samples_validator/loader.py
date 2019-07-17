import os
from pathlib import Path
from typing import List, Optional

from samples_validator.base import CodeSample, HttpMethod, Language
from samples_validator.utils import CodeSamplesTree


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
    parents += ('/' if not endpoint.startswith('/') else '')
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
    samples_tree = CodeSamplesTree()
    for sample in samples:
        samples_tree.put(sample)
    return samples_tree.list_sorted_samples()
