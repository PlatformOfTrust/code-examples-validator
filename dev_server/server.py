import json

import bottle

from dev_server.product_api import app as products_app

app = bottle.Bottle()
app.mount('/products/v1', products_app)


def custom_error_handler(error: bottle.HTTPError) -> str:
    try:
        body = json.loads(error.body)
    except json.decoder.JSONDecodeError:
        body = error.body

    data = {'error': {'status': error.status_code, 'message': body}}
    bottle.response.content_type = 'application/json'
    return json.dumps(data)


for application in (app, products_app):
    application.default_error_handler = custom_error_handler


def main(reload=False):
    app.run(
        host='localhost',
        port='8888',
        debug=True,
        reloader=reload,
    )


if __name__ == '__main__':
    main(reload=True)
