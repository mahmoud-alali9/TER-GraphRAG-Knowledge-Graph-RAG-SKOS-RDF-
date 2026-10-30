import os
from groq import Groq
from openai import OpenAI

from workflow.tracing import traceable

_groq_client    = None
_together_client = None
_mistral_client  = None

def _get_groq():
    global _groq_client
    if _groq_client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY missing in .env")
        _groq_client = Groq(api_key=key)
    return _groq_client

def _get_together():
    global _together_client
    if _together_client is None:
        key = os.getenv("TOGETHER_API_KEY")
        if not key:
            raise ValueError("TOGETHER_API_KEY missing in .env")
        _together_client = OpenAI(api_key=key, base_url="https://api.together.xyz/v1")
    return _together_client

def _get_mistral():
    global _mistral_client
    if _mistral_client is None:
        key = os.getenv("MISTRAL_API_KEY")
        if not key:
            raise ValueError("MISTRAL_API_KEY missing in .env")
        # Mistral API is OpenAI-compatible
        _mistral_client = OpenAI(api_key=key, base_url="https://api.mistral.ai/v1")
    return _mistral_client

@traceable(name="ask_llm", run_type="llm")
def ask_llm(prompt, system=None, temperature=0.1, model=None, stream=False):
    backend = os.getenv("LLM_BACKEND", "groq").lower()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    if backend == "mistral":
        if model is None:
            model = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
        resp = _get_mistral().chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=stream,
        )
        if stream:
            return resp
        return resp.choices[0].message.content

    elif backend == "together":
        if model is None:
            model = os.getenv("TOGETHER_MODEL", "meta-llama/Llama-3.3-70B-Instruct-Turbo")
        resp = _get_together().chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=stream,
        )
        if stream:
            return resp
        return resp.choices[0].message.content

    else:
        if model is None:
            model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        resp = _get_groq().chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=stream,
        )
        if stream:
            return resp
        return resp.choices[0].message.content