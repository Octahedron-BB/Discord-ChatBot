import os
import re
import asyncio
import random
from datetime import datetime, timezone
import discord
from dotenv import load_dotenv
from main import DiscordTwin
from vision import get_visual_description, fetch_twitter_metadata, fetch_instagram_metadata
import config

os.environ['ANONYMIZED_TELEMETRY'] = 'False'

# 1. Load environment variables
load_dotenv()
DISCORD_TOKEN = config.DISCORD_BOT_TOKEN
ALLOWED_PRIVATE_IDS = config.ALLOWED_PRIVATE_IDS
TARGET_USER_NAME = config.TARGET_USER_NAME
DEFAULT_FRIEND_NAME = config.DEFAULT_FRIEND_NAME
LLM_PROVIDER = getattr(config, 'LLM_PROVIDER', 'deepseek')

# Validate essential keys
if not DISCORD_TOKEN:
    print("❌ Missing DISCORD_BOT_TOKEN! Please check your .env file.")
    exit(1)

if LLM_PROVIDER == 'deepseek' and not config.DEEPSEEK_API_KEY:
    print("⚠️ DEEPSEEK_API_KEY is not set in .env! (LLM_PROVIDER is 'deepseek')")

if LLM_PROVIDER == 'gemini' and not config.GEMINI_API_KEY:
    print("⚠️ DISCORD_AI_API_KEY / GEMINI_API_KEY is not set in .env! (LLM_PROVIDER is 'gemini')")

# Helper function to extract Discord Embeds from link
async def extract_content_with_embeds(message, raw_text, brain=None):
    """
    Extracts text and Discord link preview (Embeds) if URLs are present.
    Specialized high-fidelity resolution for Twitter/X URLs (videos & images).
    For general URLs, inspects Discord embeds, companion bot embeds, and media attachments.
    """
    has_url = bool(re.search(r'https?://\S+', raw_text))
    if not has_url:
        return raw_text

    # 1. Specialized Twitter / X Resolver
    # In Discord, companion bots often split tweets with video into multiple messages,
    # or Discord's crawler misses video thumbnails or gets blocked by 18+ warnings.
    # fxtwitter extracts author, text, photos, and video thumbnails directly and cleanly.
    twitter_match = re.search(r'https?://(?:x|twitter)\.com/[a-zA-Z0-9_]+/status/\d+', raw_text)
    if twitter_match and brain:
        tweet_url = twitter_match.group(0)
        print(f"🐦 [Twitter] Detected Tweet URL: {tweet_url}, fetching rich metadata...")
        tweet_data = await fetch_twitter_metadata(tweet_url)
        if tweet_data:
            parts = []
            if tweet_data.get("author"):
                parts.append(f"作者: {tweet_data['author']}")
            if tweet_data.get("text"):
                desc = tweet_data['text'].strip().replace('\n', ' ')
                if len(desc) > 120:
                    desc = desc[:120] + "..."
                if desc:
                    parts.append(f"内容: {desc}")

            media_urls = tweet_data.get("media_urls", [])
            if media_urls:
                try:
                    print(f"🖼️ [Twitter Media] Found media preview URL: {media_urls[0][:70]}...")
                    img_desc = await get_visual_description(brain, media_urls[0])
                    if img_desc:
                        parts.append(f"画面预览: {img_desc}")
                except Exception as e:
                    print(f"⚠️ [Twitter Vision] Error: {e}")

            if parts:
                detail = " | ".join(parts)
                text_without_urls = re.sub(r'https?://\S+', '[Shared Link]', raw_text).strip()
                if text_without_urls and text_without_urls != '[Shared Link]':
                    enriched = f"{text_without_urls}\n[分享链接预览]:\n[{detail}]"
                else:
                    enriched = f"[分享链接预览]:\n[{detail}]"
                print(f"🔗 [Twitter Resolved] -> {detail}")
                return enriched

    # 2. Specialized Instagram Resolver
    ig_match = re.search(r'https?://(?:www\.)?(?:instagram\.com|instagr\.am)/(?:p|reel|reels|tv|share/(?:p|reel))/[a-zA-Z0-9_-]+', raw_text)
    if ig_match and brain:
        ig_url = ig_match.group(0)
        print(f"📷 [Instagram] Detected Instagram URL: {ig_url}, fetching rich metadata...")
        ig_data = await fetch_instagram_metadata(ig_url)
        if ig_data:
            parts = []
            if ig_data.get("author"):
                parts.append(f"作者/来源: {ig_data['author']}")
            if ig_data.get("text"):
                desc = ig_data['text'].strip().replace('\n', ' ')
                if len(desc) > 120:
                    desc = desc[:120] + "..."
                if desc:
                    parts.append(f"配文内容: {desc}")

            media_urls = ig_data.get("media_urls", [])
            if media_urls:
                try:
                    print(f"🖼️ [Instagram Media] Found media preview URL: {media_urls[0][:70]}...")
                    img_desc = await get_visual_description(brain, media_urls[0])
                    if img_desc:
                        parts.append(f"画面预览: {img_desc}")
                except Exception as e:
                    print(f"⚠️ [Instagram Vision] Error: {e}")

            if parts:
                detail = " | ".join(parts)
                text_without_urls = re.sub(r'https?://\S+', '[Shared Link]', raw_text).strip()
                if text_without_urls and text_without_urls != '[Shared Link]':
                    enriched = f"{text_without_urls}\n[分享链接预览]:\n[{detail}]"
                else:
                    enriched = f"[分享链接预览]:\n[{detail}]"
                print(f"🔗 [Instagram Resolved] -> {detail}")
                return enriched

    # 3. General URL handling (Discord Native Embeds & Companion Bots like ermiana)
    embeds_to_process = list(message.embeds)
    companion_images = []

    # If Discord crawler or companion bot has not posted embeds yet, wait and poll up to 3.2 seconds
    if not embeds_to_process:
        print("🔗 Link detected in message, waiting for Discord Embed / Companion bot unfurl...")
        for attempt in range(4):
            await asyncio.sleep(0.8)
            try:
                refetched = await message.channel.fetch_message(message.id)
                if refetched.embeds:
                    embeds_to_process = list(refetched.embeds)
                    break
            except Exception:
                pass

            try:
                # Inspect recent companion bot messages
                async for follow_up in message.channel.history(limit=5, after=message):
                    if follow_up.author.bot:
                        if follow_up.embeds:
                            for eb in follow_up.embeds:
                                if eb not in embeds_to_process:
                                    embeds_to_process.append(eb)
                        if follow_up.attachments:
                            for att in follow_up.attachments:
                                if att not in companion_images:
                                    companion_images.append(att)
            except Exception as e:
                print(f"⚠️ [Embed Bot Search] Error: {e}")

            if embeds_to_process or companion_images:
                break

    embed_details = []
    for eb in embeds_to_process:
        parts = []
        if eb.provider and eb.provider.name:
            parts.append(f"平台: {eb.provider.name}")
        if eb.title:
            parts.append(f"标题: {eb.title}")
        if eb.author and eb.author.name:
            parts.append(f"作者: {eb.author.name}")
        if eb.description:
            desc = eb.description.strip().replace('\n', ' ')
            if len(desc) > 120:
                desc = desc[:120] + "..."
            parts.append(f"简介: {desc}")

        # Check for media thumbnail or image in the embed (e.g. YouTube thumbnail, Tenor/Giphy GIF, video cover)
        img_url = (eb.image.url if eb.image and eb.image.url else None) or \
                  (eb.thumbnail.url if eb.thumbnail and eb.thumbnail.url else None)
        if img_url and brain:
            try:
                img_desc = await get_visual_description(brain, img_url)
                if img_desc:
                    parts.append(f"画面预览: {img_desc}")
            except Exception as e:
                print(f"⚠️ [Embed Vision] Error: {e}")

        if parts:
            embed_details.append(" | ".join(parts))

    # Process companion bot image attachments if any
    for att in companion_images:
        is_img = (att.content_type and att.content_type.startswith("image/")) or \
                 any(att.filename.lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.webp', '.gif'))
        if is_img and brain:
            try:
                img_bytes = await att.read()
                img_desc = await get_visual_description(brain, img_bytes, filename=att.filename)
                if img_desc:
                    embed_details.append(f"附图画面: {img_desc}")
            except Exception as e:
                print(f"⚠️ [Companion Bot Image Vision] Error: {e}")

    # Replace raw URL in text with [Shared Link]
    text_without_urls = re.sub(r'https?://\S+', '[Shared Link]', raw_text).strip()

    if embed_details:
        embed_block = "\n".join([f"[{detail}]" for detail in embed_details])
        if text_without_urls and text_without_urls != '[Shared Link]':
            enriched = f"{text_without_urls}\n[分享链接预览]:\n{embed_block}"
        else:
            enriched = f"[分享链接预览]:\n{embed_block}"
        print(f"🔗 [Embed Extracted] -> {embed_details}")
        return enriched

    return text_without_urls if text_without_urls else "[Shared Link]"

def is_standalone_emoji(text: str) -> bool:
    """Check if a line contains only emojis or symbols."""
    s = text.strip()
    if not s or len(s) > 6:
        return False
    emoji_pattern = re.compile(r'^[\U00010000-\U0010ffff\u2600-\u27bf\ufe0f\u200d\u203c-\u2049\u2139\u2194-\u21aa\u231a-\u23fa]+$')
    return bool(emoji_pattern.match(s))

# 2. Initialize digital twin brain
print(f"🧠 Awakening EchoMirror brain (Provider: {LLM_PROVIDER.upper()}, Target: {TARGET_USER_NAME})...")
twin = DiscordTwin(target_user=TARGET_USER_NAME, friend_name=DEFAULT_FRIEND_NAME)

# 3. Set Discord bot permissions
intents = discord.Intents.default()
intents.message_content = True

class EchoMirrorBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_msg_time = {}  # channel_id: timestamp
        self.is_responding = {}   # channel_id: bool
        self.proactive_task = None

    async def on_ready(self):
        print(f'✅ Successfully logged in as {self.user}')
        print(f'🎯 Allowed private chat IDs: {ALLOWED_PRIVATE_IDS}')
        print(f'📢 Will respond to @mentions in servers')
        if config.AUTO_REPLY_CHANNEL_ID:
            print(f'🤖 Auto-responding enabled in channel: {config.AUTO_REPLY_CHANNEL_ID}')
            # Start background task for proactive group messaging
            if self.proactive_task is None or self.proactive_task.done():
                self.proactive_task = asyncio.create_task(self.proactive_group_check_loop())
        else:
            print('ℹ️ No AUTO_REPLY_CHANNEL_ID configured. Group proactive messaging is disabled.')
        print('='*40)

    async def close(self):
        if self.proactive_task and not self.proactive_task.done():
            self.proactive_task.cancel()
        await super().close()

    async def proactive_group_check_loop(self):
        """Background loop: Periodically check if the configured group channel has been idle and initiate conversation."""
        await self.wait_until_ready()
        channel_id = config.AUTO_REPLY_CHANNEL_ID
        check_interval = getattr(config, 'PROACTIVE_CHECK_INTERVAL', 900)
        idle_threshold_hours = getattr(config, 'PROACTIVE_IDLE_TIME', 24.0)

        print(f"⏰ [Proactive] Group monitor running for channel ID: {channel_id}")
        print(f"   Idle Threshold: {idle_threshold_hours}h | Check Interval: {check_interval}s")

        while not self.is_closed():
            try:
                await asyncio.sleep(check_interval)

                channel = self.get_channel(channel_id)
                if not channel:
                    try:
                        channel = await self.fetch_channel(channel_id)
                    except Exception as e:
                        print(f"⚠️ [Proactive] Failed to fetch channel {channel_id}: {e}")
                        continue

                # Find the timestamp of the latest message in the channel
                last_message = None
                async for msg in channel.history(limit=1):
                    last_message = msg
                    break

                if not last_message:
                    print("ℹ️ [Proactive] Channel has no previous messages. Skipping.")
                    continue

                now_utc = datetime.now(timezone.utc)
                idle_seconds = (now_utc - last_message.created_at).total_seconds()
                idle_hours = idle_seconds / 3600.0

                channel_name = getattr(channel, 'name', f"channel-{channel_id}")

                if idle_hours >= idle_threshold_hours:
                    print(f"🚨 [Proactive] #{channel_name} idle for {idle_hours:.2f}h >= {idle_threshold_hours}h threshold. Generating proactive message...")
                    
                    proactive_text = await twin.generate_group_proactive_message(channel_name=channel_name)
                    if proactive_text:
                        async with channel.typing():
                            delay = random.uniform(config.AUTO_REPLY_DELAY_MIN, config.AUTO_REPLY_DELAY_MAX)
                            print(f"⏳ [Proactive] Simulating typing delay: {delay:.1f}s")
                            await asyncio.sleep(delay)
                            await channel.send(proactive_text)
                            print(f"📤 [Proactive] Sent to #{channel_name}: {proactive_text}\n")
                            twin.last_interaction_time = datetime.now()
                else:
                    # Debug log periodically
                    pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ [Proactive] Error in check loop: {e}")

    def get_help_message(self) -> str:
        """Generate comprehensive command help manual."""
        debug_status = "🟢 开启" if getattr(config, 'DEBUG_MODE', False) else "🔴 关闭"
        provider_name = "Google Gemini" if twin.brain.provider == 'gemini' else "DeepSeek"
        return (
            "📖 **Bibi Chat Bot 指令手册**\n\n"
            f"当前运行状态: `{provider_name}` (`{twin.brain.model_id}`) | 调试模式: {debug_status}\n\n"
            "⚙️ **模型管理 (`!model`)**\n"
            "• `!model` : 查看当前模型配置与连接状态\n"
            "• `!model list` : 查看支持的所有模型清单（DeepSeek / Gemini）\n"
            "• `!model <模型名称>` : 实时无缝切换模型（例如：`!model gemini-3.8-flash` 或 `!model deepseek-chat`）\n"
            "• `!model deepseek` / `!model gemini` : 快捷切换服务商平台\n\n"
            "🛠️ **调试模式 (`!debug`)**\n"
            "• `!debug` : 快捷反转调试模式开关\n"
            "• `!debug on` : 开启调试模式（Bot 发言前会附带其解析到的文字、链接及图片内容）\n"
            "• `!debug off` : 关闭调试模式（恢复纯净对话输出）\n\n"
            "❓ **系统指令 (`!help`)**\n"
            "• `!help` : 呼出本指令手册\n\n"
            "💡 *说明：输入指令时不会触发角色日常闲聊。所有设置更改均会自动保存至本地 `.env`。*"
        )

    async def _handle_bot_command(self, message, raw_cmd: str):
        """Handle administrator and utility commands (!model, !debug, !help)"""
        parts = raw_cmd.strip().split()
        cmd = parts[0].lstrip("!！").lower()
        args = parts[1:] if len(parts) > 1 else []

        print(f"⚙️ [Bot Command] Executed by {message.author} ({message.author.id}): {raw_cmd}")

        if cmd in ["help", "帮助", "h"]:
            help_text = self.get_help_message()
            await message.channel.send(help_text)
            return

        # For admin commands (!model, !debug), verify permission
        if message.author.id not in ALLOWED_PRIVATE_IDS:
            print(f"🚫 [Command Denied] User {message.author} ({message.author.id}) attempted to run admin command: {raw_cmd}")
            await message.channel.send("⛔ 权限不足：只有管理员可使用此指令。")
            return

        if cmd == "model":
            if not args or args[0].lower() in ["status", "current", "info"]:
                status_text = twin.brain.get_model_status()
                await message.channel.send(status_text)
            elif args[0].lower() in ["list", "help", "all"]:
                list_text = twin.brain.get_model_list()
                await message.channel.send(list_text)
            else:
                target_model = args[0]
                success, reply_msg = twin.brain.switch_model(target_model)
                await message.channel.send(reply_msg)

        elif cmd == "debug":
            if not args:
                new_state = not getattr(config, 'DEBUG_MODE', False)
            elif args[0].lower() in ["on", "true", "1", "open", "enable"]:
                new_state = True
            elif args[0].lower() in ["off", "false", "0", "close", "disable"]:
                new_state = False
            else:
                await message.channel.send("❓ 用法: `!debug on` 或 `!debug off` (或直接输入 `!debug` 切换状态)")
                return

            config.DEBUG_MODE = new_state
            config.update_env_value("DEBUG_MODE", "true" if new_state else "false")
            state_str = "🟢 **已开启** (Bot 回复将展示解析到的内容)" if new_state else "🔴 **已关闭** (Bot 回复恢复纯文本模式)"
            await message.channel.send(f"🛠️ **调试模式**: {state_str}")
        else:
            await message.channel.send(f"❓ 未知指令 `{raw_cmd}`。输入 `!help` 查看可用指令列表。")

    async def on_message(self, message):
        # 1. Ignore messages sent by the bot itself or other bots (e.g. ermiana, MEE6)
        if message.author == self.user or message.author.bot:
            return

        raw_cmd = (message.content or "").strip()

        # 2. Intercept commands (any message starting with ! or ！) - NEVER trigger persona chatter
        if raw_cmd.startswith(("!", "！")):
            await self._handle_bot_command(message, raw_cmd)
            return

        now = asyncio.get_event_loop().time()
        channel_id = message.channel.id
        is_dm = (message.guild is None)

        # Check if there is an image attachment even if text content is empty
        has_attachment_image = any(
            (att.content_type and att.content_type.startswith("image/")) or \
            any(att.filename.lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.webp', '.gif'))
            for att in message.attachments
        )

        print(f"📩 [Message] From: {message.author} (ID: {message.author.id}) | DM: {is_dm} | Channel: {channel_id} | Attachments: {len(message.attachments)} | Content: {repr(message.content[:40])}")
        
        # 2s-Absolute Refractory Period
        last_time = self.last_msg_time.get(channel_id, 0)
        if (now - last_time) < config.REFRACTORY_ABSOLUTE:
            print(f"⏳ [Refractory Dropped] Message from {message.author} arrived within 2s cooldown. Skipped.")
            self.last_msg_time[channel_id] = now
            return
        
        self.last_msg_time[channel_id] = now

        # Case 1: Specific Auto-Reply Channel
        is_auto_channel = (channel_id == config.AUTO_REPLY_CHANNEL_ID)
        
        # Case 2: Private Message (Direct Message)
        is_private = is_dm and (message.author.id in ALLOWED_PRIVATE_IDS)
        if is_dm and not is_private:
            print(f"🚫 [DM Ignored] User {message.author} (ID: {message.author.id}) is NOT in ALLOWED_PRIVATE_IDS: {ALLOWED_PRIVATE_IDS}")
        
        # Case 3: Mention in Server
        is_mention = message.guild and self.user.mentioned_in(message) and config.RESPOND_TO_MENTIONS

        if not is_dm and not is_auto_channel and not is_mention:
            print(f"ℹ️ [Ignored Guild Msg] Channel {channel_id} is not AUTO_REPLY_CHANNEL_ID ({config.AUTO_REPLY_CHANNEL_ID}) and bot was not @mentioned.")

        should_reply = False
        trigger_text = message.content or ""

        if is_private:
            should_reply = True
        elif is_mention:
            should_reply = True
            trigger_text = message.content.replace(f"<@{self.user.id}>", "").replace(f"<@!{self.user.id}>", "").strip()
        elif is_auto_channel:
            if self.is_responding.get(channel_id, False):
                if random.random() < config.CHANNEL_REPLY_PROBABILITY:
                    should_reply = True
            else:
                should_reply = True
        
        if should_reply and (trigger_text or has_attachment_image):
            await self._process_message(message, trigger_text)
    
    async def _process_message(self, message, clean_text):
        """Process and respond to a message"""
        channel_id = message.channel.id
        self.is_responding[channel_id] = True
        
        try:
            async with message.channel.typing():
                # 1. Extract link embeds if message contains URL
                processed_input = await extract_content_with_embeds(message, clean_text, brain=twin.brain)

                # 2. Extract direct image/gif attachments
                attachment_descriptions = []
                for att in message.attachments:
                    is_img = (att.content_type and att.content_type.startswith("image/")) or \
                             any(att.filename.lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.webp', '.gif'))
                    if is_img:
                        try:
                            print(f"🖼️ [Attachment] Processing image/gif: {att.filename}...")
                            img_bytes = await att.read()
                            desc = await get_visual_description(twin.brain, img_bytes, filename=att.filename)
                            if desc:
                                attachment_descriptions.append(desc)
                        except Exception as e:
                            print(f"⚠️ [Attachment] Failed to process attachment {att.filename}: {e}")

                if attachment_descriptions:
                    att_block = "\n".join(attachment_descriptions)
                    if processed_input and processed_input != '[Shared Link]':
                        processed_input = f"{processed_input}\n{att_block}"
                    else:
                        processed_input = att_block

                # If after processing there is still no input (e.g. non-image attachment)
                if not processed_input or not processed_input.strip():
                    print("⚠️ [Process] Empty processed input after embed/attachment extraction. Skipping reply.")
                    return

                # 3. Fetch background context (10 messages before the current one)
                background_history = []
                async for msg in message.channel.history(limit=10, before=message):
                    author = msg.author.display_name
                    content = msg.clean_content
                    if msg.embeds:
                        embed_titles = [eb.title for eb in msg.embeds if eb.title]
                        if embed_titles:
                            content += f" [链接预览: {' | '.join(embed_titles)}]"
                    if msg.attachments:
                        img_count = sum(1 for a in msg.attachments if (a.content_type and a.content_type.startswith("image/")) or any(a.filename.lower().endswith(e) for e in ('.png', '.jpg', '.jpeg', '.webp', '.gif')))
                        if img_count > 0:
                            content += f" [发送了{img_count}张图片/动图]"
                    background_history.append(f"{author}: {content}")
                
                background_history.reverse()
                history_text = "\n".join(background_history)

                reply = await twin.respond(
                    processed_input, 
                    author_id=str(message.author.id), 
                    author_name=message.author.display_name,
                    background_history=history_text
                )
                
                # Split reply into separate message bursts (clean lines & limit to max 5)
                raw_lines = [l.strip() for l in (reply or "").strip().split('\n') if l.strip()]
                clean_lines = []
                for l in raw_lines:
                    cleaned = re.sub(r'^(?:[0-9]+[.)、\s]+|[-*•]\s*)', '', l).strip()
                    if cleaned:
                        clean_lines.append(cleaned)
                clean_lines = clean_lines[:5]

                # Dampen excessive AI habit of prepending a standalone emoji on every reply
                if len(clean_lines) > 1 and is_standalone_emoji(clean_lines[0]):
                    first_token = clean_lines[0]
                    keep_prob = 0.05 if '🤔' in first_token else 0.15
                    if random.random() > keep_prob:
                        print(f"🧹 [Filter] Suppressed repetitive standalone emoji prefix: {first_token}")
                        clean_lines = clean_lines[1:]

                if not clean_lines and reply and reply.strip():
                    clean_lines = [reply.strip()]

                delay = random.uniform(config.AUTO_REPLY_DELAY_MIN, config.AUTO_REPLY_DELAY_MAX)
                print(f"⏳ [{message.channel}] Simulating initial typing: {delay:.1f}s")
                await asyncio.sleep(delay)

                for i, line in enumerate(clean_lines):
                    # Attach debug header to the first message if DEBUG_MODE is True
                    if i == 0 and getattr(config, 'DEBUG_MODE', False):
                        debug_header = f"> 🛠️ **[DEBUG 看到的内容]**\n> {processed_input.replace(chr(10), chr(10) + '> ')}\n\n"
                        send_text = f"{debug_header}{line}"
                    else:
                        send_text = line

                    if i > 0:
                        burst_wait = min(max(len(line) * 0.08 + random.uniform(0.6, 1.4), 0.8), 2.5)
                        async with message.channel.typing():
                            await asyncio.sleep(burst_wait)

                    await message.channel.send(send_text)
                    print(f"📤 [{message.channel}] Replied [{i+1}/{len(clean_lines)}]: {line}")
        finally:
            self.is_responding[channel_id] = False

# 4. Start the bot
if __name__ == "__main__":
    print("🚀 Starting Discord bot...")
    try:
        client = EchoMirrorBot(intents=intents)
        client.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Failed to connect without proxy: {e}")
        print("🔄 Retrying with proxy...")
        try:
            client = EchoMirrorBot(intents=intents, proxy="http://127.0.0.1:7891")
            client.run(DISCORD_TOKEN)
        except Exception as e2:
            print(f"❌ Failed to connect with proxy: {e2}")
            print("💥 Unable to start the bot. Please check your network or proxy settings.")
            exit(1)
