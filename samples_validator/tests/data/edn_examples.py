from textwrap import dedent


def simple_param_load():
    return dedent("""{
    :apiVersion "v1",
    :productName {:type "string", :description "Product", :example "Whiskey"}
    }
    """), {'productName': 'Whiskey'}


def simple_param():
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
    return edn, parsed, sample, subs


def array_param():
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
    return edn, parsed, sample, subs
