import bottle
from marshmallow import fields
from webargs.bottleparser import use_args
from webargs import fields as web_fields

app = bottle.Bottle()


@app.post('/')
@use_args({
    'dataContext': fields.URL(required=True),
    'parameterContext': fields.URL(required=True),
    'productCode': fields.String(required=True),
    'name': fields.String(required=True),
    'translatorUrl': fields.URL(required=True),
    'organizationPublicKeys': web_fields.Nested(
        {
            'type': fields.String(required=True),
            'url': fields.URL(required=True),
        },
        required=True, many=True, only=('type', 'url')
    ),
    'imageUrl': fields.URL(allow_none=True),
    'description': fields.String(allow_none=True),
})
def create(args):
    return {
        '@context': '<context URL>',
        '@type': 'Product',
        '@id': '<URL to the product resource>',
        'product_code': 'XXX',
        'dataContext': '<data context URL>',
        'parameterContext': '<parameter context URL>',
        'translatorUrl': '<translator URL>',
        'name': '<product name>',
        'organizationPublicKeys': [
            {
                'url': '<public key URL>',
                'type': '<public key type>'
            }
        ],
        'description': '<product description>',
        'imageUrl': '<image URL>'
    }


@app.get('/<product>')
def get_product(product):
    return {}


@app.get('/')
def list_products():
    return {}


@app.put('/<product>')
def edit(product):
    print(product)
    check_that_param_is_not_placeholder(product)
    return {}


@app.delete('/<product>')
def delete(product):
    check_that_param_is_not_placeholder(product)
    return {}


def check_that_param_is_not_placeholder(param: str):
    if param.startswith('{'):
        raise ValueError
