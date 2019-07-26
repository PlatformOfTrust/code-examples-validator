## PoT code samples validation tool

[![Build Status](https://travis-ci.org/PlatformOfTrust/code-examples-validator.svg?branch=master)](https://travis-ci.org/PlatformOfTrust/code-examples-validator)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Platform_of_Trust_Code_Examples_Validator&metric=alert_status)](https://sonarcloud.io/dashboard?id=Platform_of_Trust_Code_Examples_Validator)

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

[Configuration](#configuration) is made by modification of `conf.yaml`

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
2) Sort samples by HTTP method within an endpoint
3) Create virtual environment for Python, as well as install all the dependencies
for Python and NodeJS in temporary directory
4) Run each sample and find out if output is correct
5) Print test session result with detailed failure explanation

### Configuration

**sample_timeout** - Execution timeout per sample  
**debug** - Extended output like stdout/stderr logging from even
successful runs  
**substitutions** - Rules for placeholder replacements in a source code 
of generated samples  
**resp_attr_replacements** - Conversion rules for keys in JSON bodies of POST
responses. For example, you have two code examples: `POST /resource` and
`GET /resource/{id}`. First endpoint respond with a JSON like
`{"resourceId": "123}`. So basically you need to get `resourceId` from the 
previous response and use it as substitution of `{id}` placeholder in the next 
response. Then you can define such conversion rules per each test.
   


---
Copyright © 2019 Platform Of Trust

[poetry-install]: https://github.com/sdispater/poetry#installation
[samples-generator-gh]: https://github.com/PlatformOfTrust/code-examples-generator