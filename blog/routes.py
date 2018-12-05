from blog import app

@app.route('/')
def homw():
    return "Geuka niku!"

@app.route('/index')
def index():
    return "Hello, World!"
    