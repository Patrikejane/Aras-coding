import json
import re
from .base_provider import BaseProvider


class MockProvider(BaseProvider):
    """
    Mock LLM provider — no API calls, used for local dev and tests.
    Driven by keyword detection so tests get varied, meaningful output.
    """

    def call(self, system_prompt: str, user_prompt: str) -> str:
        rule_id = self._extract(user_prompt, "rule_id")
        code    = self._extract(user_prompt, "code")
        violated, reasoning, confidence, suggestion = self._evaluate(rule_id, code)
        return json.dumps({
            "violated": violated,
            "reasoning": reasoning,
            "confidence": confidence,
            "suggested_fix": suggestion
        })

    def _extract(self, text, field):
        m = re.search(rf"{field}:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    def _evaluate(self, rule_id, code):
        r = rule_id.lower()
        c = code.lower()

        if "must_return_item" in r or "return_item" in r:
            if "return" not in c:
                return (True, "No return statement found. Server methods must return an Item on every path.", "high",
                        "Add 'return part;' at the end of the success path.")
            if not re.search(r'return\s+\w+\s*;?\s*$', code.strip()):
                return (True, "Return exists inside a branch but not on every code path. Silent fall-through returns null.", "high",
                        "Ensure every code path ends with a return statement.")
            return (False, "Method returns an Item on all observed paths.", "high", None)

        if "getinnovator" in r:
            if "getinnovator" not in c:
                return (True, "getInnovator() is not called. Server methods need the Innovator context.", "medium",
                        "Add: Innovator inn = this.getInnovator();")
            return (False, "getInnovator() is present.", "high", None)

        if "null_check" in r or "getproperty_default" in r:
            if "getproperty" in c and '""' not in code and "''" not in code:
                return (True, "getProperty() called without a default value. Returns null if property is missing.", "medium",
                        'Provide a default: getProperty("fieldName", "")')
            return (False, "getProperty() includes a default value.", "high", None)

        if "var_usage" in r:
            if re.search(r'\bvar\b', code):
                return (True, "var declarations found. var has function-scoped hoisting that causes subtle bugs.", "high",
                        "Replace var with let (mutable) or const (immutable).")
            return (False, "No var declarations found.", "high", None)

        if "nan" in r:
            has_parse = "parsefloat" in c or "parseint" in c
            has_check = "isnan" in c
            if has_parse and not has_check:
                return (True, "parseFloat/parseInt used without isNaN() validation. Empty values silently produce NaN.", "high",
                        "Add: if (isNaN(value)) { aras.AlertError('Invalid number'); return; }")
            return (False, "Numeric parsing is validated or not present.", "high", None)

        if "eval" in r:
            if "eval(" in c:
                return (True, "eval() detected — critical security vulnerability.", "high",
                        "Remove eval() entirely. There is no safe use of eval in Aras methods.")
            return (False, "No eval() usage detected.", "high", None)

        if "credential" in r or "hardcoded" in r:
            if any(p in c for p in ["password", "secret", "apikey", "api_key", "token ="]):
                return (True, "Potential hardcoded credential detected. Credentials in source code are exposed in version history.", "medium",
                        "Move credentials to environment variables or Azure Key Vault.")
            return (False, "No obvious hardcoded credentials detected.", "medium", None)

        if "datetime" in r:
            if "datetime.now" in c and "datetime.utcnow" not in c:
                return (True, "DateTime.Now uses local server time. Aras servers may differ in timezone from users.", "medium",
                        "Use DateTime.UtcNow for database timestamps.")
            return (False, "No DateTime.Now usage or already using UtcNow.", "high", None)

        if "empty_catch" in r:
            if re.search(r'catch\s*\([^)]*\)\s*\{\s*\}', code):
                return (True, "Empty catch block found. Exceptions are silently swallowed.", "high",
                        "Return inn.newError(ex.Message) inside the catch block.")
            return (False, "No empty catch blocks detected.", "high", None)

        if "string_concat" in r:
            if '"+' in code or '+ "' in code:
                return (True, "String concatenation used for display output. Template literals are cleaner.", "low",
                        "Use template literals: `Part: ${partNumber} - ${partName}`")
            return (False, "No string concatenation issues detected.", "high", None)

        if "no_error_handling" in r:
            if "try" not in c and "catch" not in c:
                return (True, "No try/catch found. Uncaught exceptions display a generic Aras error dialog.", "medium",
                        "Wrap method logic in try { ... } catch(e) { aras.AlertError(e.message); }")
            return (False, "Error handling is present.", "high", None)

        # Default
        return (False, f"Mock: no specific check for '{rule_id}'. Defaulting to pass.", "low", None)

    def name(self):
        return "mock"
