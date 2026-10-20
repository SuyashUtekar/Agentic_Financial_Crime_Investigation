from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parents[1]
# Secrets load after public configuration, so a local credential takes priority.
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env.secrets", override=True)


@dataclass(frozen=True)
class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "disabled")
    llm_model: str = os.getenv("LLM_MODEL", "qwen3:4b")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_base_url: str = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    openai_compatible_base_url: str = os.getenv("OPENAI_COMPATIBLE_BASE_URL", "https://api.openai.com/v1")
    openai_compatible_api_key: str = os.getenv("OPENAI_COMPATIBLE_API_KEY", "")


settings = Settings()
