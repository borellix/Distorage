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


class Server:
    def __init__(self, authorization: str, category_id: str = None, prefix: str = "") -> None:
        self._AUTHORIZATION = None
        self.AUTHORIZATION = authorization
        self.CATEGORY_ID = str(category_id)
        self.PREFIX = prefix

    @property
    def AUTHORIZATION(self) -> str:
        return self._AUTHORIZATION

    @AUTHORIZATION.setter
    def AUTHORIZATION(self, authorization) -> None:
        self._AUTHORIZATION = f'Bot {authorization}'

    def get_channels(self, guilds_ids: str or list[str]) -> list[dict] or any:
        """
        Get channels of guild that begin with the prefix
        :param guilds_ids: The guild id or list of guild ids
        :return: The channels of the guild
        """
        if isinstance(guilds_ids, list):
            return [
                channel for channel in (
                    self.get_channels(guilds_ids=guild_id) for guild_id in guilds_ids
                )
            ]
        if isinstance(guilds_ids, str):
            print(guilds_ids)
            # Return the channels of the guild if the name of the channel begins with the prefix
            return [
                channel for channel in (
                    requests.get(
                        url=API_BASE_URL + f'/guilds/{guilds_ids}/channels',
                        headers={'Authorization': self.AUTHORIZATION},
                    ).json()
                ) if channel['name'].startswith(self.PREFIX)
            ]

    def get_channels_ids(self, guild_id: str) -> list[str]:
        """
        Get the ids of the channels
        :param guild_id: The guild id
        :return: The ids of the channels
        """
        return [channel['id'] for channel in self.get_channels(guilds_ids=guild_id)]

    def get_available_channel_id(self, guild_id: str) -> str:
        """
        Get available channel id
        :param guild_id: The guild id
        :return: The available channel id
        """
        channels = self.get_channels(guilds_ids=guild_id)  # Get channels that begin with the prefix

        # Keep only the channels that are a text channel
        channels = [channel for channel in channels if channel['type'] == 0]
        if self.CATEGORY_ID:
            channels = [channel for channel in channels if channel['parent_id'] == self.CATEGORY_ID]
        channels = [channel for channel in channels if len(self.get_messages(channel_id=channel['id'])) < 100]


        # If there is no channel that hasn't got 100 messages in it, create a new one
        if not channels:
            return self.create_text_channel(
                guild_id=guild_id,
                name=self.PREFIX + str(self.get_channel_number(guild_id=guild_id))
            )['id']
        return channels[0]['id']

    def get_channel_number(self, guild_id: str) -> int:
        """
        Get the numbers of channels that begin with the prefix
        :param guild_id: The guild id
        :return: The numbers of channels begin with the prefix
        """
        try:
            channels = self.get_channels(guilds_ids=guild_id)  # Get channels that begin with the prefix
            return len(channels) + 1  # Return the number of channels that begin with the prefix + 1
        except ValueError:
            return 1

    def create_text_channel(self, guild_id: str, name: str) -> dict:
        """
        Create a text channel
        :param guild_id: The guild id
        :param name: The name of the channel
        :return: The created channel
        """
        json_data = {
            'name': name,
            'type': 0,  # 0 = text
        }
        if self.CATEGORY_ID:
            json_data['parent_id'] = self.CATEGORY_ID

        r = requests.post(
            url=API_BASE_URL + f'/guilds/{guild_id}/channels',
            headers={'Authorization': self.AUTHORIZATION},
            json=json_data
        ).json()  # Create a text channel with the name in the guild
        return r

    def get_messages(self, channel_id: str) -> dict:
        """
        Get messages of a channel
        :param channel_id: The channel id
        :return: The messages of the channel
        """
        return requests.get(
            url=API_BASE_URL + f'/channels/{channel_id}/messages',
            headers={'Authorization': self.AUTHORIZATION}
        ).json()  # Get messages of the channel

    def get_message(self, channel_id: str, message_id: str, *args, **kwargs) -> dict:
        """
        Get a message
        :param channel_id: The channel id
        :param message_id: The message id
        :param args: Arguments
        :param kwargs: Keyword arguments
        :return: The message
        """
        return requests.get(
            url=API_BASE_URL + f'/channels/{channel_id}/messages/{message_id}',
            headers={'Authorization': self.AUTHORIZATION}
        ).json()  # Get message

    def file_upload(self, path: str, guild_id: str, channel_id: str = None) -> dict:
        """"
        Upload a file
        :param path: The path of the file to upload
        :param guild_id: The guild id where the file will be uploaded
        :param channel_id: The channel id where the file will be uploaded
        :return: The uploaded file
        """
        file = open(path, 'rb')  # Open the file to upload
        if channel_id is None:
            # Get available channel id if channel_id is None
            channel_id = self.get_available_channel_id(guild_id=guild_id)
        response = requests.post(
            url=API_BASE_URL + f'/channels/{channel_id}/messages',
            headers={'Authorization': self.AUTHORIZATION},
            json={'content': ''},
            files={'file': file}
        ).json()  # Upload the file
        file.close()  # Close the file
        # os.remove(path)  TODO: Delete the file decomment this line if you want to delete the file
        return {'file_key': '{}:{}'.format(channel_id, response['id'])}  # Return the file key

    def file_edit(self, file_key: str, path: str) -> dict:
        """
        Edit a file
        :param file_key: The file key of the file to edit
        :param path: The path of the file to edit
        :return: The edited file
        """
        channel_id, message_id = file_key.split(":")
        file = open(path, 'rb')
        response = requests.patch(
            url=API_BASE_URL + f'/channels/{channel_id}/messages/{message_id}',
            headers={'Authorization': self.AUTHORIZATION},
            files={'file': file}
        ).json()
        file.close()
        # os.remove(path) TODO: Delete the file decomment this line if you want to delete the file
        return {'file_key': '{}:{}'.format(channel_id, response['id'])}

    def file_delete(self, file_key: str) -> None:
        """
        Delete a file
        :param file_key: The file key of the file to delete
        :return: None
        """
        channel_id, message_id = file_key.split(":")  # Get the channel id and the message id
        requests.delete(
            url=API_BASE_URL + f'/channels/{channel_id}/messages/{message_id}',
            headers={'Authorization': self.AUTHORIZATION}
        ).json()  # Delete the file message from the channel


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
    print(os.getcwd())
    print(os.path.join(os.getcwd(), 'temporary'))
    app.run('127.0.0.1', port=80, debug=True)
