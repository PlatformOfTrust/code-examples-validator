import sys
from pathlib import Path

import click
from loguru import logger

from samples_validator.base import Language
from samples_validator.runner import make_session_from_dir


@click.command()
@click.option(
    '-s', '--samples-dir',
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help='Path to directory with samples',
)
@click.option(
    '-c', '--config',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help='Path to configuration file',
)
@click.option(
    '-l', '--lang',
    type=click.Choice(['python', 'js', 'shell']),
    help='Run samples only for that language. Run all of them by default',
)
def run_tests(samples_dir: str, config: str, lang: str):
    setup_logging()
    if config:
        from samples_validator.conf import conf
        conf.reload(Path(config))
    languages = [Language[lang]] if lang else None
    test_session = make_session_from_dir(Path(samples_dir), languages)
    failed_tests_count = test_session.run()
    sys.exit(failed_tests_count)


def setup_logging():
    logger.remove()
    logger.level('regular', no=100)
    logger.level('red', no=101, color='<red>')
    logger.level('green', no=102, color='<green>')
    logger.add(sys.stdout, colorize=True, format='<level>{message}</>',
               level='DEBUG')


if __name__ == '__main__':
    run_tests()
