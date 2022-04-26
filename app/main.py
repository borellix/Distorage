from flask import Flask, url_for, render_template, redirect
import os

from .errors import errors
from . import api

app = Flask(__name__)
app.register_blueprint(errors)
app.register_blueprint(api.api, url_prefix='/api')
app.config['LOAD_PATHS'] = [
    'D:/Code/Distorage/api/app/api/v2/static'
]
api.v2_assets.init_app(app)


@app.route('/')
def _index():
    return redirect(url_for('_home'))


@app.route('/home', methods=['GET'])
def _home():
    return render_template('home.html')


if __name__ == '__main__':
    print(os.getcwd())
    print(os.path.join(os.getcwd(), 'tmp'))
    app.run('127.0.0.1', port=80, debug=True)
