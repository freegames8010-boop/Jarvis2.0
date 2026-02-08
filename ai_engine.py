# ai_engine.py
# OpenAI ONLY (new SDK, no DeepSeek)

from openai import OpenAI
from config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def has_api():
    if not settings.OPENAI_API_KEY or not settings.OPENAI_API_KEY.startswith("sk-"):
        return False, "Invalid OpenAI API key"
    return True, "OpenAI ready"


def chat_completion(messages, model=settings.OPENAI_MODEL):
    """
    messages = [{"role": "user", "content": "..."}]
    """
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.6,
        max_tokens=500
    )
    return response.choices[0].message.content.strip()
