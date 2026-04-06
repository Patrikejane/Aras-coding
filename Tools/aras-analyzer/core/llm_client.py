import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.rule_loader import Rule
from core.code_reader import Method

SYSTEM_PROMPT = """You are a senior code reviewer specialising in Aras Innovator customisation.
Evaluate a single code snippet against a single rule and return a JSON verdict.
Respond with ONLY valid JSON — no markdown, no text outside the JSON.

Format:
{
  "violated": true | false,
  "reasoning": "Clear explanation referencing specific lines or patterns",
  "confidence": "high | medium | low",
  "suggested_fix": "Concrete fix, or null if not violated"
}"""


class LLMClient:
    def __init__(self, llm_config: dict):
        self.config   = llm_config
        self.provider = self._resolve()

    def evaluate(self, method: Method, rule: Rule) -> dict:
        prompt = (
            f"method_name: {method.name}\n"
            f"language: {method.language}\n"
            f"method_type: {method.method_type}\n"
            f"rule_id: {rule.rule_id}\n"
            f"rule_message: {rule.message}\n"
            f"rule_detail: {rule.rule_detail}\n\n"
            f"code:\n{method.code}\n\n"
            "Does this code violate the rule? Respond with JSON only."
        )
        try:
            raw    = self.provider.call(SYSTEM_PROMPT, prompt)
            parsed = self._parse(raw)
        except Exception as e:
            parsed = {"violated": False, "reasoning": f"LLM call failed: {e}", "confidence": "low", "suggested_fix": None}

        return {
            "rule_id":       rule.rule_id,
            "category":      rule.category,
            "severity":      rule.severity,
            "routing":       rule.routing,
            "reviewer_role": rule.reviewer_role,
            "message":       rule.message,
            "violated":      parsed.get("violated", False),
            "llm_reasoning": parsed.get("reasoning", ""),
            "llm_confidence":parsed.get("confidence", "low"),
            "suggested_fix": parsed.get("suggested_fix"),
            "llm_provider":  self.provider.name()
        }

    def _parse(self, raw):
        clean = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        try:
            return json.loads(clean)
        except:
            m = re.search(r"\{.*\}", clean, re.DOTALL)
            if m: return json.loads(m.group(0))
            raise ValueError(f"Cannot parse LLM response: {raw[:200]}")

    def _resolve(self):
        p = self.config.get("provider", "mock").lower()
        if p == "mock":
            from providers.mock_provider import MockProvider
            return MockProvider()
        elif p == "claude":
            from providers.claude_provider import ClaudeProvider
            return ClaudeProvider(self.config)
        elif p == "openai":
            from providers.openai_provider import OpenAIProvider
            return OpenAIProvider(self.config)
        elif p == "azure_openai":
            from providers.openai_provider import AzureOpenAIProvider
            return AzureOpenAIProvider(self.config)
        else:
            raise ValueError(f"Unknown provider: '{p}'. Use mock|claude|openai|azure_openai")
