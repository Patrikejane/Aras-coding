import os, json, urllib.request, urllib.error
from .base_provider import BaseProvider

class OpenAIProvider(BaseProvider):
    def __init__(self, config):
        self.model       = config.get("model", "gpt-4o")
        self.max_tokens  = config.get("max_tokens", 2000)
        self.temperature = config.get("temperature", 0.1)
        env_var          = config.get("api_key_env", "LLM_API_KEY")
        self.api_key     = os.environ.get(env_var, "")
        if not self.api_key:
            raise EnvironmentError(f"OpenAI: API key not found in env var '{env_var}'.")
        self.base_url = config.get("openai", {}).get("base_url", "https://api.openai.com/v1")

    def _url(self):     return f"{self.base_url}/chat/completions"
    def _headers(self): return {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

    def call(self, system_prompt, user_prompt):
        payload = json.dumps({
            "model": self.model, "temperature": self.temperature, "max_tokens": self.max_tokens,
            "messages": [{"role": "system", "content": system_prompt},
                         {"role": "user",   "content": user_prompt}]
        }).encode("utf-8")
        req = urllib.request.Request(self._url(), data=payload, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"OpenAI API {e.code}: {e.read().decode()}")

    def name(self): return "openai"


class AzureOpenAIProvider(OpenAIProvider):
    def __init__(self, config):
        super().__init__(config)
        az = config.get("azure_openai", {})
        self.deployment  = az.get("deployment_name", "gpt-4o")
        self.api_version = az.get("api_version", "2024-02-01")
        ep_env  = az.get("base_url_env", "AZURE_OPENAI_ENDPOINT")
        ep      = os.environ.get(ep_env, "")
        if not ep:
            raise EnvironmentError(f"Azure OpenAI: endpoint not found in env var '{ep_env}'.")
        self.base_url = ep.rstrip("/")

    def _url(self):
        return f"{self.base_url}/openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"

    def _headers(self):
        return {"Content-Type": "application/json", "api-key": self.api_key}

    def name(self): return "azure_openai"
