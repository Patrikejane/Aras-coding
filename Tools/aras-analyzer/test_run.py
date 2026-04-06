import sys
sys.path.insert(0, ".")
from core.rule_loader import RuleLoader
from core.code_reader import CodeReader
from core.analyzer_agent import AnalyzerAgent
from core.report_builder import ReportBuilder

rules   = RuleLoader("config/rules.yaml").load()
methods = CodeReader("../extracted").read_all()

print(f"Rules loaded  : {len(rules)}")
print(f"Methods found : {len(methods)}")
for m in methods:
    print(f"  {m.name} | {m.language} | {m.method_type}")

print("\nRunning full analysis with mock provider...")
cfg = {"provider": "mock"}
agent   = AnalyzerAgent("config/rules.yaml", "../extracted", cfg)
results = agent.run()
builder = ReportBuilder("reports/analysis_report.json", source="local")
report  = builder.build(results)

s = report["summary"]
print(f"\n=== RESULT: {report['overall_status']} ===")
print(f"AUTO_FAIL    : {s['auto_fail']}")
print(f"NEEDS_REVIEW : {s['needs_review']}")
print(f"AUTO_PASS    : {s['auto_pass']}")
