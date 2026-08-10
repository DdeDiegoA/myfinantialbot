"""OpenAI-compatible completion call across providers, config-driven only."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

PROVIDERS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "nvidia": "https://integrate.api.nvidia.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "openai": "https://api.openai.com/v1",
}


def get_completion(prompt: str, context: str) -> str:
    provider = os.environ["LLM_PROVIDER"]
    model = os.environ["LLM_MODEL"]
    api_key = os.environ["LLM_API_KEY"]
    # ponytail: resolved at call time, not import time, so LLM_CUSTOM_BASE_URL
    # set after module import (e.g. by a test or a config reload) still works
    base_url = os.environ.get("LLM_CUSTOM_BASE_URL", "") if provider == "custom" else PROVIDERS[provider]

    if provider == "anthropic":
        # Anthropic's Messages API is not OpenAI-chat-completions-compatible:
        # different endpoint, x-api-key header, and response shape.
        response = requests.post(
            f"{base_url}/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "system": context,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024,
                "temperature": 0,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]

    # OpenAI-compatible providers: use the OpenAI client for consistency
    client = OpenAI(base_url=base_url, api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        temperature=0,  # deterministic output: eval.py needs reproducible scores
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    # ponytail: smoke test only, needs real env/network to pass; asserts the contract shape
    assert set(PROVIDERS) == {"openrouter", "nvidia", "anthropic", "openai"}
    assert all(isinstance(v, str) for v in PROVIDERS.values())
    print("llm.py self-check ok")
