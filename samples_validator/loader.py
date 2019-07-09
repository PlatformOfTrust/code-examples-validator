from pathlib import Path
from typing import List, Optional

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

    return samples


def sort_code_samples(samples: List[CodeSample]) -> List[CodeSample]:
    pass
