import json
from datetime import datetime
from pathlib import Path

CONF_RANK = {"high": 3, "medium": 2, "low": 1}
ESCALATE_BELOW = "medium"


class ReportBuilder:
    def __init__(self, output_path: str, source: str = "local"):
        self.output_path = Path(output_path)
        self.source      = source

    def build(self, method_results: list, run_id: str = None) -> dict:
        run_id = run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
        summary = {"total_methods":0,"auto_fail":0,"needs_review":0,"auto_pass":0,
                   "reviewed_pass":0,"reviewed_fail":0}
        methods_out = []

        for entry in method_results:
            method = entry["method"]
            issues = [self._process(i) for i in entry["issues"]]
            status = self._method_status(issues)
            summary["total_methods"] += 1
            summary[{"AUTO_FAIL":"auto_fail","NEEDS_REVIEW":"needs_review"}.get(status,"auto_pass")] += 1
            methods_out.append({
                "method_name": method.name,
                "language":    method.language,
                "method_type": method.method_type,
                "source_file": method.source_file,
                "status":      status,
                "total_issues":len([i for i in issues if i["review_status"] != "AUTO_PASS"]),
                "issues":      issues
            })

        report = {
            "run_id":         run_id,
            "generated_at":   datetime.now().isoformat(),
            "source":         self.source,
            "overall_status": self._overall(summary),
            "summary":        summary,
            "methods":        methods_out
        }
        self._write(report)
        return report

    def _process(self, issue):
        violated   = issue.get("violated", False)
        routing    = issue.get("routing", "auto_fail")
        confidence = issue.get("llm_confidence", "low")

        if not violated:
            status = "AUTO_PASS"
        elif routing == "needs_review":
            status = "NEEDS_REVIEW"
        elif routing == "auto_fail":
            status = "NEEDS_REVIEW" if CONF_RANK.get(confidence,0) < CONF_RANK.get(ESCALATE_BELOW,2) else "AUTO_FAIL"
        else:
            status = "AUTO_PASS"

        result = {
            "rule_id":          issue["rule_id"],
            "category":         issue["category"],
            "severity":         issue["severity"],
            "routing":          routing,
            "message":          issue["message"],
            "violated":         violated,
            "llm_reasoning":    issue.get("llm_reasoning",""),
            "llm_confidence":   confidence,
            "suggested_fix":    issue.get("suggested_fix"),
            "llm_provider":     issue.get("llm_provider","unknown"),
            "review_status":    status,
            "reviewer_decision":None,
            "reviewer_comment": None
        }
        if status == "NEEDS_REVIEW":
            result["reviewer_role"] = issue.get("reviewer_role")
        return result

    def _method_status(self, issues):
        s = {i["review_status"] for i in issues}
        if "AUTO_FAIL"    in s: return "AUTO_FAIL"
        if "NEEDS_REVIEW" in s: return "NEEDS_REVIEW"
        return "AUTO_PASS"

    def _overall(self, s):
        if s["auto_fail"]    > 0: return "FAIL"
        if s["needs_review"] > 0: return "NEEDS_REVIEW"
        return "PASS"

    def _write(self, report):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"  [ReportBuilder] Report written -> {self.output_path}")
