import socket
import threading
from PIL import Image
import io
# import discord

## Discord bot setup
# intents = discord.Intents.default()
# bot = discord.Bot(intents=intents)

# Server setup
HOST = '127.0.0.1'  # Localhost
PORT = 65432        # Port to listen on

# Flag to control the server loop
server_running = True

def handle_client_connection(client_socket):
    try:
        while server_running:
            # Read the size of the incoming image first
            size_data = client_socket.recv(4)
            if not size_data:
                return
            
            # Convert size data to an integer (assuming 8 bytes for size)
            size = int.from_bytes(size_data, byteorder='big')
            print("Received image size:", size)

            # Now read the image data based on the reported size
            received_data = b""
            while len(received_data) < size:
                packet = client_socket.recv(4096)  # Adjust buffer size as needed
                if not packet:
                    break
                received_data += packet
            received_size = len(received_data)
            print(f"Received size: {received_size}")
            
            if received_size == size:
                # Assuming the data is an image in bytes
                image_data = io.BytesIO(received_data)
                image = Image.open(image_data)
                
                # Process the image (e.g., convert to grayscale)
                grayscale_image = image.convert('L')
                grayscale_image.show()  # Display for testing

                # Here you could send a message or image to a Discord channel
                # await bot_channel.send("Processed an image!")  # Example (inside a coroutine)
            else:
                print("Error: Incomplete image data received")
                print("Expected size:", size)
                print("Received size:", len(received_data))
        client_socket.close()
    except Exception as e:
        print(f"Error: {e}")
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
            client_handler = threading.Thread(
                target=handle_client_connection,
                args=(client_socket,)
            )
            client_handler.start()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server.close()

if __name__ == '__main__':
    try:
        start_server()
    except KeyboardInterrupt:
        print("Shutting down server...")
        server_running = False
    # # Running the server in a separate thread to avoid blocking the bot
    # server_thread = threading.Thread(target=start_server)
    # server_thread.start()

    # # Discord bot event
    # @bot.event
    # async def on_ready():
    #     print(f'Logged in as {bot.user}')

    # bot.run('YOUR_DISCORD_BOT_TOKEN')
