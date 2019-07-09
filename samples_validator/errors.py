from samples_validator.base import SystemCmdResult


class ValidationError(Exception):
    def __init__(self, *args, **kwargs):
        pass


def command_failed(cmd_result: SystemCmdResult) -> str:
    return (
        f'Command returned non-zero exit code: {cmd_result.exit_code}\n'
        f'STDOUT:\n{cmd_result.stdout}\n'
        f'STDERR:\n{cmd_result.stderr}\n'
    )


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
