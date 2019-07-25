from textwrap import dedent

from samples_validator.base import Language


def simple_param_curl():
    edn = dedent("""{
    :apiVersion "v1",
    :productName {:type "string", :description "Product", :example "Whiskey"}
    }
    """)
    parsed = {'productName': 'Whiskey'}
    sample = dedent("""
    "{
        \\"productName\\": \\"<Product name>\\"
    "}
    """)
    subs = {'<Product name>': 'Whiskey'}
    return edn, parsed, sample, subs, Language.shell


def array_param_curl():
    edn = dedent("""{
    :apiVersion "v1",
    :keys
      {
        :type "array",
        :example "[{\\"key\\": \\"rsa\\"}]",
        :description "Test"}
    }
    """)
    parsed = {'keys': [{'key': 'rsa'}]}
    sample = dedent("""
    "{
        \\"keys\\": [{\\"key\\": \\"<VALUE>\\"}]
    "}
    """)
    subs = {'[{\\"key\\": \\"<VALUE>\\"}]': '[{\\"key\\": \\"rsa\\"}]'}
    return edn, parsed, sample, subs, Language.shell


def simple_param_curl_py():
    edn = dedent("""{
    :apiVersion "v1",
    :imageUrl {:type "string", :description "URL", :example "http://ok"}
    }
    """)
    parsed = {'imageUrl': 'http://ok'}
    sample = dedent("""
    data=({"imageUrl":"<image URL>"})
    """)
    subs = {'<image URL>': 'http://ok'}
    return edn, parsed, sample, subs, Language.python


def array_param_py():
    edn = dedent("""{
    :apiVersion "v1",
    :keys
      {
        :type "array",
        :example "[{\\"key\\": \\"rsa\\"}]",
        :description "Test"}
    }
    """)
    parsed = {'keys': [{'key': 'rsa'}]}
    sample = dedent("""
    data=({"keys": [{"key":"<key type>"}]})
    """)
    subs = {'[{"key":"<key type>"}]': '[{"key": "rsa"}]'}
    return edn, parsed, sample, subs, Language.python
