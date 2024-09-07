import socket
import threading
from PIL import Image
import io
import google.generativeai as genai
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
# from google.cloud import texttospeech

load_dotenv(".env.local")
FFMPEG_PATH = os.environ["FFMPEG_PATH"]

# Load system Prompt
with open('sysprompt.txt', encoding='utf8') as file_object:
    sysprompt = file_object.read()


# # Instantiates a client
# tts_client = texttospeech.TextToSpeechClient()
# # Build the voice request, select the language code ("en-US") and the ssml
# # voice gender ("neutral")
# voice = texttospeech.VoiceSelectionParams(
#     language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
# )
# # Select the type of audio file you want returned
# audio_config = texttospeech.AudioConfig(
#     audio_encoding=texttospeech.AudioEncoding.MP3
# )

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Gemini setup
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 1024,
}
model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)

# Server setup
HOST = '127.0.0.1'
PORT = 65432
server_running = True

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("You need to be in a voice channel to use this command.")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("I'm not in a voice channel.")

async def process_image_and_speak(image_data, text_channel, voice_channel):
    # Process image with Gemini
    image = Image.open(io.BytesIO(image_data))
    response = model.generate_content([image, sysprompt])

    # Send text response
    await text_channel.send(response.text)

    # # Generate speech with Google TTS
    # synthesis_input = texttospeech.SynthesisInput(text=response.text)
    # tts_response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    #
    # # Play audio in voice channel
    # voice_client = discord.utils.get(bot.voice_clients, channel=voice_channel)
    # if voice_client and voice_client.is_connected():
    #     if os.path.exists(FFMPEG_PATH):
    #         audio_source = io.BytesIO(tts_response.audio_content)
    #         voice_client.play(discord.FFmpegPCMAudio(audio_source, pipe=True, executable=FFMPEG_PATH))
    #     else:
    #         await text_channel.send(f"FFmpeg not found at {FFMPEG_PATH}. Please check the path.")
    #         return
    # else:
    #     await text_channel.send("Bot is not connected to the voice channel. Use !join to connect the bot.")

def handle_client_connection(client_socket):
    try:
        while server_running:
            size_data = client_socket.recv(4)
            if not size_data:
                return
            
            size = int.from_bytes(size_data, byteorder='big')
            received_data = b""
            while len(received_data) < size:
                packet = client_socket.recv(4096)
                if not packet:
                    break
                received_data += packet
            
            if len(received_data) == size:
                text_channel = bot.get_channel(int(os.environ["TEXT_CHANNEL_ID"]))
                voice_channel = bot.get_channel(int(os.environ["VOICE_CHANNEL_ID"]))
                print(voice_channel)
                bot.loop.create_task(process_image_and_speak(received_data, text_channel, voice_channel))
            else:
                print("Error: Incomplete image data received")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server listening on {HOST}:{PORT}")

    try:
        while server_running:
            client_socket, addr = server.accept()
            print(f"Accepted connection from {addr}")
            client_handler = threading.Thread(target=handle_client_connection, args=(client_socket,))
            client_handler.start()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server.close()

if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server)
    server_thread.start()
    bot.run(os.environ["DISCORD_BOT_TOKEN"])