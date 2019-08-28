import ast
from collections import defaultdict
from pathlib import Path
from typing import List, Optional

from samples_validator.base import ApiTestResult, CodeSample, HttpMethod


class TestExecutionResultMap:
    """
    Data structure for storing results of test runs for each code sample
    based on its HTTP resource path
    """

    def __init__(self):
        self._map = {}

    def put(self,
            test_result: ApiTestResult,
            replace_keys: Optional[List[dict]] = None,
            extra: Optional[dict] = None):
        replace_keys = replace_keys or []
        parent_body = test_result.json_body or {}
        for replacement in replace_keys:
            for key_from, key_to in replacement.items():
                if key_from in parent_body:
                    parent_body[key_to] = parent_body[key_from]
        parent_body.update(extra or {})
        self._put_test_result(
            self._map, test_result, path=test_result.sample.name,
        )

    def get_parent_result(self, sample: CodeSample) -> Optional[ApiTestResult]:
        return self._get_parent_test_result(
            self._map, sample, path=sample.name, current_body={},
        )

    def get_parent_body(
            self,
            sample: CodeSample,
            escaped: bool = False) -> dict:
        body: dict = {}
        self._get_parent_test_result(
            self._map, sample, path=sample.name, current_body=body,
        )
        if escaped:
            # we want to replace placeholders like "{data}",
            # not the pure strings like "data"
            body = {f'{{{k}}}': v for k, v in body.items()}
        return body

    def _put_test_result(
            self,
            current_dict: dict,
            test_result: ApiTestResult,
            path: str) -> dict:
        """
        Place test result in the maximum nested structure based on its path

        :param current_dict: Dict on current nesting level
        :param test_result: Result of running the code sample
        :param path: Path of the sample relative to current nesting level
        :return: Modified version of original dict containing the test_result

        For example, sample's path is 'a/b', then resulted dict will look like
        {'a': {'b': {'methods': {<HttpMethod.get: 'GET'>: ApiTestResult(..)}}}}
        """
        path_parts = path.split('/')
        current_path = path_parts[0]
        further_path = '/'.join(path_parts[1:])

        if not current_dict.get(current_path):
            current_dict[current_path] = defaultdict(dict)

        if not further_path:
            http_method = test_result.sample.http_method
            current_dict[current_path]['methods'][http_method] = test_result
        else:
            current_dict[current_path] = self._put_test_result(
                current_dict[current_path], test_result, further_path,
            )
        return current_dict

    def _get_parent_test_result(
            self,
            current_dict: dict,
            sample: CodeSample,
            path: str,
            current_body: dict,
            current_parent: Optional[ApiTestResult] = None,
    ) -> Optional[ApiTestResult]:
        """
        Get the result of POST sample of parent resource in REST terminology.
        For example, we have a result of POST /parent. So for the
        /parent/{id} we want to get the result of previous request, mainly
        for substitution of the `id` param in the future

        :param current_dict: Dict on current nesting level
        :param sample: "Child" code sample
        :param path: Path of the sample relative to current nesting level
        :param current_parent: Current result of a method
        :return: Test result if it's present in the structure
        """

        path_parts = path.split('/')
        current_path = path_parts[0]
        further_path = '/'.join(path_parts[1:])

        current_methods = current_dict.get('methods', {})
        current_parent = current_methods.get(HttpMethod.post, current_parent)
        next_dict = current_dict.get(current_path)
        if current_parent and current_parent.json_body:
            current_body.update(current_parent.json_body)
        if not next_dict:
            return current_parent

        if not further_path:
            return current_parent
        else:
            return self._get_parent_test_result(
                next_dict, sample, further_path, current_body, current_parent,
            )


class CodeSamplesTree:
    """
    Data structure for storing code samples in a tree form based on
    HTTP resource path
    """

    def __init__(self):
        self._tree = {}

    def put(self, sample: CodeSample):
        self._put_code_sample(
            self._tree, f'{sample.lang.value}{sample.name}', sample,
        )

    def list_sorted_samples(self) -> List[CodeSample]:
        sorted_samples: List[CodeSample] = []
        self._sort_samples(self._tree, sorted_samples)
        return sorted_samples

    def _put_code_sample(self,
                         current_dict: dict,
                         path: str,
                         sample: CodeSample) -> dict:
        """
        Place code sample in the maximum nested structure based on its path

        :param current_dict: Dict on current nesting level
        :param path: Path of the sample relative to current nesting level
        :param sample: Code sample to put
        :return: Modified version of original dict containing the code sample

        For example, sample's path is 'a/b', then resulted dict will look like
        {'a': {'b': {'methods': {<HttpMethod.get: 'GET'>: CodeSample(..)}}}}
        """

        path_parts = path.split('/')
        current_path = path_parts[0]
        further_path = '/'.join(path_parts[1:])

        if not current_dict.get(current_path):
            current_dict[current_path] = defaultdict(dict)

        if not further_path:
            current_dict[current_path]['methods'][sample.http_method] = sample
        else:
            current_dict[current_path] = self._put_code_sample(
                current_dict[current_path], further_path, sample,
            )
        return current_dict

    def _sort_samples(
            self,
            endpoints: dict,
            result_list: List[CodeSample]):
        """
        DFS implementation for loading code samples from nested structure
        created by _put_code_sample method. It takes into account child-parent
        relations and sorting HTTP methods in logical order, e.g create parent,
        create child, delete child, delete parent.

        :param endpoints: Result of _put_code_sample function
        :param result_list: List to put sorted samples into
        :return: None. This function is mutate the result_list argument
        """

        methods = endpoints.get('methods', {})
        for method in (HttpMethod.post, HttpMethod.get, HttpMethod.put):
            if method in methods:
                result_list.append(methods[method])

        further_paths = [
            name for name in endpoints.keys() if name != 'methods'
        ]
        deepest_level = not further_paths

        if not deepest_level:
            for value in further_paths:
                self._sort_samples(endpoints[value], result_list)

        if HttpMethod.delete in methods:
            result_list.append(methods[HttpMethod.delete])


def parse_edn_spec_file(path: Path) -> dict:
    """Find a possible API param examples in a debug .edn file.
    If the keyword has a 'type', 'example', and 'description' property
    then it's considered to be an API param.
    Example of entry in edn:
    `{:name {:description "Product", :type "string", :example "Whiskey"}}`
    It will be parsed to {"name": "Whiskey"}
    """
    import edn_format
    from edn_format import Keyword
    from edn_format.immutable_dict import ImmutableDict

    edn = edn_format.loads(path.read_text())
    edn_dump = {}

    def search(current_dict: dict):
        for key in current_dict.keys():
            data = current_dict[key]
            if not isinstance(data, ImmutableDict):
                continue
            param_type = data.get(Keyword('type'))
            param_example = data.get(Keyword('example'))
            param_description = data.get(Keyword('description'))
            if param_type and param_example:
                param_key = key.name.replace('?', '')
                if param_type == 'array':
                    param_value = ast.literal_eval(param_example)
                else:
                    param_value = str(param_example)
                edn_dump[param_key] = param_value
            elif param_type and param_description:
                param_key = key.name.replace('?', '')
                edn_dump[param_key] = 'STUB'
            else:
                search(current_dict[key])

    search(edn)
    return edn_dump
