"""
run_analysis.py  -  Aras Innovator LLM Static Analyser
=======================================================
Usage:
  python run_analysis.py
  python run_analysis.py --extracted "..\extracted" --archive
  python run_analysis.py --provider claude
"""
import sys, argparse, yaml, shutil
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

from core.analyzer_agent import AnalyzerAgent
from core.report_builder  import ReportBuilder


def load_yaml(p):
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def print_summary(report):
    s    = report["summary"]
    icon = {"PASS":"v","NEEDS_REVIEW":"~","FAIL":"X"}.get(report["overall_status"],"?")
    print("\n" + "="*60)
    print(f"  ANALYSIS COMPLETE  [{icon}] {report['overall_status']}")
    print("="*60)
    print(f"  Methods  : {s['total_methods']}")
    print(f"  [X] AUTO_FAIL    : {s['auto_fail']}")
    print(f"  [~] NEEDS_REVIEW : {s['needs_review']}")
    print(f"  [v] AUTO_PASS    : {s['auto_pass']}")
    print("="*60)
    for m in report.get("methods", []):
        i = {"AUTO_FAIL":"X","NEEDS_REVIEW":"~","AUTO_PASS":"v"}.get(m["status"],"?")
        print(f"\n  [{i}] {m['method_name']}  ({m['language']})")
        for issue in m.get("issues", []):
            if issue["review_status"] == "AUTO_PASS": continue
            print(f"      [{issue['severity'].upper()}] {issue['rule_id']}")
            print(f"             {issue['llm_reasoning'][:120]}")
            if issue.get("suggested_fix"):
                print(f"             Fix: {issue['suggested_fix'][:100]}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--extracted",  default=str(BASE.parent / "extracted"))
    p.add_argument("--rules",      default=str(BASE / "config" / "rules.yaml"))
    p.add_argument("--llm-config", default=str(BASE / "config" / "llm_config.yaml"))
    p.add_argument("--output",     default=str(BASE / "reports" / "analysis_report.json"))
    p.add_argument("--provider",   default=None)
    p.add_argument("--source",     default="local", choices=["local","azure_devops"])
    p.add_argument("--archive",    action="store_true")
    args = p.parse_args()

    print("\n  Aras Innovator LLM Static Analyser")
    print(f"  Extracted : {args.extracted}")
    print(f"  Rules     : {args.rules}")

    cfg = load_yaml(args.llm_config)
    if args.provider:
        cfg["provider"] = args.provider

    print(f"  Provider  : {cfg.get('provider','mock')}")

    run_id  = datetime.now().strftime("%Y%m%d-%H%M%S")
    agent   = AnalyzerAgent(rules_path=args.rules, extracted_path=args.extracted, llm_config=cfg)
    results = agent.run()

    builder = ReportBuilder(output_path=args.output, source=args.source)
    report  = builder.build(results, run_id=run_id)

    if args.archive:
        arc = Path(args.output).parent / "archive" / f"analysis_report_{run_id}.json"
        arc.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.output, arc)
        print(f"  Archived -> {arc}")

    print_summary(report)

    sys.exit(1 if report["overall_status"] == "FAIL" else 0)


if __name__ == "__main__":
    main()
