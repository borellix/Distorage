from flask import Blueprint
from .v2 import v2

api = Blueprint('api', __name__)
api.register_blueprint(v2, url_prefix='/v2')


@api.route('/')
def index():
    return 'Welcome to the API'
