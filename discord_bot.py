import os
import asyncio
import random
import discord
from dotenv import load_dotenv
from main import DiscordTwin
import config

# 1. Load environment variables from config
load_dotenv()
API_KEY = config.API_KEY
DISCORD_TOKEN = config.DISCORD_BOT_TOKEN
ALLOWED_PRIVATE_IDS = config.ALLOWED_PRIVATE_IDS
TARGET_USER_NAME = config.TARGET_USER_NAME
DEFAULT_FRIEND_NAME = config.DEFAULT_FRIEND_NAME

if not DISCORD_TOKEN or not API_KEY or not ALLOWED_PRIVATE_IDS:
    print("❌ Missing environment variables! Please check if .env file has API_KEY, DISCORD_BOT_TOKEN, and ALLOWED_PRIVATE_IDS set")
    exit()

# 2. Initialize digital twin brain
print("🧠 Awakening EchoMirror brain...")
# The names here can correspond to the Persona set in your config
twin = DiscordTwin(api_key=API_KEY, target_user=TARGET_USER_NAME, friend_name=DEFAULT_FRIEND_NAME)

# 3. Set Discord bot permissions
intents = discord.Intents.default()
intents.message_content = True  # Must be enabled, otherwise the bot cannot see message content

class EchoMirrorBot(discord.Client):
    async def on_ready(self):
        print(f'✅ Successfully logged in as {self.user}')
        print(f'🎯 Allowed private chat IDs: {ALLOWED_PRIVATE_IDS}')
        print(f'📢 Will respond to @mentions in servers')
        print('='*40)

    async def on_message(self, message):
        # Ignore messages sent by the bot itself
        if message.author == self.user:
            return

        # Check if it's a private message from an allowed user
        if isinstance(message.channel, discord.DMChannel) and message.author.id in ALLOWED_PRIVATE_IDS:
            print(f"📥 Received DM from {message.author.name}: {message.content}")
            await self._process_message(message)
        
        # Check if bot is mentioned in a server message
        elif message.guild and self.user.mentioned_in(message) and config.RESPOND_TO_MENTIONS:
            # Remove the mention from the content to get the actual message
            clean_content = message.content.replace(f"<@{self.user.id}>", "").replace(f"<@!{self.user.id}>", "").strip()
            if clean_content:
                print(f"📥 Received mention from {message.author.name} in #{message.channel.name}: {clean_content}")
                # Replace the message content for processing
                message.content = clean_content
                await self._process_message(message)
    
    async def _process_message(self, message):
        """Process and respond to a message"""
        # Trigger Discord's native "typing..." animation
        async with message.channel.typing():
            
            # Key optimization: since twin.respond is a synchronous function
            # Use asyncio.to_thread to run it in the background to avoid blocking the Discord bot's connection
            reply = await asyncio.to_thread(twin.respond, message.content)
            
            # Human-like typing delay (using asyncio.sleep)
            delay = random.uniform(config.AUTO_REPLY_DELAY_MIN, config.AUTO_REPLY_DELAY_MAX)
            print(f"⏳ Simulating typing, waiting {delay:.1f} seconds...")
            await asyncio.sleep(delay)
            
            # Send message back to Discord
            await message.channel.send(reply)
            print(f"📤 Replied: {reply}\n")


# 4. Start the bot
print("🚀 Starting Discord bot...")
try:
    # Try without proxy first
    client = EchoMirrorBot(intents=intents)
    client.run(DISCORD_TOKEN)
except Exception as e:
    print(f"❌ Failed to connect without proxy: {e}")
    print("🔄 Retrying with proxy...")
    try:
        # Retry with proxy
        client = EchoMirrorBot(intents=intents, proxy="http://127.0.0.1:7891")
        client.run(DISCORD_TOKEN)
    except Exception as e2:
        print(f"❌ Failed to connect with proxy: {e2}")
        print("💥 Unable to start the bot. Please check your network or proxy settings.")
        exit(1)