"""
core/llm_factory.py
-------------------
Factory that builds LangChain BaseChatModel instances per provider.

Supported providers:
    - bedrock   → langchain_aws.ChatBedrockConverse   (requires: langchain-aws)
    - openai    → langchain_openai.ChatOpenAI          (requires: langchain-openai)
    - anthropic → langchain_anthropic.ChatAnthropic    (requires: langchain-anthropic)
    - auto      → langchain.init_chat_model            (provider inferred from model name)

All returned objects are LangChain BaseChatModel instances, so they support
.invoke(), .ainvoke(), .stream(), .astream(), and .bind_tools() out of the box.

Usage:
    from core.llm_factory import LLMFactory

    llm = LLMFactory.create()                        # default provider from settings
    llm = LLMFactory.create("openai")                # explicit provider
    llm = LLMFactory.create("bedrock", model_id="amazon.nova-pro-v1:0")
    response = llm.invoke("Hello!")
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


# ── Provider builder functions ────────────────────────────────────────────────

def _build_bedrock(model_id: str | None = None, **kwargs: Any) -> BaseChatModel:
    """
    Build a ChatBedrockConverse model.

    Requires: pip install langchain-aws boto3

    Auth is handled by boto3 credential chain (env vars, ~/.aws/credentials,
    IAM role). Set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_REGION
    in .env or use an IAM role — do NOT put raw keys in settings.
    """
    try:
        from langchain_aws import ChatBedrockConverse  # type: ignore
    except ImportError as e:
        raise ImportError(
            "langchain-aws is required for the Bedrock provider. "
            "Install it with: pip install langchain-aws boto3"
        ) from e

    params: dict[str, Any] = {
        "model": model_id or settings.bedrock_model_id,
        "region_name": settings.aws_region,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        **kwargs,
    }
    # Pass explicit credentials only if set — otherwise boto3 uses its credential chain
    if settings.aws_access_key_id:
        params["aws_access_key_id"] = settings.aws_access_key_id
    if settings.aws_secret_access_key:
        params["aws_secret_access_key"] = settings.aws_secret_access_key
    if settings.bedrock_api_key:
        params["api_key"] = settings.bedrock_api_key
    logger.info("Initialising ChatBedrockConverse", extra={"model": params["model"]})
    return ChatBedrockConverse(**params)


def _build_openai(model_id: str | None = None, **kwargs: Any) -> BaseChatModel:
    """
    Build a ChatOpenAI model.

    Requires: pip install langchain-openai
    Set OPENAI_API_KEY in .env.
    """
    try:
        from langchain_openai import ChatOpenAI  # type: ignore
    except ImportError as e:
        raise ImportError(
            "langchain-openai is required for the OpenAI provider. "
            "Install it with: pip install langchain-openai"
        ) from e

    params: dict[str, Any] = {
        "model": model_id or settings.openai_model_id,
        "api_key": settings.openai_api_key,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        **kwargs,
    }
    logger.info("Initialising ChatOpenAI", extra={"model": params["model"]})
    return ChatOpenAI(**params)


def _build_anthropic(model_id: str | None = None, **kwargs: Any) -> BaseChatModel:
    """
    Build a ChatAnthropic model.

    Requires: pip install langchain-anthropic
    Set ANTHROPIC_API_KEY in .env.
    """
    try:
        from langchain_anthropic import ChatAnthropic  # type: ignore
    except ImportError as e:
        raise ImportError(
            "langchain-anthropic is required for the Anthropic provider. "
            "Install it with: pip install langchain-anthropic"
        ) from e

    params: dict[str, Any] = {
        "model": model_id or settings.anthropic_model_id,
        "api_key": settings.anthropic_api_key,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        **kwargs,
    }
    logger.info("Initialising ChatAnthropic", extra={"model": params["model"]})
    return ChatAnthropic(**params)


def _build_auto(model_id: str | None = None, **kwargs: Any) -> BaseChatModel:
    """
    Use LangChain's universal init_chat_model.
    Model name can be prefixed: 'openai:gpt-4o', 'anthropic:claude-3-5-sonnet-20241022'.

    Requires: pip install langchain
    """
    try:
        from langchain.chat_models import init_chat_model  # type: ignore
    except ImportError as e:
        raise ImportError(
            "langchain is required for the auto provider. "
            "Install it with: pip install langchain"
        ) from e

    model = model_id or settings.bedrock_model_id
    params: dict[str, Any] = {
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        **kwargs,
    }
    logger.info("Initialising model via init_chat_model", extra={"model": model})
    return init_chat_model(model, **params)


# ── Factory ───────────────────────────────────────────────────────────────────

_REGISTRY: dict[str, Any] = {
    "bedrock": _build_bedrock,
    "openai": _build_openai,
    "anthropic": _build_anthropic,
    "auto": _build_auto,
}


class LLMFactory:
    """
    Central factory for LangChain chat models.

    All returned models are BaseChatModel instances — fully compatible with
    LCEL chains, agents, and the callback handler in agent/callbacks/handler.py.
    """

    @classmethod
    def create(
        cls,
        provider: str | None = None,
        model_id: str | None = None,
        **kwargs: Any,
    ) -> BaseChatModel:
        """
        Create a LangChain chat model.

        Args:
            provider:  'bedrock' | 'openai' | 'anthropic' | 'auto'.
                       Defaults to settings.default_llm_provider.
            model_id:  Override the model name from settings.
            **kwargs:  Extra params forwarded to the underlying model constructor
                       (e.g. streaming=True, top_p=0.9).

        Returns:
            BaseChatModel — ready to use with .invoke() / .ainvoke() / .stream().

        Raises:
            ValueError:   Unknown provider.
            ImportError:  Required provider package not installed.
        """
        provider = (provider or settings.default_llm_provider).lower()
        builder = _REGISTRY.get(provider)
        if not builder:
            raise ValueError(
                f"Unknown LLM provider '{provider}'. "
                f"Available: {list(_REGISTRY.keys())}"
            )
        return builder(model_id=model_id, **kwargs)

    @classmethod
    def register(cls, name: str, builder_fn: Any) -> None:
        """
        Register a custom provider builder at runtime.

        Args:
            name:       Provider key (e.g. 'ollama').
            builder_fn: Callable(model_id, **kwargs) → BaseChatModel.
        """
        _REGISTRY[name.lower()] = builder_fn
        logger.info("Registered custom LLM provider", extra={"provider": name})
