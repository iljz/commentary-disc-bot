from discord.ext import commands
import discord

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print('Bot is ready')
    #channel = bot.get_channel(CHANNEL_ID)
    #await channel.send('Hello World!')

#bot.run(BOT_TOKEN)
from transformers import AutoProcessor, BarkModel
import scipy


processor = AutoProcessor.from_pretrained("suno/bark")
model = BarkModel.from_pretrained("suno/bark")

voice_preset = "v2/en_speaker_6"

inputs = processor("Hello, my dog is cute", voice_preset=voice_preset)

audio_array = model.generate(**inputs)
audio_array = audio_array.cpu().numpy().squeeze()

sample_rate = model.generation_config.sample_rate
scipy.io.wavfile.write("bark_out.wav", rate=sample_rate, data=audio_array)