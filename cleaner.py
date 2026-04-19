import json
import re
import sys
from datetime import datetime
from collections import defaultdict
import config

def get_unique_authors(input_file):
    """Get all unique authors from the chat data"""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    authors = {}
    for msg in data.get('messages', []):
        author = msg.get('author', {})
        author_id = author.get('id')
        author_name = author.get('name', 'Unknown')
        if author_id and author_id not in authors:
            authors[author_id] = author_name

    return authors

def select_user_roles(authors):
    """Select which ID is 'me' and assign roles"""
    print("Detected authors:")
    for i, (aid, name) in enumerate(authors.items()):
        print(f"{i+1}. {name} (ID: {aid})")

    # Select 'me'
    while True:
        try:
            choice_input = input("Please select which user you are (enter number, default 1): ").strip()
            if not choice_input:
                choice = 0  # Default to first user (index 0)
            else:
                choice = int(choice_input) - 1
            
            if 0 <= choice < len(authors):
                me_id = list(authors.keys())[choice]
                break
            else:
                print("Invalid choice, please try again.")
        except ValueError:
            print("Please enter a valid number.")

    # Assign roles
    roles = {}
    roles[me_id] = 'me'
    for aid in authors:
        if aid != me_id:
            roles[aid] = authors[aid]  # Use name as role for others

    return roles

def clean_discord_data(input_file, output_file):
    authors = get_unique_authors(input_file)
    if len(authors) < 2:
        print("Error: Need at least two users' conversation data.")
        return

    roles = select_user_roles(authors)

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    messages = data.get('messages', [])
    cleaned_data = []

    current_session = []
    last_timestamp = None

    for msg in messages:
        author_id = msg.get('author', {}).get('id')
        if author_id not in roles:
            continue  # Skip messages from unknown users

        raw_time = msg.get('timestamp')
        if not raw_time:
            continue

        # 1. Get raw text content
        content = msg.get('content', '').strip()

        # 2. Process Embeds (link preview information)
        embed_details = []
        for eb in msg.get('embeds', []):
            title = eb.get('title')
            desc = eb.get('description')
            if title:
                embed_details.append(f"Title: {title}")
            if desc:
                short_desc = (desc[:60] + '...') if len(desc) > 60 else desc
                embed_details.append(f"Brief: {short_desc}")

        if embed_details:
            context_str = " [" + " | ".join(embed_details) + "]"
            content += context_str

        # 3. Process attachment tags
        if msg.get('attachments'):
            content += " [Sent Image/Attachment]"

        if not content.strip():
            continue

        # 4. Replace URLs with [Shared Link] to prevent hallucination
        content = re.sub(r'http[s]?://\S+', '[Shared Link]', content)

        # 5. Parse timestamp
        timestamp = datetime.fromisoformat(raw_time)

        # 6. Conversation session splitting
        if last_timestamp and (timestamp - last_timestamp).total_seconds() > config.SESSION_SPLIT_TIME:
            if current_session:
                cleaned_data.append(current_session)
            current_session = []

        role = roles[author_id]
        current_session.append({
            "role": role,
            "text": content,
            "time": timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })
        last_timestamp = timestamp

    if current_session:
        cleaned_data.append(current_session)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)

    print(f"Cleaning complete! Link previews considered, extracted {len(cleaned_data)} sessions.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Discord Chat Cleaner")
        print("Usage: python cleaner.py [input_file] [output_file]")
        print("")
        print("Parameters:")
        print("  input_file: Discord chat JSON file (default: MyA_Chat.json)")
        print("  output_file: Cleaned output file (default: cleaned_chat.json)")
        print("")
        print("Enters interactive mode if no parameters are provided.")
        sys.exit(0)

    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    elif len(sys.argv) == 2:
        input_file = sys.argv[1]
        output_file = 'cleaned_chat.json'
    else:
        # Interactive mode
        input_file = input("Enter the input filename (default: MyA_Chat.json): ").strip()
        if not input_file:
            input_file = 'MyA_Chat.json'

        output_file = input("Enter the output filename (default: cleaned_chat.json): ").strip()
        if not output_file:
            output_file = 'cleaned_chat.json'

    clean_discord_data(input_file, output_file)