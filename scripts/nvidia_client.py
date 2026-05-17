#!/usr/bin/env python3
"""
Hermes YouTube Growth OS — NVIDIA NIM Model Client
Uses OpenAI-compatible streaming SDK for NVIDIA inference.

Working Models:
- deepseek-ai/deepseek-v4-flash (fast, 1M context)
- qwen/qwen3-coder-480b-a35b-instruct (fast, 128K context)

Usage:
    python3 scripts/nvidia_client.py "Your prompt here"
    python3 scripts/nvidia_client.py --model deepseek-ai/deepseek-v4-flash "Prompt"
"""

import sys
import os
import json

# Add repo root to path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

def get_api_key():
    """Get NVIDIA API key from environment or .env file."""
    key = os.environ.get("NVIDIA_API_KEY", "")
    if not key:
        env_path = os.path.join(os.path.expanduser("~"), ".hermes", ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith("NVIDIA_API_KEY="):
                        key = line.strip().split("=", 1)[1].strip()
                        break
    return key


def chat(prompt, model="deepseek-ai/deepseek-v4-flash", system=None, max_tokens=4096, temperature=0.7, stream=True):
    """Send a chat completion request to NVIDIA NIM API."""
    from openai import OpenAI
    
    api_key = get_api_key()
    if not api_key:
        print("❌ NVIDIA_API_KEY not found. Set it in ~/.hermes/.env or environment.")
        sys.exit(1)
    
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )
    
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=0.8,
        max_tokens=max_tokens,
        stream=stream
    )
    
    if stream:
        full_response = ""
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
        print()  # Final newline
        return full_response
    else:
        response = completion.choices[0].message.content
        print(response)
        return response


def list_models():
    """List all available NVIDIA models."""
    import urllib.request
    
    api_key = get_api_key()
    if not api_key:
        print("❌ NVIDIA_API_KEY not found.")
        sys.exit(1)
    
    url = "https://integrate.api.nvidia.com/v1/models"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Hermes-YouTube-Growth-OS/1.0"
    })
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    
    print(f"📊 {len(data.get('data', []))} models available:\n")
    
    # Group by provider
    providers = {}
    for m in data.get("data", []):
        provider = m["owned_by"]
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(m["id"])
    
    for provider, models in sorted(providers.items()):
        print(f"\n🏢 {provider} ({len(models)} models):")
        for m in sorted(models):
            print(f"   - {m}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="NVIDIA NIM Model Client for Hermes")
    parser.add_argument("prompt", nargs="?", default=None, help="Prompt to send")
    parser.add_argument("--model", default="deepseek-ai/deepseek-v4-flash", help="Model to use")
    parser.add_argument("--system", default=None, help="System prompt")
    parser.add_argument("--max-tokens", type=int, default=4096, help="Max tokens")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    
    args = parser.parse_args()
    
    if args.list_models:
        list_models()
    elif args.prompt:
        chat(
            prompt=args.prompt,
            model=args.model,
            system=args.system,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            stream=not args.no_stream
        )
    else:
        parser.print_help()
