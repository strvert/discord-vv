import discord
from discord import app_commands
from discord.channel import VoiceChannel
from discord.player import FFmpegPCMAudio
import asyncio
import aiofiles
import datetime
import env_token
import uuid
import os
import json
from extra_message.extra_message import ExtraMessageChain
from extra_message.ozanari_user import OzanariUserExtraMessage
from extra_message.zunda_oracle import ZundaOracleExtraMessage
from extra_message.url_omitted import URLOmittedExtraMessage
from extra_message.morphological_analysis import MorphologicalAnalysisExtraMessage

from voicevox.voicevox_client import VoiceVoxQuery, VoiceVoxSynthesis
from voicebox_bot.voicechannel import VoiceClientManager
from typing import Dict, Tuple, Optional

# https://discord.com/api/oauth2/authorize?client_id=1094263434276786217&permissions=3148800&scope=bot

# VoiceBoxで合成した音声をボイスチャットで再生するBot
# テキストを送信すると、そのテキストを音声に変換してボイスチャットに流すことができる

intents = discord.Intents.default()
intents.typing = False
intents.message_content = True
client = discord.Client(intents=intents)
command_tree = app_commands.CommandTree(client)

config = json.load(open("config.json", "r", encoding="utf-8")) # type: Dict
print(config)

extra_message_chain = ExtraMessageChain([
    URLOmittedExtraMessage(),
    OzanariUserExtraMessage(config),
    ZundaOracleExtraMessage("ねえずんだもん、", env_token.OPENAI_TOKEN),
    MorphologicalAnalysisExtraMessage("ずんだもん形態素解析して。")
])

def modify_message(message: discord.Message) -> Optional[Tuple[str, Optional[str]]]: # (voice_content, text_content)
    content = message.content

    extra = extra_message_chain.get_extra_message(message)
    if extra is not None:
        extra_content = extra[0].lower()
        is_omit_long_text = extra[1]
        is_send_as_text = extra[2]
        if not is_omit_long_text:
            return extra_content, extra_content if is_send_as_text else None
        else:
            content = extra_content

    # 40文字以上は省略
    limit_length = 40
    if len(content) > limit_length:
        return content[:limit_length] + "って長い！　詠唱破棄", content

    return None

# discord.Message から VoiceChannel を取得する
def get_voice_channel(message: discord.Message) -> VoiceChannel | None:
    if message.author.voice is None:
        return None
    return message.author.voice.channel


async def write_wav_file(file_name: str, data: bytes):
    async with aiofiles.open(file_name, "wb") as f:
        await f.write(data)
    return file_name

def generate_file_name():
    # UUIDを生成
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S") + f"_{str(uuid.uuid4())}.wav"

voice_clients = VoiceClientManager()

current_speaker_id = 3
def cache_speaker_list():
    global current_speaker_id
    current_speaker_id = 21

for define_extra_commands in extra_message_chain.get_extra_commands():
    command_tree.add_command(define_extra_commands)

# @command_tree.command(name="give-knowledge", description="ずんだもんに知識を授けます")

@command_tree.command(name="vv", description="discord vv をボイスチャンネルに招待します")
async def invite_voicevox(inter: discord.Interaction):
    voice_channel = inter.user.voice.channel
    voice_client = await voice_clients.new_voice_client(inter.guild_id, voice_channel, inter.channel_id)
    if voice_client is None:
        await inter.response.send_message("ボイスチャンネルに接続できませんでした", ephemeral=True)
        return
    await inter.response.send_message("よばれて飛び出てずんだもん ", ephemeral=False)

@command_tree.command(name="sync", description="discord vv のコマンドを同期します")
async def sync_commands(inter: discord.Interaction):
    await command_tree.sync()
    await inter.response.send_message("同期したのだ", ephemeral=False)

@command_tree.command(name="set-voice", description="discord vv の声を変更します")
async def set_voice_voicevox(inter: discord.Interaction, voice_id: str):
    global current_speaker_id
    current_speaker_id = int(voice_id)
    await inter.response.send_message(f"声を変更しました。{voice_id}", ephemeral=False)

async def on_message_handler(message: discord.Message):
    print(f"message: {message.content}")

    voice_client_result = voice_clients.get_voice_client(message.guild.id)
    voice_client, voice_client_lock, inter_channel_id = voice_client_result if voice_client_result is not None else (None, None, None)

    if voice_client is not None and inter_channel_id != message.channel.id:
        return

    modify_result = modify_message(message)
    modified_message, text_message = modify_result if modify_result is not None else (None, None)

    if modified_message is not None:
        print(f"extra: {modified_message}")
        voice_message = modified_message
    else:
        voice_message = message.content.lower()

    if text_message is not None:
        await message.channel.send(text_message)

    if voice_client is None:
        return

    query = VoiceVoxQuery(voice_message, current_speaker_id)
    query.set_speed(1.2)
    query_content = await query.execute()
    if query_content is None:
        return None

    synthesis = VoiceVoxSynthesis.from_query(query_content, current_speaker_id)
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


@client.event
async def on_ready():
    print(f"ログインしました: {client.user.name} (ID: {client.user.id})")
    await command_tree.sync()

client.run(env_token.DISCORD_TOKEN)