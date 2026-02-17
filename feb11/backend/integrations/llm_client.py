"""
LLM Client Wrapper - Single source of truth for LLM calls

This module provides a unified interface for calling OpenAI's API,
making it easy to switch models, add logging, and handle errors consistently.
"""

from openai import OpenAI
import os

# Global client
try:
    client = OpenAI()
    HAS_OPENAI = True
except Exception as e:
    client = None
    HAS_OPENAI = False
    print(f"⚠️  Warning: OpenAI client not available: {e}")


def call_llm(
    system_prompt: str,
    user_prompt: str,
    response_format=None,
    model="gpt-4o-mini"
) -> str:
    """
    Unified LLM call function.
    
    Args:
        system_prompt: System instructions
        user_prompt: User query
        response_format: Optional response format (e.g., {"type": "json_object"})
        model: Model to use (default: gpt-4o-mini)
    
    Returns:
        Response content string
    
    Example:
        >>> response = call_llm(
        ...     system_prompt="You are a helpful assistant.",
        ...     user_prompt="What is 2+2?",
        ...     response_format={"type": "json_object"}
        ... )
    """
    if not HAS_OPENAI or not client:
        print("⚠️  OpenAI client not available, returning empty JSON")
        return "{}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    kwargs = {"model": model, "messages": messages}
    if response_format:
        kwargs["response_format"] = response_format
    
    try:
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except Exception as e:
        print(f"⚠️  LLM call failed: {e}")
        return "{}"

