from typing import Dict, List

from samples_validator.base import ApiTestResult, CodeSample, Language
from samples_validator.conf import conf
from samples_validator.prerequisites.base import ResourceRegistry
from samples_validator.reporter import Reporter
from samples_validator.runner import CurlRunner, NodeRunner, PythonRunner
from samples_validator.utils import TestExecutionResultMap


class TestSession:

    def __init__(self, samples: List[CodeSample]):
        self.runners = {
            Language.js: NodeRunner(),
            Language.python: PythonRunner(),
            Language.shell: CurlRunner(),
        }
        self.samples = samples
        self._test_results_map = TestExecutionResultMap()
        self._resource_registry = ResourceRegistry()

    def run(self) -> int:
        reporter = Reporter()
        samples_by_lang: Dict[Language, List[CodeSample]] = {
            Language.js: [],
            Language.python: [],
            Language.shell: [],
        }
        results: List[ApiTestResult] = []
        for sample in self.samples:
            samples_by_lang[sample.lang].append(sample)

        for lang in Language:
            results.extend(
                self.run_api_tests_for_lang(samples_by_lang[lang], lang),
            )

        reporter.print_test_session_report(results)
        failed_count = sum(1 for res in results if not res.passed)
        return failed_count

    def run_api_tests_for_lang(self, samples: List[CodeSample], lang: Language):
        reporter = Reporter()
        reporter.show_language_scope_run(lang)
        test_results = []

        for sample in samples:
            prerequisite_subs: Dict[str, dict] = {}
            if sample.name in conf.before_sample:
                params = conf.before_sample[sample.name]
                if params['method'] == sample.http_method.value:
                    prerequisite_subs = self._resource_registry.create(
                        params['resource'], params['subs'],
                    )
            substitutions = self._test_results_map.get_parent_body(sample)
            substitutions.update(prerequisite_subs)
            reporter.show_test_is_running(sample)
            test_result = self.runners[lang].run_sample(
                sample, substitutions,
            )
            self._test_results_map.put(
                test_result,
                replace_keys=conf.resp_attr_replacements.get(sample.name, {}),
                extra=prerequisite_subs,
            )
            test_results.append(test_result)
            reporter.show_short_test_status(test_result)
        self._resource_registry.cleanup()
        return test_results
