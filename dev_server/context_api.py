import bottle

app = bottle.Bottle()


@app.get('/')
def list_contexts():
    return {}
