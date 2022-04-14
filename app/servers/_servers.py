import requests
import os
import json
from flask import abort

API_BASE_URL = os.environ.get('API_BASE_URL')
AUTHORIZATION = os.environ.get('AUTHORIZATION')
GUILDS_IDS = os.environ.get('GUILDS_IDS').split(';')
MEGABYTE = 1024 * 1024


class Server:
    API_BASE_URL = 'https://discord.com/api/v9'

    def __init__(self,
                 authorization: str,
                 category_name: str = None,
                 prefix: str = "",
                 guilds_ids: list[str] or str = None
                 ) -> None:
        self._AUTHORIZATION = None
        self.AUTHORIZATION = authorization
        if category_name:
            self.CATEGORY_NAME = str(category_name)
        else:
            self.CATEGORY_NAME = None
        self.PREFIX = prefix
        if not prefix:
            self.PREFIX = ""
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

    def get_bot_id(self) -> str:
        """
        Get the bot id
        :return: The bot id
        """
        return requests.get(
            url=self.API_BASE_URL + '/users/@me',
            headers={'Authorization': self.AUTHORIZATION},
        ).json()['id']  # Get the bot id

    def get_channels(self, guild_id: str = None) -> list[dict] or any:
        """
        Get channels of guild that begin with the prefix
        :return: The channels of the guild
        """
        guilds_ids = [guild_id] if guild_id else self.GUILDS_IDS
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

    def get_channels_ids(self) -> list[str]:
        """
        Get the ids of the channels
        :return: The ids of the channels
        """
        return [channel['id'] for channel in self.get_channels()]

    def get_available_guild_id(self) -> str:
        """
        Get the id of the first guild that has less than 500 channels for a common server and 400 channels for custom
        server
        :return: The id of the first guild that has less than 500 channels for a common server and 400 channels for
        """
        if self.SERVER_TYPE == "COMMON":
            return [
                guild_id for guild_id in self.GUILDS_IDS
                if len(self.get_channels(guild_id)) < int(os.getenv("MAX_CHANNELS_COMMON_SERVER"))
            ][0]
        elif self.SERVER_TYPE == "CUSTOM":
            return [
                guild_id for guild_id in self.GUILDS_IDS
                if len(self.get_channels(guild_id)) < int(os.getenv('MAX_CHANNELS_CUSTOM_SERVER'))
            ][0]
        else:
            raise ValueError("The server type is not specified")

    def get_available_channel_id(self) -> str:
        """
        Get available channel id
        :return: The available channel id
        """
        channels = self.get_channels()  # Get channels that begin with the prefix

        # Keep only the channels that are a text channel
        channels = [channel for channel in channels if channel['type'] == 0]
        if self.CATEGORY_NAME:
            channels = [
                channel for channel in channels if
                channel['parent_id'] == self.get_category_id(
                    guild_id=channel['guild_id'],
                    category_name=self.CATEGORY_NAME
                )
            ]
        channels = [channel for channel in channels if len(self.get_messages(channel_id=channel['id'])) < 100]

        # If there is no channel that hasn't got 100 messages in it, create a new one
        if not channels:
            available_guild_id = self.get_available_guild_id()
            return self.create_text_channel(
                guild_id=available_guild_id,
                name=self.PREFIX + str(self.get_channel_number(guild_id=available_guild_id))
            )['id']
        return channels[0]['id']

    def get_channel_number(self, guild_id: str) -> int:
        """
        Get the numbers of channels that begin with the prefix
        :param guild_id: The guild id
        :return: The numbers of channels begin with the prefix
        """
        try:
            channels = self.get_channels(guild_id)  # Get channels that begin with the prefix
            return len(channels) + 1  # Return the number of channels that begin with the prefix + 1
        except ValueError:
            return 1

    def get_everyone_id(self, guild_id: str) -> str:
        """
        Get the id of the everyone role
        :param guild_id: The guild id
        :return: The id of the everyone role
        """
        # Use requests
        response = requests.get(
            url=self.API_BASE_URL + f"/guilds/{guild_id}/roles",
            headers={'Authorization': self.AUTHORIZATION}
        )
        # Get the id of the everyone role
        return [role['id'] for role in response.json() if role['name'] == "@everyone"][0]

    def get_category_id(self, guild_id: str, category_name: str) -> str:
        """
        Get the id of the category
        :param guild_id: The guild id
        :param category_name: The category name
        :return: The id of the category
        """
        response = requests.get(
            url=self.API_BASE_URL + f"/guilds/{guild_id}/channels",
            headers={'Authorization': self.AUTHORIZATION}
        )
        try:
            return [category['id'] for category in response.json() if category['name'] == category_name][0]
        except IndexError:
            return self.create_category(guild_id=guild_id, name=category_name)['id']

    def create_category(self, guild_id: str, name: str) -> dict:
        """
        Create a category channel
        :param guild_id: The guild id
        :param name: The name of the category channel
        :return: The category channel
        """
        r = requests.post(
            url=self.API_BASE_URL + f"/guilds/{guild_id}/channels",
            headers={'Authorization': self.AUTHORIZATION},
            json={
                "name": name,
                "type": 4,
                "permission_overwrites": [
                    {
                        "type": 0,  # 0 = role
                        "id": self.get_everyone_id(guild_id=guild_id),  # Get the id of the everyone role
                        "deny": 0x400 | 0x10  # Deny the permission to see the channel
                    },
                    {
                        "type": 1,  # 1 = user
                        "id": self.get_bot_id(),  # Get the id of the bot
                        "allow": 0x400 | 0x10  # Allow the permission to:
                        # see the channel and manage channel
                    }
                ]
            }
        ).json()
        return r

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
        if self.CATEGORY_NAME:
            json_data['parent_id'] = self.get_category_id(guild_id=guild_id, category_name=self.CATEGORY_NAME)

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

    def _file_upload(self, path: str, channel_id: str = None) -> dict[str, str]:
        """"
        Upload a files
        :param path: The path of the files to upload
        :param channel_id: The channel id where the files will be uploaded
        :return: The uploaded files
        """
        file = open(path, 'rb')  # Open the file to upload
        if channel_id is None:
            # Get available channel id if channel_id is None
            channel_id = self.get_available_channel_id()
        response = requests.post(
            url=self.API_BASE_URL + f'/channels/{channel_id}/messages',
            headers={'Authorization': self.AUTHORIZATION},
            json={'content': ''},
            files={'files': file}
        ).json()  # Upload the file
        file.close()  # Close the file
        return {'file_key': '{}:{}'.format(channel_id, response['id'])}  # Return the file key

    def _file_edit(self, file_key: str, path: str) -> dict[str, str]:
        """
        Edit a files
        :param file_key: The files key of the files to edit
        :param path: The path of the files to edit
        :return: The edited files
        """
        channel_id, message_id = file_key.split(":")
        file = open(path, 'rb')  # Open the file to edit
        requests.patch(
            url=self.API_BASE_URL + f'/channels/{channel_id}/messages/{message_id}',
            headers={'Authorization': self.AUTHORIZATION},
            files={
                'files': file,
                'payload_json': (None, json.dumps({"attachments": []}), "application/json")
            }
        ).json()  # Edit the file
        file.close()  # Close the file
        return {'file_key': file_key}

    def file_delete(self, file_key: str) -> tuple[dict[str, str], int]:
        """
        Delete a files
        :param file_key: The files key of the files to delete
        :return: None
        """
        channel_id, message_id = file_key.split(":")  # Get the channel id and the message id
        requests.delete(
            url=self.API_BASE_URL + f'/channels/{channel_id}/messages/{message_id}',
            headers={'Authorization': self.AUTHORIZATION}
        )  # Delete the files message from the channel
        return {'message': "DELETED"}, 200  # Return a response with a status code of 200

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
        super().__init__(authorization=AUTHORIZATION, guilds_ids=GUILDS_IDS)

    def file_upload_or_edit(self, path: str, file_key: str = None) -> dict[str, str]:
        """
        Upload or edit the files with check if the size limit doesn't
        exceed the limit of the server
        :param path: The path of the files to upload or edit
        :param file_key: The files key of the files to edit
        :return: The files key
        """
        # Check if the files doesn't exceed the limit of the server (8MB)
        file_size = os.path.getsize(path)
        if file_size > 8 * MEGABYTE:
            return abort(
                400,
                {'message': f"The files is too big ({round(file_size / MEGABYTE, 2)}MB), the limit is 8MB"}
            )
        if file_key:
            self._file_edit(file_key=file_key, path=path)
            os.remove(path)  # Delete the file
            return {'file_key': file_key}
        else:
            # Upload the files if the file_key is None
            file_key = self._file_upload(path=path)
            os.remove(path)  # Delete the file
            return file_key


class CustomServer(Server):
    SERVER_TYPE = 'CUSTOM'

    def __init__(self,
                 authorization: str,
                 guilds_ids: list[str] or str = None,
                 category_name: str = None,
                 prefix: str = ""
                 ):
        super().__init__(authorization=authorization, category_name=category_name, prefix=prefix, guilds_ids=guilds_ids)

    def get_guild_id_by_channel_id(self, channel_id: str) -> str:
        """
        Get the guild id of the channel
        :param channel_id: The channel id
        :return: The guild id
        """
        return requests.get(
            url=self.API_BASE_URL + f'/channels/{channel_id}',
            headers={'Authorization': self.AUTHORIZATION}
        ).json()['guild_id']  # Get the guild id of the channel

    def file_upload_or_edit(self, path: str, file_key: str = None) -> dict[str, str]:
        if not file_key:
            guild_id = self.get_available_guild_id()
        else:
            guild_id = self.get_guild_id_by_channel_id(file_key.split(":")[0])
        file_size = os.path.getsize(path)
        rounded_file_size_megabytes = round(file_size / MEGABYTE, 2)
        # Check if the files is too big
        if file_size > 8 * MEGABYTE and self.get_boosts_level(guild_id) < 2:
            return abort(
                400, {
                    "message": f"The files is too big ({rounded_file_size_megabytes}MB)"
                               f" and the guild ({guild_id}) doesn't have the required boosts level (2)"
                               f" for upload more than 8MB files"
                }
            )
        elif file_size > 50 * MEGABYTE and self.get_boosts_level(guild_id) < 3:
            return abort(
                400, {
                    "message": f"The files is too big ({rounded_file_size_megabytes}MB)"
                               f" and the guild ({guild_id}) doesn't have the required boosts level (3)"
                               f" for upload more than 50MB files"
                }
            )
        elif file_size > 100 * MEGABYTE:
            return abort(
                400, {
                    "message": f"The files is too big ({rounded_file_size_megabytes}MB)"
                               f" for upload more than 100MB files"
                }
            )

        if file_key:
            self._file_edit(file_key=file_key, path=path)
            os.remove(path)
            return {'file_key': file_key}
        else:
            file_key = self._file_upload(path=path)
            os.remove(path)
            return file_key
