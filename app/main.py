import json

import requests
from flask import Flask, url_for, render_template, redirect, request, abort
import os
from uuid import uuid4

app = Flask(__name__)
API_BASE_URL = os.environ.get('API_BASE_URL')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GUILDS_IDS = os.environ.get('GUILDS_IDS').split(';')
MEGABYTE = 1024 * 1024


class Discord:
    def __init__(self, bot_token: str):
        self.AUTHORIZATION = f'Bot {bot_token}'

    def get_available_channel_id(self) -> str or dict:
        guilds_ids = eval(os.environ['guilds_ids'])  # eval() for convert string to list type
        for guilds_ids in guilds_ids:
            channels = self.get_channels(guilds_ids)
            if len(channels) < 500:
                for channel in channels:
                    try:
                        if channel['type'] == 0:
                            channel_id = channel['id']
                            if len(self.get_messages(channel_id)) < 100:
                                return channel_id
                    except TypeError:
                        return abort(401)
                return self.create_text_channel(name=str(self.get_channel_number(guilds_ids=guilds_ids)),
                                                guilds_ids=guilds_ids)
        return abort(503)

    def create_text_channel(self, name: str, guilds_ids: list[str] = None, authorization: [str, None] = None) -> str:
        return requests.post(
            url=API_BASE_URL + f"/guilds/{guilds_ids}/channels",
            headers={'Authorization': authorization if authorization is not None else self.AUTHORIZATION},
            json={'name': name, 'type': 0}
        ).json()['id']

    def get_channel_number(self, guilds_ids: list[str] = None) -> int:
        try:
            return max([int(channel['name']) for channel in self.get_channels(guilds_ids=guilds_ids)]) + 1
        except ValueError:
            return 1

    def get_channels(self, guilds_ids: list[str] = None) -> dict:
        return requests.get(
            url=API_BASE_URL + f'/guilds/{guilds_ids}/channels',
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
        for guilds_ids in guilds_ids:
            channels = requests.get(
                url=API_BASE_URL + f"/guilds/{guilds_ids}/channels",
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
    API_BASE_URL = 'https://discord.com/api/v9'

    def __init__(self,
                 authorization: str,
                 category_id: str = None,
                 prefix: str = "",
                 guilds_ids: list[str] or str = None
                 ) -> None:
        self._AUTHORIZATION = None
        self.AUTHORIZATION = authorization
        self.CATEGORY_ID = str(category_id)
        self.PREFIX = prefix
        if isinstance(guilds_ids, int):
            guilds_ids = str(guilds_ids)
        if isinstance(guilds_ids, str):
            guilds_ids = [guilds_ids]

        self.GUILDS_IDS = guilds_ids
        self._SERVER_TYPE = None

    @property
    def SERVER_TYPE(self):
        return self._SERVER_TYPE

    @property
    def AUTHORIZATION(self) -> str:
        return self._AUTHORIZATION

    @AUTHORIZATION.setter
    def AUTHORIZATION(self, authorization) -> None:
        self._AUTHORIZATION = f'Bot {authorization}'

    def get_guilds_ids(self, guilds_ids: list[str] or str = None) -> list[str]:
        if isinstance(guilds_ids, str):
            return [guilds_ids]
        if isinstance(guilds_ids, int):
            return [str(guilds_ids)]
        if not guilds_ids:
            if self.GUILDS_IDS:
                return self.GUILDS_IDS
            else:
                raise ValueError("No guild ID is specified")

        return guilds_ids

    def get_channels(self, guilds_ids: list[str] or str = None) -> list[dict] or any:
        """
        Get channels of guild that begin with the prefix
        :param guilds_ids: The guild id or list of guild ids
        :return: The channels of the guild
        """
        guilds_ids = self.get_guilds_ids(guilds_ids)

        return [
            channel for guild_channel in [
                (
                    requests.get(
                        url=self.API_BASE_URL + f'/guilds/{guild_id}/channels',
                        headers={'Authorization': self.AUTHORIZATION},
                    ).json()
                ) for guild_id in guilds_ids
            ] for channel in guild_channel if channel['name'].startswith(self.PREFIX)
        ]  # Return the channels of the guilds that begin with the prefix

    def get_channels_ids(self, guilds_ids: list[str] = None) -> list[str]:
        """
        Get the ids of the channels
        :param guilds_ids: The guild id
        :return: The ids of the channels
        """
        guilds_ids = self.get_guilds_ids(guilds_ids)
        return [channel['id'] for channel in self.get_channels(guilds_ids=guilds_ids)]

    def get_available_guild_id(self, guilds_ids: list[str] = None) -> str:
        """
        Get the id of the first guild that has less than 500 channels for a common server and 400 channels for custom
        server
        :param guilds_ids: The list of guild ids
        :return: The id of the first guild that has less than 500 channels for a common server and 400 channels for
        """
        if self.SERVER_TYPE == "COMMON":
            guilds_ids = self.get_guilds_ids(guilds_ids)
            return [
                guild_id for guild_id in guilds_ids
                if len(self.get_channels(guild_id)) < int(os.getenv("MAX_CHANNELS_COMMON_SERVER"))
            ][0]
        elif self.SERVER_TYPE == "CUSTOM":
            guilds_ids = self.get_guilds_ids(guilds_ids)
            return [
                guild_id for guild_id in guilds_ids
                if len(self.get_channels(guild_id)) < int(os.getenv('MAX_CHANNELS_CUSTOM_SERVER'))
            ][0]
        else:
            raise ValueError("The server type is not specified")

    def get_available_channel_id(self, guilds_ids: list[str] or str = None) -> str:
        """
        Get available channel id
        :param guilds_ids: The guilds ids or the guild id where it will be found an available channel
        :return: The available channel id
        """
        guilds_ids = self.get_guilds_ids(guilds_ids)
        channels = self.get_channels(guilds_ids=guilds_ids)  # Get channels that begin with the prefix

        # Keep only the channels that are a text channel
        channels = [channel for channel in channels if channel['type'] == 0]
        if self.CATEGORY_ID:
            channels = [channel for channel in channels if channel['parent_id'] == self.CATEGORY_ID]
        channels = [channel for channel in channels if len(self.get_messages(channel_id=channel['id'])) < 100]

        # If there is no channel that hasn't got 100 messages in it, create a new one
        if not channels:
            available_guild_id = self.get_available_guild_id(guilds_ids=guilds_ids)
            return self.create_text_channel(
                guild_id=available_guild_id,
                name=self.PREFIX + str(self.get_channel_number(guild_id=available_guild_id))
            )['id']
        return channels[0]['id']

    def get_channel_number(self, guild_id: str = None) -> int:
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

    def create_text_channel(self, name: str, guild_id: str) -> dict:
        """
        Create a text channel
        :param name: The name of the channel
        :param guild_id: The guild id
        :return: The created channel
        """
        json_data = {
            'name': name,
            'type': 0,  # 0 = text
        }
        if self.CATEGORY_ID:
            json_data['parent_id'] = self.CATEGORY_ID

        r = requests.post(
            url=self.API_BASE_URL + f'/guilds/{guild_id}/channels',
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
            url=self.API_BASE_URL + f'/channels/{channel_id}/messages',
            headers={'Authorization': self.AUTHORIZATION}
        ).json()  # Get messages of the channel

    def get_message(self, channel_id: str, message_id: str) -> dict:
        """
        Get a message
        :param channel_id: The channel id
        :param message_id: The message id
        :return: The message
        """
        return requests.get(
            url=self.API_BASE_URL + f'/channels/{channel_id}/messages/{message_id}',
            headers={'Authorization': self.AUTHORIZATION}
        ).json()  # Get message

    def _file_upload(self, path: str, guilds_ids: list[str] = None, channel_id: str = None) -> dict[str, str]:
        """"
        Upload a file
        :param path: The path of the file to upload
        :param guilds_ids: The guild id where the file will be uploaded
        :param channel_id: The channel id where the file will be uploaded
        :return: The uploaded file
        """
        file = open(path, 'rb')  # Open the file to upload
        if channel_id is None:
            # Get available channel id if channel_id is None
            channel_id = self.get_available_channel_id(guilds_ids=guilds_ids)
        response = requests.post(
            url=self.API_BASE_URL + f'/channels/{channel_id}/messages',
            headers={'Authorization': self.AUTHORIZATION},
            json={'content': ''},
            files={'file': file}
        ).json()  # Upload the file
        file.close()  # Close the file
        # os.remove(path)  TODO: Delete the file uncomment this line if you want to delete the file
        return {'file_key': '{}:{}'.format(channel_id, response['id'])}  # Return the file key

    def _file_edit(self, file_key: str, path: str) -> dict[str, str]:
        """
        Edit a file
        :param file_key: The file key of the file to edit
        :param path: The path of the file to edit
        :return: The edited file
        """
        channel_id, message_id = file_key.split(":")
        file = open(path, 'rb')
        response = requests.patch(
            url=self.API_BASE_URL + f'/channels/{channel_id}/messages/{message_id}',
            headers={'Authorization': self.AUTHORIZATION},
            files={'file': file}
        ).json()
        file.close()
        # os.remove(path) TODO: Delete the file uncomment this line if you want to delete the file
        return {'file_key': '{}:{}'.format(channel_id, response['id'])}

    def file_delete(self, file_key: str) -> None:
        """
        Delete a file
        :param file_key: The file key of the file to delete
        :return: None
        """
        channel_id, message_id = file_key.split(":")  # Get the channel id and the message id
        requests.delete(
            url=self.API_BASE_URL + f'/channels/{channel_id}/messages/{message_id}',
            headers={'Authorization': self.AUTHORIZATION}
        ).json()  # Delete the file message from the channel

    def get_boosts_level(self, guild_id: str) -> int:
        """
        Get the boosts level of a guild
        :param guild_id: The guild id
        :return: The boosts level
        """
        return requests.get(
            url=self.API_BASE_URL + f'/guilds/{guild_id}',
            headers={'Authorization': self.AUTHORIZATION}
        ).json()['premium_tier']  # Get the boosts level of the guild

    def get_boosts_levels(self, guilds_ids: list[str] = None) -> dict[str, int]:
        """
        Return premium_level of the guild if that is give else of self.GUILDS_IDS order by id
        :param guilds_ids: The guilds ids
        :return: The boosts level of the guilds
        """
        return {guild_id: self.get_boosts_level(guild_id) for guild_id in guilds_ids or self.GUILDS_IDS}


class CommonServer(Server):
    SERVER_TYPE = 'COMMON'

    def __init__(self):
        super().__init__(authorization=BOT_TOKEN, guilds_ids=GUILDS_IDS)

    def file_upload_or_edit(self, path: str, file_key: str = None, guilds_ids: list[str] = None) -> dict[str, str]:
        """
        Upload or edit the file with check if the size limit doesn't
        exceed the limit of the server
        :param path: The path of the file to upload or edit
        :param file_key: The file key of the file to edit
        :param guilds_ids: The guilds ids
        :return: The file key
        """
        # Check if the file doesn't exceed the limit of the server (8MB)
        file_size = os.path.getsize(path)
        if file_size > 8 * MEGABYTE:
            return abort(
                400,
                {'message': f"The file is too big ({round(file_size / MEGABYTE, 2)}MB), the limit is 8MB"}
            )
        if file_key:
            self._file_edit(file_key=file_key, path=path)
        else:
            # Upload the file if the file_key is None
            file_key = self._file_upload(path=path, guilds_ids=guilds_ids)
        os.remove(path)  # Delete the file
        return {'file_key': file_key}


class CustomServer(Server):
    SERVER_TYPE = 'CUSTOM'

    def __init__(self,
                 authorization: str,
                 guilds_ids: list[str] or str = None,
                 category_id: str = None,
                 prefix: str = None
                 ):
        super().__init__(authorization=authorization, category_id=category_id, prefix=prefix, guilds_ids=guilds_ids)

    def file_upload_or_edit(self, path: str, file_key: str = None, guilds_ids: list[str] = None) -> dict[str, str]:
        guild_id = self.get_available_guild_id(guilds_ids)
        file_size = os.path.getsize(path)
        rounded_file_size_megabytes = round(file_size / MEGABYTE, 2)
        # Check if the file is too big
        if file_size > 8 * MEGABYTE and self.get_boosts_level(guild_id) < 2:
            return abort(
                400, {
                    "message": f"The file is too big ({rounded_file_size_megabytes}MB)"
                               f" and the guild ({guild_id}) doesn't have the required boosts level (2)"
                               f" for upload more than 8MB files"
                }
            )
        elif file_size > 50 * MEGABYTE and self.get_boosts_level(guild_id) < 3:
            return abort(
                400, {
                    "message": f"The file is too big ({rounded_file_size_megabytes}MB)"
                               f" and the guild ({guild_id}) doesn't have the required boosts level (3)"
                               f" for upload more than 50MB files"
                }
            )
        elif file_size > 100 * MEGABYTE:
            return abort(
                400, {
                    "message": f"The file is too big ({rounded_file_size_megabytes}MB)"
                               f" for upload more than 100MB files"
                }
            )

        if file_key:
            self._file_edit(file_key=file_key, path=path)
        else:
            file_key = self._file_upload(path=path)
        os.remove(path)
        return {'file_key': file_key}


common_server = CommonServer()


@app.route('/')
def _index():
    return redirect(url_for('_home'))


@app.route('/home', methods=['GET'])
def _home():
    return render_template('home.html')


@app.route('/file/upload', methods=['POST'])
def _file_upload() -> dict[str, str]:
    """
    Upload a file
    :return: The uploaded file or an error message
    """
    file = request.files.get('file')
    if not file:
        return abort(400, {"message": "Bad Request"})

    authorization = request.form.get('bot_token')
    category_id = request.form.get('category')
    guilds_ids = [guild_id.strip() for guild_id in request.form.get('guilds_ids').rsplit(';')]

    path = os.path.join(os.getcwd(), 'tmp', str(uuid4()) + '.' + file.filename.split('.')[-1])
    file.save(path)

    # if this is a custom server
    if authorization and guilds_ids:
        custom_server = CustomServer(authorization, guilds_ids, category_id)
        return custom_server.file_upload_or_edit(path=path)

    # if this is a common server
    if not authorization and not guilds_ids and not category_id:
        return common_server.file_upload_or_edit(path=path)
    # else: incoherent request
    else:
        return abort(400, {"message": "Bad Request"})


@app.route('/file/download', methods=['POST'])
def _file_download():
    """
    Download a file
    :return: The discord url file or an error message
    """
    file_key = request.form.get('file_key')
    if file_key is None:
        return abort(400, {"message": "Bad Request"})
    channel_id, message_id = file_key.split(':')
    authorization = request.args.get('bot_token')

    if authorization:  # Custom server
        custom_server = CustomServer(authorization=authorization)
        response: dict = custom_server.get_message(channel_id=channel_id, message_id=message_id)
        if response.get('code') == 50001:
            return abort(401)
        try:
            return response['attachments'][0]['url']
        except (KeyError, IndexError):
            return abort(404, {"message": "File Not Found"})

    else:  # Common Server
        response: dict = common_server.get_message(channel_id=channel_id, message_id=message_id)
        if response.get('code') == 50001:
            return abort(401)
        try:
            return response['attachments'][0]['url']
        except (KeyError, IndexError):
            if channel_id in common_server.get_channels_ids(common_server.get_guilds_ids()):
                return abort(404, {"message": "File Not Found"})
            else:
                return abort(401, )


@app.route('/file/edit', methods=['POST'])
def _file_edit() -> dict[str, str]:
    """
    Edit a file
    :return: The discord url file or an error message
    """
    file = request.files.get('file')
    file_key = request.form.get('file_key')
    if not file_key or not file:
        return abort(400, {"message": "Bad Request"})
    authorization = request.form.get('bot_token')
    guilds_ids = request.form.get('guilds_ids')

    path = os.path.join(os.getcwd(), 'tmp', str(uuid4()) + '.' + file.filename.split('.')[-1])
    file.save(path)

    if authorization and guilds_ids:  # Custom server
        custom_server = CustomServer(authorization=authorization, guilds_ids=guilds_ids)
        return custom_server.file_upload_or_edit(path=path, file_key=file_key)

    if not authorization and not guilds_ids:  # Common server
        return common_server.file_upload_or_edit(path=path, file_key=file_key)

    # else: incoherent request
    else:
        return abort(400, {"message": "Bad Request"})


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
    print(os.path.join(os.getcwd(), 'tmp'))
    app.run('127.0.0.1', port=80, debug=True)
