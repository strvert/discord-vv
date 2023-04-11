import discord
from abc import ABCMeta, abstractmethod
from typing import Tuple, Optional, Callable, List
from discord import app_commands


class ExtraMessage(metaclass=ABCMeta):
    """
    特殊メッセージ処理を定義する基底クラス
    """

    @abstractmethod
    def is_supported(self, message: discord.Message) -> bool:
        """
        対応するメッセージか
        """

    @abstractmethod
    def is_omit_long_text(self) -> bool:
        """
        長文省略処理の対象とするか
        """
    @abstractmethod
    def is_send_as_text(self) -> bool:
        """
        テキストとして送信するか
        """

    @abstractmethod
    def is_consumed(self) -> bool:
        """
        メッセージを消費するか
        """

    @abstractmethod
    def get_extra_message(self, message: discord.Message) -> str:
        """
        特殊メッセージを取得する
        """

    @abstractmethod
    def get_extra_commands(self) -> Optional[List[app_commands.Command]]:
        """
        ExtraMessage特有のコマンドを取得する
        """


class ExtraMessageChain():
    """
    ExtraMessage のチェーン
    """
    extra_messages: list[ExtraMessage]

    def __init__(self, extra_messages: list[ExtraMessage]):
        self.extra_messages = extra_messages

    def add_extra_message(self, extra_message: ExtraMessage):
        self.extra_messages.append(extra_message)

    def get_extra_message(self, message: discord.Message) -> Optional[Tuple[str, bool, bool]]:
        """
        特殊メッセージを取得する
        """
        is_extra = False
        is_omit_long_text = False
        is_send_as_text = False
        result_message = message
        for extra_message in self.extra_messages:
            if extra_message.is_supported(result_message):
                result_message = extra_message.get_extra_message(result_message)
                is_omit_long_text = is_omit_long_text or extra_message.is_omit_long_text()
                is_send_as_text = extra_message.is_send_as_text()
                is_extra = True
                if extra_message.is_consumed():
                    break

        if is_extra:
            return result_message, is_omit_long_text, is_send_as_text

        return None
    
    def get_extra_commands(self) -> list[app_commands.Command]:
        """
        特殊メッセージを取得するコマンドを取得する
        """
        commands: List[app_commands.Command] = []
        for extra_message in self.extra_messages:
            command = extra_message.get_extra_commands()
            if command is not None:
                commands.extend(command)
        return commands