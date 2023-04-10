import discord
from discord.channel import VoiceChannel
from discord.player import FFmpegPCMAudio
import asyncio
import aiofiles
import datetime
import env_token
import uuid
import os
from extra_message.extra_message import ExtraMessageChain
from extra_message.ozanari_user import OzanariUserExtraMessage
from extra_message.zunda_oracle import ZundaOracleExtraMessage
from extra_message.url_omitted import URLOmittedExtraMessage

from voicevox.voicevox_client import VoiceVoxQuery, VoiceVoxSynthesis
from voicebox_bot.voicechannel import VoiceClientManager
from typing import Callable, Dict, Tuple

# https://discord.com/api/oauth2/authorize?client_id=1094263434276786217&permissions=3148800&scope=bot

# VoiceBoxで合成した音声をボイスチャットで再生するBot
# テキストを送信すると、そのテキストを音声に変換してボイスチャットに流すことができる

intents = discord.Intents.default()
intents.typing = False
intents.message_content = True
client = discord.Client(intents=intents)

extra_message_chain = ExtraMessageChain([
    URLOmittedExtraMessage(),
    OzanariUserExtraMessage({705984080109633556: "ろくろ"}, 30),
    ZundaOracleExtraMessage("ねえずんだもん、", env_token.OPENAI_TOKEN)
])

def modify_message(message: discord.Message) -> str | None:
    content = message.content

    extra = extra_message_chain.get_extra_message(message) 
    if extra is not None:
        extra_content = extra[0].lower()
        is_omit_long_text = extra[1]
        if not is_omit_long_text:
            return extra_content
        else:
            content = extra_content

    # 40文字以上は省略
    limit_length = 40
    if len(content) > limit_length:
        return content[:limit_length] + "って長い！　詠唱破棄"

    return None

# discord.Message から VoiceChannel を取得する
def get_voice_channel(message: discord.Message) -> VoiceChannel | None:
    if message.author.voice is None:
        return None
    return message.author.voice.channel


@client.event
async def on_ready():
    print(f"ログインしました: {client.user.name} (ID: {client.user.id})")


async def write_wav_file(file_name: str, data: bytes):
    async with aiofiles.open(file_name, "wb") as f:
        await f.write(data)
    return file_name

def generate_file_name():
    # UUIDを生成
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S") + f"_{str(uuid.uuid4())}.wav"

voice_clients = VoiceClientManager()

async def on_message_handler(message: discord.Message):
    voice_channel = get_voice_channel(message)
    if voice_channel is None:
        return
    print(f"message: {message.content}")

    modified_message = modify_message(message)
    if modified_message is not None:
        print(f"extra: {modified_message}")
        voice_message = modified_message
    else:
        voice_message = message.content.lower()

    voice_client, voice_client_lock = await voice_clients.new_voice_client(message.guild.id, voice_channel)
    if voice_client is None:
        return

    speaker_id = 3

    query = VoiceVoxQuery(voice_message, speaker_id)
    query.set_speed(1.0)
    query_content = await query.execute()
    if query_content is None:
        return None

    synthesis = VoiceVoxSynthesis.from_query(query_content, speaker_id)
    wav_bytes = await synthesis.execute()
    if wav_bytes is None:
        return

    async def play_audio():
        file_path = await write_wav_file(f"output/{generate_file_name()}", wav_bytes)
        pcm_audio = FFmpegPCMAudio(file_path)

        async with voice_client_lock:
            voice_client.play(pcm_audio)
            while voice_client.is_playing():
                await asyncio.sleep(0.1)
            os.remove(file_path)

    await play_audio()

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    asyncio.create_task(on_message_handler(message))

client.run(env_token.DISCORD_TOKEN)