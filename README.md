## PoT code samples validation tool

### Installation
First of all you need to have python environment ready (3.6+)
1) Install [poetry][poetry-install]
as a dependency management tool
2) Run `poetry install`

Note: if you have some troubles with poetry and python versions you can always
work in virtual environment to avoid any mess:
```bash
pip install virtualenv
python -m virtualenv .venv
. .venv/bin/activate
``` 

### Usage
Execute `poetry run samples-validator --help` to print the help message:
```bash
Usage: samples-validator [OPTIONS]

Options:
  -s, --samples-dir DIRECTORY  Path to directory with samples  [required]
  -c, --config FILE            Path to configuration file
  --help                       Show this message and exit.

```
For simple usage all you need is simply:
```bash
poetry run samples-validator -s path_to_samples
```
where path_to_samples is the result of
[samples generator tool][samples-generator-gh]

Configuration is made by modifying `conf.yaml`, but currently no changes
required

### Testing
```bash
poetry run mypy samples_validator
poetry run flake8 samples_validator
poetry run pytest .
```

### Description
The way this tool works is pretty straightforward:
1) Parse the samples dir structure and gather all API samples
(JS, Python, cURL)
2) Sort samples by HTTP method within an endpoint [TBD]
3) Create virtual environment for Python, as well as install all the dependencies
for Python and NodeJS in temporary directory
4) Run each sample and find out if output is correct
5) Print test session result with detailed failure explanation


Copyright © 2019 Platform Of Trust

[poetry-install]: https://github.com/sdispater/poetry#installation
[samples-generator-gh]: https://github.com/PlatformOfTrust/code-examples-generator