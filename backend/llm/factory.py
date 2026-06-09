# backend/llm/factory.py

import os
from functools import lru_cache
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import SecretStr


class LLMConfigError(Exception):
    pass


# ============================================================
# VALIDATION
# ============================================================
def _validate_env(var: str, name: str):
    if not var:
        raise LLMConfigError(f"Missing required environment variable: {name}")


# ============================================================
# FACTORY (CACHED)
# ============================================================
@lru_cache(maxsize=4)
def get_llm_provider() -> BaseChatModel:
    """
    Cached LLM factory for performance + LangGraph stability.
    """

    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    # --------------------------------------------------------
    # OLLAMA
    # --------------------------------------------------------
    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "yak-gm:latest")

        return ChatOllama(
            base_url=base_url,
            model=model,
        )

    # --------------------------------------------------------
    # MODAL (OpenAI-compatible endpoint)
    # --------------------------------------------------------
    elif provider == "modal":
        api_url = os.getenv("MODAL_API_URL")
        api_key = os.getenv("MODAL_API_KEY", "dummy-key-if-unauthenticated")
        model = os.getenv("MODAL_MODEL_NAME")

        # Inline Type Guarding: This leaves no doubt for Pylance's analyzer
        if not api_url:
            raise LLMConfigError("Missing required environment variable: MODAL_API_URL")
        if not model:
            raise LLMConfigError("Missing required environment variable: MODAL_MODEL_NAME")

        return ChatOpenAI(
            base_url=api_url,
            api_key=SecretStr(api_key),
            model=model,
        )


    # --------------------------------------------------------
    # UNKNOWN PROVIDER
    # --------------------------------------------------------
    raise ValueError(f"Unsupported LLM provider: {provider}")