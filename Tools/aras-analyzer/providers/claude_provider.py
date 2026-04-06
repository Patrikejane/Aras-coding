import os, json, urllib.request, urllib.error
from .base_provider import BaseProvider

class ClaudeProvider(BaseProvider):
    BASE_URL    = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"

    def __init__(self, config):
        self.model      = config.get("model", "claude-sonnet-4-20250514")
        self.max_tokens = config.get("max_tokens", 2000)
        self.temperature= config.get("temperature", 0.1)
        env_var         = config.get("api_key_env", "LLM_API_KEY")
        self.api_key    = os.environ.get(env_var, "")
        if not self.api_key:
            raise EnvironmentError(f"Claude: API key not found in env var '{env_var}'.")

    def call(self, system_prompt, user_prompt):
        payload = json.dumps({
            "model": self.model, "max_tokens": self.max_tokens,
            "temperature": self.temperature, "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }).encode("utf-8")
        headers = {"Content-Type": "application/json",
                   "x-api-key": self.api_key,
                   "anthropic-version": self.API_VERSION}
        req = urllib.request.Request(self.BASE_URL, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())["content"][0]["text"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Claude API {e.code}: {e.read().decode()}")

    def name(self): return "claude"
