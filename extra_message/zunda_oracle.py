from extra_message.extra_message import ExtraMessage
import discord
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

class ZundaOracleExtraMessage(ExtraMessage):
    llm: ChatOpenAI
    chain: LLMChain
    wake_word: str

    def __init__(self, wake_word: str, api_key: str) -> None:
        super().__init__()
        self.wake_word = wake_word
        self.llm = ChatOpenAI(temperature=0.7, openai_api_key=api_key)
        question_prompt = ChatPromptTemplate.from_messages([
                HumanMessagePromptTemplate(prompt = PromptTemplate(template=''
                    'あなたはずんだもんという名前のキャラクターを演じて質問に応答しなければなりません。ずんだもんはずんだの精霊です。ただし、返答する情報についてはキャラクターで制限する必要はありません。'
                    'ずんだもんはかならず語尾に「のだ」か「なのだ」をつけて喋ります。以下はずんだもんのセリフの例です。'
                    '「ボクはずんだもんなのだ！」「ずん子と一緒にずんだ餅を全国区のスイーツにする。それがずんだもんの野望なのだ！」'
                    '「かわいい精霊、ずんだもんにお任せなのだ！」「この動画には以下の要素が含まれているのだ。大丈夫なのだ？」「ずんだもんが手伝うのだ！」'
                    '以下は実際の質問文です。 {input}。', input_variables=['input']))
                ])
        self.chain = LLMChain(llm=self.llm, prompt=question_prompt)

    def is_supported(self, message: discord.Message) -> bool:
        return message.content.startswith(self.wake_word)

    def is_omit_long_text(self) -> bool:
        return False

    def is_send_as_text(self) -> bool:
        return True

    def is_consumed(self) -> bool:
        return True

    def get_extra_message(self, message: discord.Message) -> str:
        return self.chain.run(input=message.content[len(self.wake_word):])