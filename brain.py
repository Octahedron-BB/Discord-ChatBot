from google import genai
import sys
import config

class ChatBrain:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key.strip())
        self.model_id = config.MODEL_NAME

    def expand_query(self, user_input):
        prompt = f"Transform this into 3 Discord search keywords: {user_input}. Output directly, comma-separated."

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )

            if response.text:
                expanded = response.text.strip()
                print(f"DEBUG: Gemini expansion result -> {expanded}")
                return f"query: {expanded}"
            return f"query: {user_input}"

        except Exception as e:
            print(f"⚠️ Attempt to use {self.model_id} failed: {e}")
            return f"query: {user_input}"

    def list_my_models(self):
        """List available models for the current API key."""
        print("🔍 Querying available models for your API Key...")
        for model in self.client.models.list():
            print(f" - {model.name}")