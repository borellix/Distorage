from flask import Blueprint
from .file_manager import file_manager
from flask import current_app as app
from flask_assets import Environment, Bundle

v2 = Blueprint('v2', __name__, static_folder='static', template_folder='templates')

assets = Environment(app)

file = Bundle('api/v2/static/file.scss',  filters='pyscss', output='api/v2/static/file.css', depends='*.scss')
assets.register('scss_all', file)

v2.register_blueprint(file_manager, url_prefix='/file', template_folder='template', static_folder='static')


@v2.route('/')
def index():
    return 'Welcome to the 2nd version of the API'
