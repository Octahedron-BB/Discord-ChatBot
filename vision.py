import io
import re
import base64
import httpx
from PIL import Image

async def fetch_twitter_metadata(tweet_url: str) -> dict | None:
    """
    Fetch tweet text and media (photos or video thumbnail) via fxtwitter API.
    Handles age-restricted content, videos, gifs, and multiple images automatically.
    """
    match = re.search(r'https?://(?:x|twitter)\.com/([a-zA-Z0-9_]+)/status/(\d+)', tweet_url)
    if not match:
        return None
    screen_name, status_id = match.group(1), match.group(2)
    api_url = f"https://api.fxtwitter.com/{screen_name}/status/{status_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            resp = await client.get(api_url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                tweet = data.get("tweet", {})
                author_name = tweet.get("author", {}).get("name", screen_name)
                text = tweet.get("text", "")

                media = tweet.get("media", {})
                media_urls = []
                # Photos
                for photo in media.get("photos", []):
                    if photo.get("url"):
                        media_urls.append(photo["url"])
                # Videos (use high quality thumbnail)
                for video in media.get("videos", []):
                    if video.get("thumbnail_url"):
                        media_urls.append(video["thumbnail_url"])

                return {
                    "author": f"{author_name} (@{screen_name})",
                    "text": text,
                    "media_urls": media_urls
                }
    except Exception as e:
        print(f"⚠️ [Twitter API] Failed to fetch {api_url}: {e}")
    return None

async def fetch_instagram_metadata(ig_url: str) -> dict | None:
    """
    Fetch Instagram post/reel caption and preview image.
    Uses multi-stage fallback:
    1. Official Instagram oEmbed API (fast, high-res thumbnail and full caption for public posts)
    2. vxinstagram proxy (OpenGraph tags)
    3. kkclip mirror (handles HTML meta tags and direct image streams)
    Supports posts (/p/), reels (/reel/, /reels/), and videos (/tv/).
    """
    import html as html_lib
    import urllib.parse

    match = re.search(r'https?://(?:www\.)?(?:instagram\.com|instagr\.am)/(?:p|reel|reels|tv|share/(?:p|reel))/([a-zA-Z0-9_-]+)', ig_url)
    if not match:
        return None
    shortcode = match.group(1)
    clean_url = f"https://www.instagram.com/p/{shortcode}/"

    headers_browser = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    headers_bot = {
        "User-Agent": "Discordbot/2.0 (+https://discordapp.com)"
    }

    async with httpx.AsyncClient(timeout=7.0, follow_redirects=True) as client:
        # Stage 1: Official Instagram oEmbed API
        try:
            oembed_url = f"https://www.instagram.com/api/v1/oembed/?url={urllib.parse.quote(clean_url)}"
            resp = await client.get(oembed_url, headers=headers_browser)
            if resp.status_code == 200:
                data = resp.json()
                author = (data.get("author_name") or "").strip()
                title = (data.get("title") or "").strip()
                thumb = (data.get("thumbnail_url") or "").strip()
                if author or title or thumb:
                    print(f"✅ [Instagram] oEmbed resolved: {shortcode} (author: {author})")
                    return {
                        "author": author,
                        "text": title,
                        "media_urls": [thumb] if thumb else []
                    }
        except Exception as e:
            print(f"⚠️ [Instagram oEmbed] Error: {e}")

        # Stage 2: vxinstagram mirror
        try:
            vx_url = f"https://www.vxinstagram.com/p/{shortcode}/"
            resp = await client.get(vx_url, headers=headers_bot)
            if resp.status_code == 200:
                text_content = resp.text
                title_m = re.search(r'<meta\s+(?:property|name)=[\'"](?:og:title|twitter:title)[\'"]\s+content=[\'"]([^\'"]*)[\'"]', text_content, re.IGNORECASE)
                desc_m = re.search(r'<meta\s+(?:property|name)=[\'"](?:og:description|twitter:description|description)[\'"]\s+content=[\'"]([^\'"]*)[\'"]', text_content, re.IGNORECASE)
                img_m = re.search(r'<meta\s+(?:property|name)=[\'"](?:og:image|twitter:image)[\'"]\s+content=[\'"]([^\'"]*)[\'"]', text_content, re.IGNORECASE)

                author = html_lib.unescape(title_m.group(1)).strip() if title_m else ""
                desc = html_lib.unescape(desc_m.group(1)).strip() if desc_m else ""
                img_url = html_lib.unescape(img_m.group(1)).strip() if img_m else ""

                if author or desc or img_url:
                    print(f"✅ [Instagram] vxinstagram resolved: {shortcode}")
                    return {
                        "author": author,
                        "text": desc,
                        "media_urls": [img_url] if img_url else []
                    }
        except Exception as e:
            print(f"⚠️ [Instagram vxinstagram] Error: {e}")

        # Stage 3: kkclip mirror (handles HTML meta tags and direct image streaming)
        kk_urls = [
            f"https://www.kkclip.com/p/{shortcode}/",
            f"https://www.kkclip.com/reel/{shortcode}/"
        ]
        for mirror_url in kk_urls:
            try:
                resp = await client.get(mirror_url, headers=headers_bot)
                if resp.status_code == 200:
                    ct = resp.headers.get("content-type", "").lower()
                    if "image/" in ct or resp.content.startswith(b'\xff\xd8\xff'):
                        print(f"✅ [Instagram] kkclip direct image stream resolved: {shortcode}")
                        return {
                            "author": "",
                            "text": "",
                            "media_urls": [mirror_url]
                        }

                    text_content = resp.text
                    title_m = re.search(r'<meta\s+(?:property|name)=[\'"](?:twitter:title|og:title)[\'"]\s+content=[\'"]([^\'"]*)[\'"]', text_content, re.IGNORECASE)
                    desc_m = re.search(r'<meta\s+(?:property|name)=[\'"](?:og:description|twitter:description|description)[\'"]\s+content=[\'"]([^\'"]*)[\'"]', text_content, re.IGNORECASE)
                    img_m = re.search(r'<meta\s+(?:property|name)=[\'"](?:twitter:image|og:image)[\'"]\s+content=[\'"]([^\'"]*)[\'"]', text_content, re.IGNORECASE)

                    author = html_lib.unescape(title_m.group(1)).strip() if title_m else ""
                    desc = html_lib.unescape(desc_m.group(1)).strip() if desc_m else ""
                    img_url = html_lib.unescape(img_m.group(1)).strip() if img_m else ""

                    if " • Instagram" in author:
                        author = author.split(" • Instagram")[0].strip()
                    elif " on Instagram" in author:
                        author = author.replace(" on Instagram", "").strip()

                    if author or desc or img_url:
                        print(f"✅ [Instagram] kkclip HTML resolved: {shortcode}")
                        return {
                            "author": author,
                            "text": desc,
                            "media_urls": [img_url] if img_url else []
                        }
            except Exception as e:
                print(f"⚠️ [Instagram kkclip] Error on {mirror_url}: {e}")

    return None

def preprocess_image_bytes(image_bytes: bytes, filename: str = "") -> tuple[str, bool]:
    """
    Preprocess image/gif bytes into an optimized base64 data URL.
    - If GIF: extracts the first frame.
    - If RGBA/transparency: converts to RGB with white background.
    - Resizes large images to max 1024px to reduce token consumption and latency.
    """
    is_gif = False
    filename_lower = filename.lower()

    try:
        im = Image.open(io.BytesIO(image_bytes))
        
        # Check if animated GIF
        if im.format == 'GIF' or filename_lower.endswith('.gif') or getattr(im, 'is_animated', False):
            is_gif = True
            im.seek(0)  # Extract the first frame

        # Convert to RGB (handle transparency / palette modes gracefully)
        if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
            background = Image.new('RGB', im.size, (255, 255, 255))
            alpha = im.convert('RGBA').split()[-1]
            background.paste(im.convert('RGBA'), mask=alpha)
            im = background
        elif im.mode != 'RGB':
            im = im.convert('RGB')

        # Resize if dimensions exceed 1024
        max_dim = max(im.size)
        if max_dim > 1024:
            scale = 1024.0 / max_dim
            new_size = (int(im.size[0] * scale), int(im.size[1] * scale))
            im = im.resize(new_size, Image.Resampling.LANCZOS)

        out_buffer = io.BytesIO()
        im.save(out_buffer, format='JPEG', quality=85)
        b64_data = base64.b64encode(out_buffer.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{b64_data}", is_gif

    except Exception as e:
        print(f"⚠️ [Vision] Image preprocessing failed: {e}")
        return "", False

async def download_and_preprocess(url: str, timeout: float = 8.0) -> tuple[str, bool]:
    """Download image from URL and preprocess it."""
    ua = "Discordbot/2.0 (+https://discordapp.com)" if ("kkclip.com" in url or "vxinstagram.com" in url) else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    headers = {"User-Agent": ua}
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return preprocess_image_bytes(resp.content, filename=url)
            else:
                print(f"⚠️ [Vision] Failed to fetch image: HTTP {resp.status_code} ({url[:60]})")
    except Exception as e:
        print(f"⚠️ [Vision] Error fetching image URL: {e}")
    return "", False

async def get_visual_description(brain, source: bytes | str, filename: str = "") -> str:
    """
    Generate a concise text summary of an image or GIF for persona prompt injection.
    :param brain: ChatBrain instance
    :param source: bytes of image data, or a string URL
    :param filename: optional filename to aid format detection
    """
    if isinstance(source, bytes):
        data_url, is_gif = preprocess_image_bytes(source, filename)
    elif isinstance(source, str) and (source.startswith("http://") or source.startswith("https://")):
        data_url, is_gif = await download_and_preprocess(source)
    elif isinstance(source, str) and source.startswith("data:image/"):
        data_url, is_gif = source, "gif" in filename.lower()
    else:
        return ""

    if not data_url:
        return ""

    target_type = "动图/表情包" if is_gif else "图片"
    prompt = (
        f"请用极简、自然的口语描述这张{target_type}（1~2句话）："
        "1. 画面核心主体、人物/角色动作或神态；"
        "2. 图里的文字或台词（若有）；"
        "3. 表情包/玩梗点或表达的情绪（若有）。"
        "直接给出画面描述，不要多余废话。"
    )

    try:
        desc = brain.describe_image(data_url, prompt=prompt)
        if desc:
            prefix = "表情包/动图画面" if is_gif else "图片画面"
            return f"[{prefix}: {desc}]"
    except Exception as e:
        print(f"⚠️ [Vision] Failed to describe image: {e}")

    return ""
