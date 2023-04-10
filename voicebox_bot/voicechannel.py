import asyncio
import discord
from typing import Dict, Tuple, Optional

class VoiceClientManager:
    clients: Dict[int, discord.VoiceClient] = {}
    locks: Dict[discord.VoiceClient, asyncio.Lock] = {}
    interaction_channel_ids: Dict[discord.VoiceClient, int] = {}

    async def new_voice_client(self, guild_id: int, voice_channel: discord.VoiceChannel, interaction_channel_id: int) -> Tuple[discord.VoiceClient, asyncio.Lock] | None:
        voice_client = self.clients.get(guild_id) # type: discord.VoiceClient

        if voice_client is not None and voice_client.is_connected():
            return voice_client, self.locks[voice_client]

        if voice_client is not None:
            voice_client.cleanup()

        try:
            voice_client = await voice_channel.connect()
            if voice_client is None:
                return None
            print(f'connect to voice channel: {voice_channel.name} successful')

            self.register_voice_client(guild_id, voice_client, interaction_channel_id)
            return voice_client, self.locks[voice_client]
        except discord.ClientException as err:
            print(err)
            return voice_client, self.locks[voice_client]

    def get_voice_client(self, guild_id: int) -> Optional[Tuple[discord.VoiceClient, asyncio.Lock, int]]:
        voice_client = self.clients.get(guild_id)
        if voice_client is None:
            return None
        return voice_client, self.locks[voice_client], self.interaction_channel_ids[voice_client]

    def register_voice_client(self, guild_id, voice_client: discord.VoiceClient, interaction_channel_id: int):
        self.clients[guild_id] = voice_client
        self.locks[voice_client] = asyncio.Lock()
        self.interaction_channel_ids[voice_client] = interaction_channel_id

    def unregister_voice_client(self, guild_id) -> discord.VoiceClient | None:
        poped_client = self.clients.pop(guild_id)
        self.locks.pop(poped_client)
        return poped_client