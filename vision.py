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

async def download_and_preprocess(url: str, timeout: float = 6.0) -> tuple[str, bool]:
    """Download image from URL and preprocess it."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
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
