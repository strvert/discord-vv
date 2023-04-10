import aiohttp
import json

class VoiceVoxEndpoint:
    base_url = "http://localhost:50021"
    audio_query_endpoint = "/audio_query"
    synthesis_endpoint = "/synthesis"

    @staticmethod
    def get_base_url():
        return VoiceVoxEndpoint.base_url

    @staticmethod
    def get_audio_query_url():
        return VoiceVoxEndpoint.get_base_url() + VoiceVoxEndpoint.audio_query_endpoint

    @staticmethod
    def get_synthesize_url():
        return VoiceVoxEndpoint.get_base_url() + VoiceVoxEndpoint.synthesis_endpoint


class VoiceVoxQuery:
    speaker_id: int
    text: str
    pitch: float = 1.0
    speed: float = 1.0
    intnation: float = 1.0
    pre_phoneme_length: float = 0
    post_phoneme_length: float = 0

    acceleration_count: int = 15
    acceleration_scale: float = 1.2

    def __init__(self, text, speaker_id):
        self.text = text
        self.speaker_id = speaker_id

    async def execute(self) -> str | None:
        query_url = self.build_query_url()

        # リクエスト実行
        async with aiohttp.ClientSession() as session:
            async with session.post(query_url, headers={"Content-Type": "application/json"}) as response:
                if response.status != 200:
                    print(f"status code: {response.status}")
                    print(f"content: {response.content}")
                    return None

                # jsonからdictに変換
                query_content = await response.json()

                query_content['prePhonemeLength'] = self.pre_phoneme_length
                query_content['postPhonemeLength'] = self.post_phoneme_length

                query_content['speedScale'] = self.calc_speed()
                # query_content['pitchScale'] = self.pitch
                # query_content['intonationScale'] = self.intnation

                query = json.dumps(query_content, ensure_ascii=False).encode('utf-8')
                return query

    def calc_speed(self):
        return self.speed if len(self.text) < self.acceleration_count else self.speed * self.acceleration_scale

    def set_acceleration_count(self, count: int):
        self.acceleration_count = count

    def set_pitch(self, pitch: float):
        self.pitch = pitch

    def set_speed(self, speed: float):
        self.speed = speed

    def build_query_url(self) -> str:
        query_base_url = VoiceVoxEndpoint.get_audio_query_url()
        query_url = f"{query_base_url}?text={self.text}&speaker={self.speaker_id}"
        return query_url


class VoiceVoxSynthesis:
    query_content: str
    speaker_id: int

    def __init__(self, speaker_id) -> None:
        self.speaker_id = speaker_id
        self.query_content = ''

    async def execute(self) -> bytes | None:
        synthesis_url = self.build_synthesis_url()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                synthesis_url,
                headers={"Content-Type": "application/json"},
                data=self.query_content
            ) as response:
                if response.status != 200:
                    print(f"status code: {response.status}")
                    print(f"content: {await response.text()}")
                    return None
                return await response.read()

    def build_synthesis_url(self) -> str:
        synthesis_base_url = VoiceVoxEndpoint.get_synthesize_url()
        synthesis_url = f"{synthesis_base_url}?speaker={self.speaker_id}"
        return synthesis_url

    def set_query(self, query_content: str):
        self.query_content = query_content

    @staticmethod
    def from_query(query_content: str, speaker_id: int):
        synthesis = VoiceVoxSynthesis(speaker_id)
        synthesis.set_query(query_content)
        return synthesis
