import socket
import threading
from PIL import Image
import io
import google.generativeai as genai
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from transformers import AutoProcessor, BarkModel
import scipy
import numpy as np

load_dotenv(".env.local")

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

# Bark setup
processor = AutoProcessor.from_pretrained("suno/bark")
bark_model = BarkModel.from_pretrained("suno/bark")
voice_preset = "v2/en_speaker_6"

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
    response = model.generate_content([image, "Describe the image."])
    
    # Send text response
    await text_channel.send(response.text)
    
    # Generate speech with Bark
    inputs = processor(response.text, voice_preset=voice_preset)
    audio_array = bark_model.generate(**inputs)
    audio_array = audio_array.cpu().numpy().squeeze()
    
    # Save audio to file
    sample_rate = bark_model.generation_config.sample_rate
    scipy.io.wavfile.write("response.wav", rate=sample_rate, data=audio_array)
    
    # Play audio in voice channel
    if voice_channel.is_connected():
        voice_channel.play(discord.FFmpegPCMAudio("response.wav"))

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