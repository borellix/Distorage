from flask import Blueprint, abort, request
import os
from uuid import uuid4

from ..servers import *

files = Blueprint('files', __name__)


def upload() -> dict[str, str]:
    """
    Upload a files
    :return: The uploaded files or an error message
    """
    file_ = request.files.get('file')
    if not file_:
        return abort(400, {"message": "Bad Request"})

    authorization = request.headers.get('Authorization')
    category_id = request.form.get('category')
    guilds_ids = request.form.get('guilds_ids')
    path = os.path.join(os.getcwd(), 'tmp', str(uuid4()) + '.' + file_.filename.split('.')[-1])
    file_.save(path)

    # if this is a custom server
    if authorization and guilds_ids:
        guilds_ids = [guild_id.strip() for guild_id in request.form.get('guilds_ids').rsplit(';')]
        custom_server = CustomServer(authorization, guilds_ids, category_id, prefix=request.form.get('prefix'))
        return custom_server.file_upload_or_edit(path=path)

    # if this is a common server
    if not authorization and not guilds_ids and not category_id:
        return common_server.file_upload_or_edit(path=path)
    # else: incoherent request
    else:
        return abort(400, {"message": "Bad Request"})


def download(file_key) -> dict[str, str]:
    """
    Download a file
    :return: The discord url file or an error message
    """
    channel_id, message_id = file_key.split(':')
    authorization = request.headers.get('Authorization')

    if authorization:  # Custom server
        custom_server = CustomServer(authorization=authorization)
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
    authorization = request.headers.get('Authorization')

    path = os.path.join(os.getcwd(), 'tmp', str(uuid4()) + '.' + file_.filename.split('.')[-1])
    file_.save(path)

    if authorization:  # Custom server
        custom_server = CustomServer(authorization=authorization)
        return custom_server.file_upload_or_edit(path=path, file_key=file_key)

    else:  # Common server
        return common_server.file_upload_or_edit(path=path, file_key=file_key)


def delete(file_key):
    if not file_key:
        return abort(404, {"message": "Bad Request"})

    authorization = request.headers.get('Authorization')

    if authorization:  # Custom server
        custom_server = CustomServer(authorization=authorization)
        return custom_server.file_delete(file_key=file_key)
    else:  # Common server
        return common_server.file_delete(file_key=file_key)


# Handle all methods for files in /files route
@files.route('/', methods=['POST'])
@files.route('/<string:file_key>', methods=['GET', 'PATCH', 'DELETE'])
def file(file_key=None):
    if request.method == 'POST':
        return upload()
    elif request.method == 'GET':
        return download(file_key=file_key)
    elif request.method == 'PATCH':
        return edit(file_key=file_key)
    elif request.method == 'DELETE':
        return delete(file_key=file_key)
