import json
import os
import re
from google import genai
import sys
import io
import config

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def get_api_key(api_key=None):
    """Return cleaned and validated API key."""
    if api_key is None:
        api_key = os.getenv('DISCORD_AI_API_KEY') or config.API_KEY

    if not api_key or api_key.strip() == 'your_api_key_here':
        raise ValueError(
            "❌ API Key not set or invalid! Please set environment variable: export DISCORD_AI_API_KEY='your_actual_api_key'"
        )

    api_key = api_key.strip()

    try:
        api_key.encode('ascii')
    except UnicodeEncodeError:
        raise ValueError(
            "❌ API Key contains non-ASCII characters! Please check your API Key."
        )

    return api_key


def generate_persona(api_key=None, chat_file='cleaned_chat.json', target_user_role='me'):
    """Generate System Persona from chat history using AI."""
    api_key = get_api_key(api_key)

    print('🔍 Analyzing conversation history, extracting character traits...')

    with open(chat_file, 'r', encoding='utf-8') as f:
        sessions = json.load(f)

    sample_dialogues = []
    for session in sessions[:50]:
        for msg in session:
            role = 'Target persona' if msg['role'] == target_user_role else 'Conversation partner'
            sample_dialogues.append(f'{role}: {msg["text"]}')

    sample_text = '\n'.join(sample_dialogues)

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an expert in psychology and behavior. Analyze the speaking style of the 'Target persona' in the following chat logs.
    Write a 'Persona' profile for an AI System Prompt.

    Requirements:
    1. Clearly state tone, average sentence length, and common languages (Traditional/Simplified Chinese, Japanese, English).
    2. List common catchphrases, slang, abbreviations, or Emojis.
    3. The profile must be in a format that directly instructs an AI (e.g., "You are now... Please follow this style...").
    4. Provide only the persona profile content without extra explanation.

    Dialogue samples:
    ---
    {sample_text}
    """

    print('⏳ Asking Gemini to generate persona profile...')
    response = client.models.generate_content(
        model=config.MODEL_NAME,
        contents=prompt
    )

    persona_content = response.text.strip()
    update_config_persona(persona_content)

    with open('current_persona.txt', 'w', encoding='utf-8') as f:
        f.write(persona_content)

    print('✅ Persona profile successfully generated and updated in config.py!')
    print('✅ Persona profile saved to current_persona.txt!')
    return persona_content


def update_config_persona(new_persona):
    """Update PERSONA variable in config.py."""
    with open('config.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_persona_block = f'PERSONA = """{new_persona}"""\n'
    updated = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('PERSONA ='):
            lines[index] = new_persona_block
            updated = True
            break

    if not updated:
        content = ''.join(lines)
        pattern = r'PERSONA\s*=\s*(?:"""[\s\S]*?"""|""[\s\S]*Standardized Model Selection"")'
        replacement = new_persona_block.strip()
        new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
        if count == 0:
            raise RuntimeError('Could not find PERSONA variable in config.py. Ensure config.py contains PERSONA = """..."""')
        lines = new_content.splitlines(keepends=True)

    with open('config.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)


if __name__ == '__main__':
    generate_persona(None, 'cleaned_chat.json', target_user_role='me')
