# backend/llm/factory.py

import os
from functools import lru_cache
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic 
from langchain_google_genai import ChatGoogleGenerativeAI 
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
def get_llm_provider(provider="gemini") -> BaseChatModel:
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
    # OPENAI (Official)
    # --------------------------------------------------------
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

        if not api_key:
            raise LLMConfigError("Missing required environment variable: OPENAI_API_KEY")

        return ChatOpenAI(api_key=SecretStr(api_key), model=model)

    # --------------------------------------------------------
    # ANTHROPIC (Official)
    # --------------------------------------------------------
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model = os.getenv("ANTHROPIC_MODEL_NAME", "claude-3-5-sonnet-latest")
        timeout = 2.0
        stop = None

        if not api_key:
            raise LLMConfigError("Missing required environment variable: ANTHROPIC_API_KEY")

        return ChatAnthropic(model_name=model, timeout=timeout, stop=stop, api_key=SecretStr(api_key), )

    # --------------------------------------------------------
    # GEMINI (Official Google GenAI)        
    # --------------------------------------------------------
    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

        if not api_key:
            raise LLMConfigError("Missing required environment variable: GEMINI_API_KEY")
        

        # needs to format the response
        return ChatGoogleGenerativeAI(
            google_api_key=SecretStr(api_key),
            model=model,
        )


    # --------------------------------------------------------
    # UNKNOWN PROVIDER
    # --------------------------------------------------------
    raise ValueError(f"Unsupported LLM provider: {provider}")