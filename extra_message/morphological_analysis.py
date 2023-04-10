from extra_message.extra_message import ExtraMessage
import discord
import spacy
import re
from typing import List

wake_word = ""
en_nlp = spacy.load("en_core_web_sm")

class MorphologicalAnalysisExtraMessage(ExtraMessage):
    wake_word: str

    def __init__(self, wake_word: str) -> None:
        self.wake_word = wake_word

    def is_supported(self, message: discord.Message) -> bool:
        return message.content.startswith(self.wake_word)

    def is_omit_long_text(self) -> bool:
        return True

    def is_consumed(self) -> bool:
        return True

    def is_send_as_text(self) -> bool:
        return True

    def get_extra_message(self, message: discord.Message) -> str:
        target_text = message.content[len(self.wake_word):].strip()
        doc = en_nlp(target_text)

        tokens: List[str] = []
        for token in doc:
            if any(c.isupper() for c in token.text[1:]):  # Check if there's any uppercase character in the middle of the word
                split_words = self.split_camel_case(token.text)
                tokens.append(f"{str(split_words)}: {token.pos_}")
            else:
                tokens.append(f"[\"{token.text}\"]: {token.pos_}")

        return str(tokens)

    @staticmethod
    def split_camel_case(word) -> str:
        splited = re.sub('([A-Z][a-z]+)', r' \1', re.sub('([A-Z]+)', r' \1', word)) # type: str
        return splited.split()