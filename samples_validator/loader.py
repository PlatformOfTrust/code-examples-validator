from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from samples_validator.base import CodeSample, HttpMethod, Language


def load_code_samples(
        root: Path,
        languages: Optional[List[Language]] = None) -> List[CodeSample]:
    if languages is None:
        languages = [Language.js, Language.python, Language.shell]
    samples = []
    valid_extensions = ('.js', '.py', 'curl')
    for file_path in root.glob('**/*'):
        if str(file_path).endswith(valid_extensions):
            http_method = HttpMethod(file_path.parent.name.upper())
            name = file_path.relative_to(root).parent.parent.as_posix()
            sample = CodeSample(
                file_path,
                http_method=http_method,
                name=name,
            )
            if sample.lang in languages:
                samples.append(sample)

    return sort_code_samples(samples)


def sort_code_samples(samples: List[CodeSample]) -> List[CodeSample]:
    scheme = Dict[str, Dict[HttpMethod, CodeSample]]
    endpoints_by_lang: scheme = defaultdict(dict)
    sorted_samples = []
    correct_order = (
        HttpMethod.post, HttpMethod.get, HttpMethod.put, HttpMethod.delete,
    )
    for sample in samples:
        key = sample.path.parent.parent
        endpoints_by_lang[f'{sample.lang}{key}'][sample.http_method] = sample

    for sample_by_method in endpoints_by_lang.values():
        for method in correct_order:
            if sample_by_method.get(method):
                sorted_samples.append(sample_by_method[method])
    return sorted_samples
