import discord
import os
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()

# Get credentials from the .env file
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
raw_channel_id = os.getenv('TARGET_CHANNEL_ID')

# --- Robust Error Checking ---
if not DISCORD_TOKEN:
    print("FATAL ERROR: 'DISCORD_TOKEN' is missing from your .env file or the file was not found.")
    exit()

TARGET_CHANNEL_ID = None
if raw_channel_id:
    try:
        TARGET_CHANNEL_ID = int(raw_channel_id)
    except ValueError:
        print(f"FATAL ERROR: 'TARGET_CHANNEL_ID' in your .env file is not a valid number. The value was: '{raw_channel_id}'")
        exit()
else:
    print("FATAL ERROR: 'TARGET_CHANNEL_ID' is missing from your .env file or the file was not found.")
    exit()

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    """Confirms the bot is connected and ready."""
    print(f'Discord Adapter: Logged in as {client.user}')

async def post_message(content, image_path=None):
    """A function that can be called to post a message to the target channel."""
    if not client.is_ready():
        print("Discord Adapter: Bot is not ready, cannot post message.")
        return False
        
    target_channel = client.get_channel(TARGET_CHANNEL_ID)
    if not target_channel:
        print(f"Discord Adapter: Could not find channel with ID {TARGET_CHANNEL_ID}")
        return False

    try:
        file_to_send = None
        if image_path and os.path.exists(image_path):
            file_to_send = discord.File(image_path)
        
        await target_channel.send(content=content, file=file_to_send)
        print(f"Discord Adapter: Successfully posted to #{target_channel.name}")
        return True
    except discord.Forbidden:
        print("Discord Adapter: Bot lacks permissions to post in the target channel.")
        return False
    except Exception as e:
        print(f"Discord Adapter: An unexpected error occurred: {e}")
        return False

def run_bot():
    """Starts the bot. This is called by the main engine."""
    client.run(DISCORD_TOKEN)

