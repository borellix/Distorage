from flask import Blueprint, abort, request, render_template
import os
from uuid import uuid4

from app.api.v2.servers import *

file_manager = Blueprint('file_manager', __name__)



def upload() -> dict[str, str]:
    """
    Upload a file
    :return: The uploaded file or an error message
    """
    file_ = request.files.get('file')
    if not file_:
        return abort(400, {"message": "Bad Request"})

    server_key = request.headers.get('Server-Key')
    if '.' in file_.filename:
        path = os.path.join(os.getcwd(), 'tmp', str(uuid4()) + '.' + file_.filename.split('.')[-1])
    else:
        path = os.path.join(os.getcwd(), 'tmp', str(uuid4()))
    file_.save(path)

    # if this is a custom server
    if server_key:
        custom_server = CUSTOM_SERVERS[server_key]
        return custom_server.file_upload_or_edit(path=path)

    # if this is a common server
    else:
        return common_server.file_upload_or_edit(path=path)


def download(file_key) -> dict[str, str]:
    """
    Download a file
    :return: The discord url file or an error message
    """
    channel_id, message_id = file_key.split(':')
    server_key = request.headers.get('Server-Key')

    if server_key:  # Custom server
        custom_server = CUSTOM_SERVERS[server_key]
        response: dict = custom_server.get_message(channel_id=channel_id, message_id=message_id)
        if response.get('code') == 50001:
            return abort(401, {"message": "Unauthorized"})
        try:
            return {'url': response['attachments'][0]['url']}
        except (KeyError, IndexError):
            return abort(404, {"message": "File Not Found"})

    else:  # Common Server
        response: dict = common_server.get_message(channel_id=channel_id, message_id=message_id)
        if response.get('code') == 50001:
            return abort(401, {"message": "Unauthorized"})
        try:
            return {'url': response['attachments'][0]['url']}
        except (KeyError, IndexError):
            if channel_id in common_server.get_channels_ids():
                return abort(404, {"message": "File Not Found"})
            else:
                return abort(401, {"message": "Unauthorized"})


def edit(file_key) -> dict[str, str]:
    """
    Edit a file
    :return: The discord url file or an error message
    """
    file_ = request.files.get('file')
    if not file_:
        return abort(400, {"message": "Bad Request"})
    server_key = request.headers.get('Server-Key')

    if '.' in file_.filename:
        path = os.path.join(os.getcwd(), 'tmp', str(uuid4()) + '.' + file_.filename.split('.')[-1])
    else:
        path = os.path.join(os.getcwd(), 'tmp', str(uuid4()))
    file_.save(path)

    if server_key:  # Custom server
        custom_server = CUSTOM_SERVERS[server_key]
        return custom_server.file_upload_or_edit(path=path, file_key=file_key)

    else:  # Common server
        return common_server.file_upload_or_edit(path=path, file_key=file_key)


def delete(file_key):
    if not file_key:
        return abort(404, {"message": "Bad Request"})

    server_key = request.headers.get('Server-Key')

    if server_key:  # Custom server
        custom_server = CUSTOM_SERVERS[server_key]
        return custom_server.file_delete(file_key=file_key)
    else:  # Common server
        return common_server.file_delete(file_key=file_key)


# Init server
@file_manager.route('/init-server', methods=['POST'], strict_slashes=False)
@file_manager.route('/init_server', methods=['POST'], strict_slashes=False)
def init_server() -> dict[str, str]:
    authorization = request.headers.get('Authorization')
    if not authorization:
        return abort(401, {"message": "Unauthorized"})
    custom_server = CustomServer(
        authorization=authorization,
        guilds_ids=request.form.get('guilds_ids').split(';'),
        category_name=request.form.get('category_name'),
        prefix=request.form.get('prefix')
    )
    server_key = str(uuid4())
    CUSTOM_SERVERS[server_key] = custom_server
    return {'Server-Key': server_key}


# Handle all methods for files in /file route
@file_manager.route('', methods=['POST'], strict_slashes=False)
@file_manager.route('/<string:file_key>', methods=['GET', 'PATCH', 'DELETE'], strict_slashes=False)
def file(file_key=None):
    print(request.method)
    if request.method == 'POST':
        return upload()
    elif request.method == 'GET':
        return download(file_key=file_key)
    elif request.method == 'PATCH':
        return edit(file_key=file_key)
    elif request.method == 'DELETE':
        return delete(file_key=file_key)


# The intefrace for the file manager
@file_manager.route('/', methods=['GET'], strict_slashes=False)
def index():
    return render_template('api/v2/file.html')
