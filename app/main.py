import json

import requests
from flask import Flask, url_for, render_template, redirect, request, abort
import os
from uuid import uuid4

app = Flask(__name__)
API_BASE_URL = os.environ.get('API_BASE_URL')
BOT_TOKEN = os.environ.get('BOT_TOKEN')


class Discord:
    def __init__(self, bot_token: str):
        self.AUTHORIZATION = f'Bot {bot_token}'

    def get_available_channel_id(self) -> str or dict:
        guilds_ids = eval(os.environ['GUILDS_IDS'])  # eval() for convert string to list type
        for guild_id in guilds_ids:
            channels = self.get_channels(guild_id)
            if len(channels) < 500:
                for channel in channels:
                    try:
                        if channel['type'] == 0:
                            channel_id = channel['id']
                            if len(self.get_messages(channel_id)) < 100:
                                return channel_id
                    except TypeError:
                        return abort(401)
                return self.create_text_channel(name=str(self.get_channel_number(guild_id=guild_id)), guild_id=guild_id)
        return abort(503)

    def create_text_channel(self, name: str, guild_id: str, authorization: [str, None] = None) -> str:
        return requests.post(
            url=API_BASE_URL + f"/guilds/{guild_id}/channels",
            headers={'Authorization': authorization if authorization is not None else self.AUTHORIZATION},
            json={'name': name, 'type': 0}
        ).json()['id']

    def get_channel_number(self, guild_id: str) -> int:
        try:
            return max([int(channel['name']) for channel in self.get_channels(guild_id=guild_id)]) + 1
        except ValueError:
            return 1

    def get_channels(self, guild_id: str) -> dict:
        return requests.get(
            url=API_BASE_URL + f'/guilds/{guild_id}/channels',
            headers={
                'Authorization': self.AUTHORIZATION
            }
        ).json()

    def get_messages(self, channel_id: str) -> dict:
        return requests.get(
            url=API_BASE_URL + f'/channels/{channel_id}/messages',
            headers={'Authorization': self.AUTHORIZATION}
        ).json()

    def get_bot_guilds_id(self, authorization: [str, None] = None) -> list:
        guilds = requests.get(
            url=API_BASE_URL + f'/users/@me/guilds',
            headers={'Authorization': authorization if authorization is not None else self.AUTHORIZATION}
        ).json()
        try:
            return [guild['id'] for guild in guilds]
        except TypeError:
            return abort(401)

    def upload_file(self, channel_id: str, path: str, authorization: [str, None] = None) -> str or dict:
        file = open(path, mode='rb')
        response = requests.post(
            url=API_BASE_URL + f'/channels/{channel_id}/messages',
            headers={'Authorization': authorization if authorization is not None else self.AUTHORIZATION},
            data={"content": ""},
            files={'file': file}
        ).json()
        file.close()
        os.remove(path)
        try:
            message_id = response["id"]
        except KeyError:
            return abort(401)
        requests.patch(
            url=API_BASE_URL + f'/channels/{channel_id}/messages/{message_id}',
            headers={'Authorization': authorization if authorization is not None else self.AUTHORIZATION},
            data={"content": f"{channel_id}:{message_id}"}
        )
        return {"file_key": f"{channel_id}:{message_id}"}


    def edit_file(self, channel_id: str, message_id: str, path: str, authorization: [str, None] = None) -> str or dict:
        file = open(path, mode='rb')
        response = requests.patch(
            url=API_BASE_URL + f'/channels/{channel_id}/messages/{message_id}',
            headers={'Authorization': authorization if authorization is not None else self.AUTHORIZATION},
            files={'file': file,
                   'payload_json': (None, json.dumps({"attachments": []}), "application/json")
                   }
        ).json()
        print(response)
        file.close()
        os.remove(path)
        try:
            return {"file_key": f"{channel_id}:{response['id']}"}
        except KeyError:
            return abort(401)

    def get_message(self, channel_id, message_id, authorization: [str, None] = None) -> dict:
        return requests.get(
            url=API_BASE_URL + f"/channels/{channel_id}/messages/{message_id}",
            headers={"Authorization": authorization if authorization is not None else self.AUTHORIZATION},
        ).json()

    def get_channels_ids(self, guilds_ids, authorization: [str, None] = None) -> list:
        channels_ids = []
        for guild_id in guilds_ids:
            channels = requests.get(
                url=API_BASE_URL + f"/guilds/{guild_id}/channels",
                headers={"Authorization": authorization if authorization is not None else self.AUTHORIZATION}
            ).json()
            channels_ids += [channel['id'] for channel in channels]
        return channels_ids

    def delete_file(self, channel_id: str, message_id: str, authorization: [str, None] = None) -> None:
        requests.delete(
            url=API_BASE_URL + f"/channels/{channel_id}/messages/{message_id}",
            headers={"Authorization": authorization if authorization is not None else self.AUTHORIZATION}
        )


discord = Discord(BOT_TOKEN)


@app.route('/')
def _index():
    return redirect(url_for('_home'))


@app.route('/home', methods=['GET'])
def _home():
    return render_template('home.html')


@app.route('/file/upload', methods=['POST'])
def _file_upload():
    bot_token = request.form.get('bot_token')
    channel_id = request.form.get('channel_id')
    file = request.files.get('file')
    if file is None:
        return abort(400, {"message": "Bad Request"})
    path = os.path.join(os.getcwd(), 'temporary', str(uuid4()) + '.' + file.filename.split('.')[-1])
    file.save(path)

    if os.stat(path).st_size / (1024 * 1024) > 8:
        return abort(400, {"message": f"File Size Exceeds 8MB ({round(os.stat(path).st_size / (1024 * 1024), 2)}MB)"})

    if bot_token is None and channel_id is None:
        available_channel_id = discord.get_available_channel_id()
        if type(available_channel_id) is dict:
            print(available_channel_id.keys())
        return discord.upload_file(channel_id=available_channel_id, path=path)

    if bot_token is not None and channel_id is not None:
        return discord.upload_file(channel_id=channel_id, path=path,
                                   authorization="Bot " + bot_token)
    else:
        return abort(400, {"message": "Bad Request 1"})


@app.route('/file/download', methods=['POST'])
def _file_download():
    file_key = request.form.get('file_key')
    if file_key is None:
        return abort(400, {"message": "Bad Request"})
    channel_id, message_id = file_key.split(':')
    bot_token = request.args.get('bot_token')

    if bot_token is None:  # Common server
        response: dict = discord.get_message(channel_id=channel_id, message_id=message_id)
        if response.get('code') == 50001:
            return abort(401)
        try:
            url = response['attachments'][0]['url']
            return url
        except (KeyError, IndexError):
            if channel_id in discord.get_channels_ids(discord.get_bot_guilds_id()):
                return abort(404, {"message": "File Not Found"})
            else:
                return abort(401)
    else:  # Custom Server
        response: dict = discord.get_message(channel_id=channel_id, message_id=message_id, authorization=bot_token)
        if response.get('code') == 50001:
            return abort(401)
        try:
            url = response['attachments'][0]['url']
            return url
        except (KeyError, IndexError):
            return abort(404, {"message": "File Not Found"})


@app.route('/file/edit', methods=['POST'])
def _file_edit():
    bot_token = request.form.get('bot_token')
    file_key = request.form.get('file_key')
    file = request.files.get('file')
    if file_key is None or file is None:
        return abort(400, {"message": "Bad Request"})
    channel_id, message_id = file_key.split(':')
    path = os.path.join(os.getcwd(), 'temporary', str(uuid4()) + '.' + file.filename.split('.')[-1])
    file.save(path)

    if os.stat(path).st_size / (1024 * 1024) > 8:
        return abort(400, {"message": f"File Size Exceeds 8MB ({round(os.stat(path).st_size / (1024 * 1024), 2)}MB)"})

    if bot_token is None:
        available_channel_id = discord.get_available_channel_id()
        if type(available_channel_id) is dict:
            print(available_channel_id.keys())
        return discord.edit_file(channel_id=available_channel_id, message_id=message_id, path=path)

    else:
        return discord.edit_file(channel_id=channel_id, message_id=message_id, path=path,
                                 authorization="Bot " + bot_token)


@app.route('/file/delete', methods=['POST'])
def _file_delete():
    file_key = request.form.get('file_key')
    if file_key is None:
        return abort(404, {"message": "Bad Request"})

    channel_id, message_id = file_key.split(':')
    bot_token = request.args.get('bot_token')

    if bot_token is None:  # Common server
        discord.delete_file(channel_id, message_id)
    else:  # Custom server
        discord.delete_file(channel_id, message_id, authorization=bot_token)
    return ""


@app.errorhandler(400)
def bad_request(e):
    return {"error": {"message": e.description['message'], "code": 400}}, 400


@app.errorhandler(401)
def unauthorized(_e):
    return {"error": {"message": "Unauthorized", "code": 401}}, 401


@app.errorhandler(404)
def not_found(e):
    return {"error": {"message": e.description['message'], "code": 404}}, 404


@app.errorhandler(503)
def service_unavailable(_e):
    return {"error": {"message": "Service Unavailable", "code": 503}}, 503


if __name__ == '__main__':
    app.run('127.0.0.1', port=80, debug=True)
