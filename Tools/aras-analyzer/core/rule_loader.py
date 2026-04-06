import yaml
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class Rule:
    rule_id:       str
    category:      str
    severity:      str
    routing:       str
    message:       str
    rule_detail:   str = ""
    reviewer_role: Optional[str] = None
    applies_to:    dict = field(default_factory=dict)
    extra:         dict = field(default_factory=dict)

    def applies_to_method(self, language: str, method_type: str) -> bool:
        if not self.applies_to:
            return True
        lang_match = self.applies_to.get("language", language) == language
        type_match = self.applies_to.get("method_type", method_type) == method_type
        return lang_match and type_match


class RuleLoader:
    KNOWN = {"severity","category","routing","message","rule_detail","reviewer_role","applies_to"}

    def __init__(self, rules_path: str):
        self.path = Path(rules_path)

    def load(self) -> list:
        if not self.path.exists():
            raise FileNotFoundError(f"Rules file not found: {self.path}")
        with open(self.path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        rules = []
        for cat_key, cat_body in raw.items():
            if not isinstance(cat_body, dict): continue
            for rule_key, body in cat_body.items():
                if not isinstance(body, dict): continue
                rules.append(self._build(cat_key, rule_key, body))
        return rules

    def _build(self, cat_key, rule_key, body):
        return Rule(
            rule_id      = f"{cat_key}.{rule_key}",
            category     = body.get("category", cat_key),
            severity     = body.get("severity", "warning"),
            routing      = body.get("routing", "auto_fail"),
            message      = body.get("message", ""),
            rule_detail  = (body.get("rule_detail") or "").strip(),
            reviewer_role= body.get("reviewer_role"),
            applies_to   = body.get("applies_to", {}),
            extra        = {k: v for k, v in body.items() if k not in self.KNOWN}
        )
