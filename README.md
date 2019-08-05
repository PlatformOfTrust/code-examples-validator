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
  -s, --samples-dir DIRECTORY   Path to directory with samples  [required]
  -c, --config FILE             Path to configuration file
  -l, --lang [python|js|shell]  Run samples only for that language. Run all of
                                them by default
  -k, --keyword TEXT            Sample name filter
  --help                        Show this message and exit.

```
For simple usage all you need is simply:
```bash
poetry run samples-validator -s <path_to_samples>
```
where <path_to_samples> is the result of
[samples generator tool][samples-generator-gh]

[Configuration](#configuration) is made by modification of `conf.yaml`

### Testing
```bash
poetry run mypy samples_validator
poetry run flake8 samples_validator
poetry run pytest .
```

### Description
The way this tool works can be described by following steps:
1) Parse the code examples directory structure and gather all API samples
(JS, Python, cURL)
2) Sort code examples by HTTP method and resource path*
3) Create virtual environment for Python, as well as install all the dependencies
for Python and NodeJS
4) Run each code example for each language in the right execution order. Replace
all the placeholders and variables with exact values*
5) Print test session result with detailed failure explanation. If some 
samples marked as ignored, their failures won't affect the exit code of a run

Some of the steps above need more detailed explanation though:
**Step 2, Sorting.**  
This tool tries to find the correct order of API samples. If some resource has
GET, POST, PUT and DELETE methods declared, then it makes sense to first 
create an entity (POST), then use its ID attribute to execute GET & PUT methods,
and finally DELETE it. For cases with nested resources, it also tries to
postpone the removal step as far as possible. For instance, if there are 
two endpoints, where one depends on another, the aim is to create the "parent" 
resource first, then create sub-resource and delete them in reverse order.
**Step 4, Execution.**
A lot of samples contain so-called "placeholders" in the source code. For example,
documentation usually can't provide some workable auth token, so there is 
`<AUTH_TOKEN>` placeholder instead. The same situation with ID attributes in 
URL and request body, to perform a request to delete some resource, we need to 
know it's ID first. As well as another required attributes. This tool tries
to solve these problems in several ways:
- Static placeholders can be defined in the configuration file. Examples:
access token, API version
- When POST request succeeds, the tool stores its response in the cache. Usually, API 
responds with information about the resource which has just created, as well as
its identifier. So in next requests for this resource and its sub-resources 
this tool will try to find the required data in the previous responses of
POST requests.  
- Code example generator provides a file called `debug.edn` for each API method.
This file contains all information about endpoint defined in RAML files. If RAML 
file has an example for API parameter and there is a placeholder for this 
parameter in the generated code sample, then this tool tries to use it as a value.
This approach is implemented, but not recommended. It's safe to provide exact
values in the payload examples in RAML files instead.  
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