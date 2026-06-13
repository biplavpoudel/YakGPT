# backend/llm/factory.py

import os
from functools import lru_cache
from langchain_core.language_models.chat_models import BaseChatModel

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic 
from langchain_google_genai import ChatGoogleGenerativeAI
# from llama_cpp import Llama
# from langchain_community.chat_models import LlamaCpp
from langchain_community.llms import LlamaCpp
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

from pydantic import SecretStr
from dotenv import load_dotenv


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
@lru_cache(maxsize=2)
def get_llm_provider() -> BaseChatModel:
    """
    Cached LLM factory for performance + LangGraph stability.
    """
    # Force a fresh disk read right before checking the provider variable
    load_dotenv(override=True)

    provider = os.getenv("LLM_PROVIDER", "huggingface").lower()
    print(f"--- ACTIVE LLM PROVIDER: {repr(provider)} ---")

    # --------------------------------------------------------
    # LLAMA.CPP
    # --------------------------------------------------------
    if provider == "llama.cpp":
        model_path = os.getenv("LLAMA_MODEL_PATH", "/home/biplav/models/llama/dark-planet-8b.gguf")
        temp = float(os.getenv("LLAMA_TEMPERATURE", "0.7"))
        top_p = float(os.getenv("LLAMA_TOP_P", "0.9"))
        max_tokens = int(os.getenv("LLAMA_MAX_TOKENS", "512"))
        repeat_penalty = float(os.getenv("LLAMA_REPEAT_PENALTY", "1.1"))
        stop = ["<|im_end|>", "<|im_start|>"]

        if not os.getenv("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = "sk-no-key-required"

        # ./llama-server --model ~/models/llama/dark-planet-8b.gguf --ctx-size 4096   --n-gpu-layers -1   --port 8080   --chat-template chatml

        return ChatOpenAI(
            # Core Client Params
            model="gpt-3.5-turbo",         # Just a placeholder, using any name works here
            base_url="http://localhost:8080/v1",
            temperature=temp,                   
            # Custom Server Params
            # Utilizing model_kwargs ensures these exact keys land un-altered in the root payload body
            model_kwargs={
                "max_tokens": max_tokens,   # Enforces the stop ceiling on llama-server natively
                "top_p": top_p,                   # Applies nucleus sampling
                "frequency_penalty": repeat_penalty, # Suppresses loop generation and narrative repetition
                "stop": stop,
            }
        )

    # --------------------------------------------------------
    # OLLAMA
    # --------------------------------------------------------
    elif provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "yak-gm:latest")

        return ChatOllama(
            base_url=base_url,
            model=model,
        )
    
    # --------------------------------------------------------
    # HUGGING FACE SERVERLESS API
    # --------------------------------------------------------
    elif provider == "huggingface":
        api_key = os.getenv("HF_TOKEN")
        model = os.getenv("HF_MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
        
        if not api_key:
            raise LLMConfigError("Missing required environment variable: HF_TOKEN")

        llm = HuggingFaceEndpoint(
            repo_id=model,
            task="text-generation",
            huggingfacehub_api_token=api_key,
            max_new_tokens=512,
            temperature=0.7,
            model=model
        )
        
        return ChatHuggingFace(llm=llm)

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


if __name__ == "__main__":
    from langchain_community.chat_models import ChatLlamaCpp
    from langchain_core.prompts import ChatPromptTemplate

    llm = ChatLlamaCpp(
        model_path="/home/biplav/models/llama/dark-planet-8b.gguf",
        n_gpu_layers=-1,
        verbose=True,
    )

    prompt = ChatPromptTemplate.from_template(
        "You are a cynical Himalayan pack yak.\n"
        "Location: {loc}. Trekker action: {action}.\n"
        "Respond in 2 sarcastic sentences."
    )

    chain = prompt | llm
    res = chain.invoke({"loc": "Manang", "action": "took a rest day"})
    print("CONTENT:", res.content)