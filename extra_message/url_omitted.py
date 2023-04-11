import discord
from extra_message.extra_message import ExtraMessage

class URLOmittedExtraMessage(ExtraMessage):
    def is_supported(self, message: discord.Message) -> bool:
        return message.content.startswith("http")

    def is_omit_long_text(self) -> bool:
        return False

    def is_send_as_text(self) -> bool:
        return False

    def is_consumed(self) -> bool:
        return True

    def get_extra_message(self, _: discord.Message) -> str:
        return "URL省略"

    def get_extra_commands(self):
        return None