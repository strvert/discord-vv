from extra_message.extra_message import ExtraMessage
import discord
import random
from typing import Dict


class OzanariUserExtraMessage(ExtraMessage):
    ozanari_users: Dict[int, str] = {}
    percentage: int

    def __init__(self, config: Dict):
        ozanari_conf = config.get('extra_message').get("ozanari")
        users_config = ozanari_conf.get("users")

        for user in users_config:
            self.ozanari_users[int(user["id"])] = user["name"]

        self.percentage = ozanari_conf.get("percentage")
        print(self.ozanari_users)
        print(self.percentage)

    def is_supported(self, message: discord.Message) -> bool:
        user = message.author # type : discord.User
        ozanari_user = self.ozanari_users.get(user.id)

        if ozanari_user is not None:
            # 30%の確率で返す
            return random.randint(0, 100) < self.percentage
        return False

    def is_omit_long_text(self) -> bool:
        return False

    def is_send_as_text(self) -> bool:
        return True

    def is_consumed(self):
        return True

    def get_extra_message(self, message: discord.Message) -> str:
        ozanari_user = self.ozanari_users.get(message.author.id)
        if ozanari_user is None:
            return message.content
        return f"{ozanari_user}、お前のことは知らない"

    def get_extra_commands(self):
        return None