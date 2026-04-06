import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.rule_loader import RuleLoader
from core.code_reader import CodeReader
from core.llm_client  import LLMClient


class AnalyzerAgent:
    def __init__(self, rules_path, extracted_path, llm_config):
        self.rules_path     = rules_path
        self.extracted_path = extracted_path
        self.llm_client     = LLMClient(llm_config)

    def run(self) -> list:
        print("\n[AnalyzerAgent] Loading rules...")
        rules = RuleLoader(self.rules_path).load()
        print(f"  Loaded {len(rules)} rules")

        print("\n[AnalyzerAgent] Reading extracted method files...")
        methods = CodeReader(self.extracted_path).read_all()
        print(f"  Found {len(methods)} method(s)")

        results = []
        for method in methods:
            print(f"\n[AnalyzerAgent] Analysing: {method.name} ({method.language} / {method.method_type})")
            applicable = [r for r in rules if r.applies_to_method(method.language, method.method_type)]
            print(f"  Applying {len(applicable)}/{len(rules)} rules")
            issues = []
            for rule in applicable:
                result = self.llm_client.evaluate(method, rule)
                icon   = "VIOLATED" if result["violated"] else "ok      "
                print(f"    [{icon}] {rule.rule_id} (confidence: {result['llm_confidence']})")
                issues.append(result)
            results.append({"method": method, "issues": issues})

        return results
