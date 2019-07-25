import bottle
from marshmallow import fields
from webargs.bottleparser import use_args

app = bottle.Bottle()


@app.post('/')
@use_args({
    "toIdentity": fields.String(required=True),
    "subject": fields.String(required=True),
    "content": fields.String(required=True),
    "cc": fields.List(fields.String()),
})
def create(args):
    return {
        "@context": "<URL to message context>",
        "@type": "Message",
        "@id": "identity",
        "id": "mmmmmmmm",
        "toIdentity": "abc-def",
        "subject": "<message subject>",
        "content": "<message content>",
        "cc": [
            "<list of identity IDs>"
        ],
        "createdAt": "2019-01-10T12:00:00Z",
        "updatedAt": "2019-01-10T12:00:00Z",
        "createdBy": "<user ID who created the message>"
    }


@app.get('/<message>')
def get(message):
    return {}


@app.put('/<message>')
def put(message):
    return {}


@app.delete('/<message>')
def delete(message):
    return {}


@app.post('/<message>/read')
def read(message):
    return {}


@app.get('/<toIdentity>/list')
def list_messages(toIdentity):
    return {}
