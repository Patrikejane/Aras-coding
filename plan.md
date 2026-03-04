Perfect. Let me design the complete file structure plan before writing a single line of code.Good. I have your existing structure in full view. Now let me design everything.

---

## Complete File Structure Plan

```
D:\AI LLM\ARAS CODING\
│
├── AML-packages\                          (existing — source XMLs)
│
└── Tools\                                 (existing — your working directory)
    │
    ├── 📁 config\                         NEW — all configuration in one place
    │   ├── rules.yaml                     MOVED+EXTENDED from root
    │   ├── llm_config.yaml                NEW — LLM provider config
    │   └── pipeline_config.yaml           NEW — ADO + reviewer settings
    │
    ├── 📁 core\                           NEW — the analysis engine
    │   ├── __init__.py
    │   ├── code_reader.py                 NEW — reads extracted .cs/.js files
    │   ├── rule_loader.py                 NEW — parses rules.yaml into objects
    │   ├── llm_client.py                  NEW — provider-agnostic LLM wrapper
    │   ├── analyzer_agent.py              NEW — orchestrates the full analysis
    │   └── report_builder.py             NEW — builds final JSON report
    │
    ├── 📁 providers\                      NEW — swappable LLM backends
    │   ├── __init__.py
    │   ├── base_provider.py               NEW — abstract interface
    │   ├── claude_provider.py             NEW — Anthropic Claude
    │   ├── openai_provider.py             NEW — OpenAI / Azure OpenAI
    │   └── mock_provider.py              NEW — for testing without API calls
    │
    ├── 📁 devops\                         NEW — Azure DevOps integration
    │   ├── post_to_pr.py                  NEW — posts results to PR via ADO API
    │   ├── azure-pipelines.yml            NEW — pipeline definition
    │   └── pr_comment_templates.py        NEW — formats comments for PR display
    │
    ├── 📁 ui\                             NEW — local reviewer web UI
    │   ├── index.html                     NEW — single-file reviewer app
    │   ├── serve.py                       NEW — tiny local server (stdlib only)
    │   └── README.md                      NEW — how to run locally
    │
    ├── 📁 extracted\                      (existing — extracted .cs/.js files)
    │   ├── cs\
    │   └── js\
    │
    ├── 📁 reports\                        NEW — all outputs land here
    │   ├── analysis_report.json           was in root, now here
    │   ├── extraction_manifest.json       was in root, now here
    │   └── 📁 archive\                   NEW — timestamped historical reports
    │
    ├── 📁 tests\                          NEW — unit tests
    │   ├── test_rule_loader.py
    │   ├── test_analyzer.py
    │   └── fixtures\                      sample .cs/.js for test cases
    │
    ├── CodeExtractor.py                   (existing — keep as-is)
    ├── XMLAnalyzer.py                     (existing — keep as-is, will be superseded)
    ├── run_analysis.py                    NEW — single entry point CLI
    └── requirements.txt                   NEW — all Python dependencies
```

---

## What Each New File Does

### `config/` — Configuration Layer

**`rules.yaml` (extended from current)**
Every rule gets 3 new fields added:

```yaml
aras_best_practices:
  must_return_item:
    severity: "error"
    message: "Server methods must return an Item on every path"
    category: "aras_specific"        # ← NEW
    routing: "needs_review"          # ← NEW: auto_fail | needs_review | auto_pass
    reviewer_role: "ArasArchitect"   # ← NEW: who gets assigned

security:                            # ← NEW category entirely
  eval_usage:
    severity: "error"
    message: "eval() is a security risk — never use in Aras methods"
    category: "security"
    routing: "needs_review"
    reviewer_role: "SecurityTeam"
  sql_string_concat:
    severity: "error"
    message: "String concatenation in AML queries risks injection"
    category: "security"
    routing: "needs_review"
    reviewer_role: "SecurityTeam"

general_csharp:                      # ← NEW category
  no_null_check:
    severity: "warning"
    message: "getProperty() result used without null/empty check"
    category: "general"
    routing: "auto_fail"             # ← general rules = no human needed

general_javascript:                  # ← NEW category
  var_usage:
    severity: "warning"
    message: "Use let/const instead of var"
    category: "general"
    routing: "auto_fail"
  nan_not_checked:
    severity: "warning"
    message: "parseFloat/parseInt result not validated for NaN"
    category: "general"
    routing: "auto_fail"
```

**`llm_config.yaml`** — swap providers with one line:

```yaml
provider: "mock"           # mock | claude | openai | azure_openai
model: "claude-sonnet-4-20250514"
temperature: 0.1           # low = deterministic analysis
max_tokens: 2000
api_key_env: "LLM_API_KEY" # reads from environment variable, never hardcoded
```

**`pipeline_config.yaml`** — ADO + reviewer settings:

```yaml
ado:
  organization: "your-org"
  project: "your-project"
  block_on_auto_fail: true
  token_env: "SYSTEM_ACCESSTOKEN"

reviewers:
  ArasArchitect: "user@company.com"
  SecurityTeam:  "security@company.com"
```

---

### `core/` — The Engine

**`rule_loader.py`** — loads `rules.yaml` into typed Python objects. One job: give the rest of the system clean rule objects with `.rule_id`, `.severity`, `.routing`, `.reviewer_role`.

**`code_reader.py`** — reads the `extracted/` folder, returns a list of method objects: `{name, language, method_type, code, source_file}`. Replaces the parsing logic scattered in `XMLAnalyzer.py`.

**`llm_client.py`** — the key abstraction layer. Has one method: `evaluate(code, rules) → list[Issue]`. Internally delegates to whichever provider is configured. The rest of the engine never knows *which* LLM it's talking to.

**`analyzer_agent.py`** — the orchestrator. Calls `rule_loader` → `code_reader` → `llm_client` → `report_builder` in sequence. This is what `run_analysis.py` and the ADO pipeline both call.

**`report_builder.py`** — takes raw issues from the agent, builds the final `analysis_report.json` with correct `review_status`, `reviewer_decision: null` placeholders, and a top-level summary.

---

### `providers/` — Swappable LLM Backends

**`base_provider.py`** — abstract class with one method: `def call(prompt: str) -> str`. All providers implement this.

**`mock_provider.py`** — returns hardcoded responses. Use this for local development and unit tests — **zero API calls, zero cost.**

**`claude_provider.py` / `openai_provider.py`** — real implementations. Activated only when `llm_config.yaml` says so.

Swapping from Claude to Azure OpenAI = change one line in `llm_config.yaml`. No code changes.

---

### `devops/` — Azure DevOps Layer

**`post_to_pr.py`** — reads `reports/analysis_report.json`, groups issues by `routing`, and calls the ADO REST API:
- `AUTO_FAIL` → active thread, PR vote = Rejected
- `NEEDS_REVIEW` → active thread, @mentions `reviewer_role`
- All pass → summary comment, no block

**`azure-pipelines.yml`** — defines 4 pipeline steps: extract → analyze → post to PR → (optionally) archive report

**`pr_comment_templates.py`** — formats the comment text. Separated from the API logic so you can adjust comment wording without touching the API code.

---

### `ui/` — Local Reviewer UI

**`index.html`** — single HTML file, no framework needed. Loads `analysis_report.json`, renders:
- 🔴 AUTO_FAIL cards (read-only)
- 🟡 NEEDS_REVIEW cards with Pass/Fail buttons + comment box
- 🟢 AUTO_PASS summary
- **Export button** → saves updated JSON with `reviewer_decision` filled in

**`serve.py`** — 10-line Python HTTP server using stdlib only (`http.server`). Reviewer just runs `python serve.py` and opens `localhost:8080`. No npm, no installs.

---

### `run_analysis.py` — Single Entry Point

```
python run_analysis.py --input extracted/ --rules config/rules.yaml --output reports/
```

This is what both the developer runs locally AND what `azure-pipelines.yml` calls. One command, consistent behavior everywhere.

---

## Data Flow — End to End

```
AML-packages/*.xml
       │
       ▼
CodeExtractor.py  ──────────────────────────►  extracted/cs/*.cs
                                                extracted/js/*.js
                                                       │
                                                       ▼
                                              core/code_reader.py
                                                       │
                                              core/rule_loader.py  ◄──  config/rules.yaml
                                                       │
                                              core/llm_client.py   ◄──  config/llm_config.yaml
                                                       │             └──  providers/*.py
                                              core/report_builder.py
                                                       │
                                              reports/analysis_report.json
                                                       │
                              ┌────────────────────────┴──────────────────────┐
                              │                                               │
                              ▼                                               ▼
                     ui/index.html                               devops/post_to_pr.py
                   (local reviewer)                              (Azure DevOps PR)
```

---

## Report JSON Schema — Final Shape

```json
{
  "run_id": "20250305-143012",
  "source": "local | azure_devops",
  "llm_provider": "mock | claude | openai",
  "overall_status": "NEEDS_REVIEW",
  "summary": {
    "total_methods": 4,
    "auto_fail": 2,
    "needs_review": 3,
    "auto_pass": 1,
    "reviewed_pass": 0,
    "reviewed_fail": 0
  },
  "methods": [
    {
      "method_name": "HRDEESMthValidatePartName",
      "language": "C#",
      "method_type": "Server",
      "status": "NEEDS_REVIEW",
      "issues": [
        {
          "rule_id": "must_return_item",
          "category": "aras_specific",
          "severity": "error",
          "routing": "needs_review",
          "reviewer_role": "ArasArchitect",
          "llm_reasoning": "Method returns inn.newError() on empty name but has no return on success path — silent fall-through returns null, violating must-return-Item rule.",
          "llm_confidence": "high",
          "review_status": "NEEDS_REVIEW",
          "reviewer_decision": null,
          "reviewer_comment": null
        }
      ]
    }
  ]
}
```

---

## Build Order — When We Start Coding

| # | File(s) | Depends on | Can test with |
|---|---------|-----------|---------------|
| 1 | `config/rules.yaml` (extended) | nothing | manual read |
| 2 | `config/llm_config.yaml` | nothing | manual read |
| 3 | `providers/base_provider.py` + `mock_provider.py` | nothing | unit test |
| 4 | `core/rule_loader.py` + `core/code_reader.py` | rules.yaml, extracted/ | unit test |
| 5 | `core/llm_client.py` | providers/, mock | unit test, no API |
| 6 | `core/report_builder.py` | llm_client | unit test |
| 7 | `core/analyzer_agent.py` + `run_analysis.py` | all core/ | full local run |
| 8 | `ui/index.html` + `ui/serve.py` | report JSON | open in browser |
| 9 | `providers/claude_provider.py` | base_provider | real API test |
| 10 | `devops/post_to_pr.py` + `azure-pipelines.yml` | report JSON | ADO test PR |

Steps 1–8 require **no API key and no Azure account**. You build and validate the whole thing locally first.

---The structure is designed so every piece is independently testable — you never have to wait until everything is built to see it working. Steps 1–7 run fully offline with the mock provider, and the real LLM only gets wired in at Step 9 when you're ready to test with actual API calls.