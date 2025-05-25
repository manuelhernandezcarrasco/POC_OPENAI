import requests
import os
from .ai_adapter import AIModelAdapter

class GeminiFlashAdapter(AIModelAdapter):
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-04-17:generateContent"
    def send_request(self, prompt: str, jd_text: str, cvs_texts: list[str]) -> dict:
        content = prompt + "\n\nJob Description:\n" + jd_text + "\n\n"
        for i, cv in enumerate(cvs_texts):
            content += f"\nCV #{i+1}:\n{cv}\n"

        headers = {
            "Content-Type": "application/json"
        }

        params = {
            "key": self.api_key
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": content}
                    ]
                }
            ]
        }

        response = requests.post(self.api_url, headers=headers, params=params, json=payload)
        if response.status_code != 200:
            return {"error": response.text}

        return response.json()
