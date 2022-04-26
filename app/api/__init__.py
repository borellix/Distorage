from flask import Blueprint
from .v2 import v2, assets as v2_assets
api = Blueprint('api', __name__, template_folder='templates', static_folder='')
api.register_blueprint(v2, url_prefix='/v2')


@api.route('/')
def index():
    return 'Welcome to the API'
