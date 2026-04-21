import json
from datetime import datetime
from collections import Counter
import re
import config

def analyze_chat_features(file_path, target_user='me', update_config=False):
    with open(file_path, 'r', encoding='utf-8') as f:
        sessions = json.load(f)

    response_delays = []
    message_lengths = []
    words = Counter()

    for session in sessions:
        last_time = None
        last_role = None

        for msg in session:
            role = msg['role']
            text = msg['text']
            current_time = datetime.strptime(msg['time'], "%Y-%m-%d %H:%M:%S")

            # 1. Calculate Latency: Time gap between others' last message and target user's response.
            if role == target_user and last_role and last_role != target_user and last_time:
                delay = (current_time - last_time).total_seconds()
                response_delays.append(delay)

            # 2. Statistics for message length and word usage
            if role == target_user:
                message_lengths.append(len(text))

                # Simple tokenization: Filter out link/attachment markers, keep text and emojis.
                clean_text = text.replace('[Shared Link]', '').replace('[Sent Image/Attachment]', '')
                tokens = [char for char in clean_text.strip() if char.strip()]
                words.update(tokens)

            last_time = current_time
            last_role = role

    # Calculate statistics
    stats = {
        'response_delays': response_delays,
        'message_lengths': message_lengths,
        'words': words
    }

    # Output statistical results
    print(f"=== Style Quantization Report for {target_user} ===")
    if response_delays:
        avg_delay = sum(response_delays) / len(response_delays)
        min_delay = min(response_delays)
        max_delay = max(response_delays)
        print(f"⏱️ Average Response Delay: {avg_delay:.1f}s")
        print(f"⏱️ Min delay: {min_delay:.1f}s, Max delay: {max_delay:.1f}s")
        stats['avg_delay'] = avg_delay
        stats['min_delay'] = min_delay
        stats['max_delay'] = max_delay

    if message_lengths:
        avg_len = sum(message_lengths) / len(message_lengths)
        print(f"📏 Average message length: {avg_len:.1f} chars")
        stats['avg_length'] = avg_len

    print("\n🗣️ Most frequent characters/emojis (Top 15):")
    for word, count in words.most_common(15):
        print(f" - {word}: {count} times")

    # Automatically update response timing in config if requested
    if update_config and response_delays:
        update_reply_timing_config(avg_delay, min_delay, max_delay)

    return stats

def update_reply_timing_config(avg_delay, min_delay, max_delay):
    """Update response timing in config.py based on analysis results."""
    with open('config.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Calculate a reasonable response range (80%-120% of avg, bounded by 0.5s-10s)
    min_reply = max(0.5, avg_delay * 0.8)
    max_reply = min(10.0, avg_delay * 1.2)

    # Use a more conservative range if average delay is very short
    if avg_delay < 2.0:
        min_reply = max(0.5, avg_delay * 0.5)
        max_reply = min(5.0, avg_delay * 2.0)

    # Update AUTO_REPLY_DELAY_MIN
    import re
    content = re.sub(
        r'AUTO_REPLY_DELAY_MIN\s*=\s*[\d.]+',
        f'AUTO_REPLY_DELAY_MIN = {min_reply:.1f}',
        content
    )

    # Update AUTO_REPLY_DELAY_MAX
    content = re.sub(
        r'AUTO_REPLY_DELAY_MAX\s*=\s*[\d.]+',
        f'AUTO_REPLY_DELAY_MAX = {max_reply:.1f}',
        content
    )

    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Updated reply timing setting: {min_reply:.1f} - {max_reply:.1f}s (based on avg delay {avg_delay:.1f}s)")

if __name__ == "__main__":
    # Check command line arguments for --update-config
    import sys
    update_config = '--update-config' in sys.argv
    analyze_chat_features('cleaned_chat.json', update_config=update_config)