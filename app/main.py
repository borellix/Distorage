from flask import Flask, url_for, render_template, redirect
import os

from .errors import errors
from . import api
from flask_assets import Environment, Bundle

app = Flask(__name__)
app.register_blueprint(errors)
app.register_blueprint(api.api, url_prefix='/api')

assets = Environment(app)

file = Bundle('css/home.scss', filters='pyscss', output='css/home.css', depends='*.scss')
assets.register('scss_all', file)
assets.init_app(app)


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
