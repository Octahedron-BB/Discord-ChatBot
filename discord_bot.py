import os
import asyncio
import random
import discord
from dotenv import load_dotenv
from main import DiscordTwin
import config

os.environ['ANONYMIZED_TELEMETRY'] = 'False'
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_msg_time = {}  # channel_id: timestamp
        self.is_responding = {}   # channel_id: bool

    async def on_ready(self):
        print(f'✅ Successfully logged in as {self.user}')
        print(f'🎯 Allowed private chat IDs: {ALLOWED_PRIVATE_IDS}')
        print(f'📢 Will respond to @mentions in servers')
        if config.AUTO_REPLY_CHANNEL_ID:
            print(f'🤖 Auto-responding enabled in channel: {config.AUTO_REPLY_CHANNEL_ID}')
        print('='*40)

    async def on_message(self, message):
        # Ignore messages sent by the bot itself
        if message.author == self.user:
            return

        now = asyncio.get_event_loop().time()
        channel_id = message.channel.id
        
        # 2s-Absolute Refractory Period
        last_time = self.last_msg_time.get(channel_id, 0)
        if (now - last_time) < config.REFRACTORY_ABSOLUTE:
            # We still record the time of this message to extend the refractory period
            self.last_msg_time[channel_id] = now
            return
        
        # Record this message's time
        self.last_msg_time[channel_id] = now

        # Case 1: Specific Auto-Reply Channel
        is_auto_channel = (channel_id == config.AUTO_REPLY_CHANNEL_ID)
        
        # Case 2: Private Message
        is_private = isinstance(message.channel, discord.DMChannel) and message.author.id in ALLOWED_PRIVATE_IDS
        
        # Case 3: Mention in Server
        is_mention = message.guild and self.user.mentioned_in(message) and config.RESPOND_TO_MENTIONS

        should_reply = False
        trigger_text = message.content

        if is_private:
            should_reply = True
        elif is_mention:
            should_reply = True
            # Clean up mentions
            trigger_text = message.content.replace(f"<@{self.user.id}>", "").replace(f"<@!{self.user.id}>", "").strip()
        elif is_auto_channel:
            # Selective Reply (Probability check if bot is already responding)
            if self.is_responding.get(channel_id, False):
                if random.random() < config.CHANNEL_REPLY_PROBABILITY:
                    should_reply = True
            else:
                should_reply = True
        
        if should_reply and trigger_text:
            await self._process_message(message, trigger_text)
    
    async def _process_message(self, message, clean_text):
        """Process and respond to a message"""
        channel_id = message.channel.id
        self.is_responding[channel_id] = True
        
        try:
            # Fetch background context (10 messages before the current one)
            background_history = []
            async for msg in message.channel.history(limit=10, before=message):
                author = msg.author.display_name
                background_history.append(f"{author}: {msg.clean_content}")
            
            # History is fetched newest first, so we reverse it
            background_history.reverse()
            history_text = "\n".join(background_history)

            # Trigger Discord's native "typing..." animation
            async with message.channel.typing():
                # twin.respond now can handle history_text
                reply = await twin.respond(
                    clean_text, 
                    author_id=str(message.author.id), 
                    author_name=message.author.display_name,
                    background_history=history_text
                )
                
                # Human-like typing delay
                delay = random.uniform(config.AUTO_REPLY_DELAY_MIN, config.AUTO_REPLY_DELAY_MAX)
                print(f"⏳ [{message.channel}] Simulating typing: {delay:.1f}s")
                await asyncio.sleep(delay)
                
                # Send message back to Discord
                await message.channel.send(reply)
                print(f"📤 [{message.channel}] Replied: {reply}\n")
        finally:
            self.is_responding[channel_id] = False


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