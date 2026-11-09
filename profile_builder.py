import json
import os
import re
import sys
import io
import config
from brain import ChatBrain

# Force UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def generate_persona(api_key=None, chat_file='cleaned_chat.json', target_user_role='me'):
    """Generate System Persona from chat history using the configured LLM Brain."""
    print('🔍 Analyzing conversation history, extracting character traits...')

    if not os.path.exists(chat_file):
        raise FileNotFoundError(f"❌ Chat history file '{chat_file}' not found.")

    with open(chat_file, 'r', encoding='utf-8') as f:
        sessions = json.load(f)

    sample_dialogues = []
    for session in sessions[:50]:
        for msg in session:
            role = 'Target persona' if msg['role'] == target_user_role else 'Conversation partner'
            sample_dialogues.append(f'{role}: {msg["text"]}')

    sample_text = '\n'.join(sample_dialogues)

    brain = ChatBrain(api_key=api_key)

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

    print(f'⏳ Asking {brain.provider.upper()} ({brain.model_id}) to generate persona profile...')
    persona_content = brain.generate_text(prompt)

    persona_file = os.getenv("PERSONA_FILE", "current_persona.txt").strip() or "current_persona.txt"
    with open(persona_file, 'w', encoding='utf-8') as f:
        f.write(persona_content)

    print(f'✅ Persona profile successfully generated and saved to {persona_file}!')
    return persona_content

if __name__ == '__main__':
    generate_persona(None, 'cleaned_chat.json', target_user_role='me')
