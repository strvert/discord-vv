from extra_message.extra_message import ExtraMessage
import discord
import random
from typing import Dict


class OzanariUserExtraMessage(ExtraMessage):
    ozanari_users: Dict[int, str]
    percentage: int

    def __init__(self, ozanari_users: Dict[int, str], percentage: int):
        self.ozanari_users = ozanari_users
        self.percentage = percentage

    def is_supported(self, message: discord.Message) -> bool:
        user = message.author # type : discord.User
        ozanari_user = self.ozanari_users.get(user.id)

        if ozanari_user is not None:
            # 30%の確率で返す
            return random.randint(0, 100) < self.percentage
        return False

    def is_omit_long_text(self) -> bool:
        return False

    def is_consumed(self):
        return True

    def get_extra_message(self, message: discord.Message) -> str:
        ozanari_user = self.ozanari_users.get(message.author.id)
        if ozanari_user is None:
            return message.content
        return f"{ozanari_user}、お前のことは知らない"