from flask import Blueprint
from .file_manager import file_manager

v2 = Blueprint('v2', __name__)
v2.register_blueprint(file_manager, url_prefix='/file')
