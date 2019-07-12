class SampleRuntimeError(Exception):
    pass


class OutputParsingError(SampleRuntimeError):
    pass


class NonZeroExitCode(SampleRuntimeError):
    pass


class UnexpectedResult(SampleRuntimeError):
    pass


class BadRequest(SampleRuntimeError):
    pass


class ExecutionTimeout(SampleRuntimeError):
    pass
