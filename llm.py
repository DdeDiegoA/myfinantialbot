"""OpenAI-compatible completion call across providers, config-driven only."""
import os
import time

import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PROVIDERS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "nvidia": "https://integrate.api.nvidia.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "openai": "https://api.openai.com/v1",
}

# Nvidia's endpoint has a documented history of intermittent 5xx (design.md) --
# observed live during eval: a 503 with zero retries killed a 23-case run at
# case 9. Retrying transient server errors here fixes it for every caller
# (rag.py, serve.py, eval.py) instead of each one reimplementing it.
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2


def get_completion(prompt: str, context: str) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            return _call(prompt, context)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code < 500 or attempt == MAX_RETRIES - 1:
                raise  # 4xx is not transient (bad key/model/etc); last attempt re-raises
            time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))


def _call(prompt: str, context: str) -> str:
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

    if provider == "nvidia":
        # ponytail: nvidia's non-streaming chat/completions hangs past the
        # read timeout for reasoning models; their own docs recommend
        # stream=True. Client-side, not a transient error, so no retry helps.
        client = OpenAI(base_url=base_url, api_key=api_key, timeout=60)
        stream = client.chat.completions.create(
            model=model,
            temperature=0,  # deterministic output: eval.py needs reproducible scores
            top_p=1,
            max_tokens=16384,
            extra_body={"reasoning_budget": 16384},
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        chunks = [
            c.choices[0].delta.content
            for c in stream
            if c.choices and c.choices[0].delta.content is not None
        ]
        return "".join(chunks)

    response = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "temperature": 0,  # deterministic output: eval.py needs reproducible scores
            "messages": [
                {"role": "system", "content": context},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def stream_completion(prompt: str, context: str):
    """Yield response text incrementally as it arrives. Only nvidia streams
    natively here (same client/params as get_completion's nvidia branch);
    other providers yield their one complete response as a single chunk --
    this project's deployed LLM_PROVIDER is nvidia, so that's the real path.
    No retry wrapper here (unlike get_completion): a 5xx after we've already
    yielded partial text to the client can't be retried transparently.
    """
    provider = os.environ["LLM_PROVIDER"]
    if provider != "nvidia":
        yield get_completion(prompt, context)
        return

    model = os.environ["LLM_MODEL"]
    api_key = os.environ["LLM_API_KEY"]
    client = OpenAI(base_url=PROVIDERS["nvidia"], api_key=api_key, timeout=60)
    stream = client.chat.completions.create(
        model=model,
        temperature=0,
        top_p=1,
        max_tokens=16384,
        extra_body={"reasoning_budget": 16384},
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )
    for c in stream:
        if c.choices and c.choices[0].delta.content is not None:
            yield c.choices[0].delta.content


if __name__ == "__main__":
    # ponytail: smoke test only, needs real env/network to pass; asserts the contract shape
    assert set(PROVIDERS) == {"openrouter", "nvidia", "anthropic", "openai"}
    assert all(isinstance(v, str) for v in PROVIDERS.values())
    print("llm.py self-check ok")
