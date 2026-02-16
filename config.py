import os
from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    llm_api_base: str = os.getenv("LLM_API_BASE_URL", "https://openrouter.ai/api/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL_NAME", "meta-llama/llama-3.1-8b-instruct")
    telegram_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
