# Aras Innovator LLM Static Analysis System
## Architecture & Build Plan

**Project:** Aras Method Code Static Analysis with LLM + Azure DevOps PR Integration
**Date:** 2025-03-05
**Status:** Planning Complete — Ready to Build

---

## 1. Vision Summary

A static analysis system that:
- Analyzes extracted Aras Innovator C# and JavaScript method code
- Uses an LLM to evaluate code against a defined ruleset (reasoning-based, not regex)
- Routes issues automatically: AUTO_FAIL, AUTO_PASS, or NEEDS_REVIEW
- Surfaces results in a **local web UI** for developer/architect review
- Posts results directly into **Azure DevOps Pull Request** comments
- Blocks PR merge on AUTO_FAIL issues
- Assigns NEEDS_REVIEW issues to named reviewers in ADO

---

## 2. Complete File Structure

```
Tools\
    config\                      NEW
        rules.yaml               MOVED+EXTENDED from root
        llm_config.yaml          LLM provider config
        pipeline_config.yaml     ADO + reviewer settings
    core\                        NEW — analysis engine
        __init__.py
        code_reader.py           reads extracted .cs/.js files
        rule_loader.py           parses rules.yaml into objects
        llm_client.py            provider-agnostic LLM wrapper
        analyzer_agent.py        orchestrates full analysis
        report_builder.py        builds final JSON report
    providers\                   NEW — swappable LLM backends
        __init__.py
        base_provider.py         abstract interface
        claude_provider.py       Anthropic Claude
        openai_provider.py       OpenAI / Azure OpenAI
        mock_provider.py         for testing — zero API cost
    devops\                      NEW — Azure DevOps integration
        post_to_pr.py            posts results via ADO REST API
        azure-pipelines.yml      pipeline definition
        pr_comment_templates.py  formats PR comment text
    ui\                          NEW — local reviewer web UI
        index.html               single-file reviewer app
        serve.py                 local HTTP server (stdlib only)
        README.md                how to run locally
    extracted\                   (existing — .cs/.js files)
        cs\
        js\
    reports\                     NEW — all outputs land here
        analysis_report.json
        extraction_manifest.json
        archive\                 timestamped historical reports
    tests\                       NEW — unit tests
        test_rule_loader.py
        test_analyzer.py
        fixtures\                sample .cs/.js test files
    CodeExtractor.py             (existing — unchanged)
    XMLAnalyzer.py               (existing — superseded)
    run_analysis.py              NEW — single CLI entry point
    requirements.txt             NEW — Python dependencies
```

---

## 3. Rule Routing System

Every rule in rules.yaml gets 3 new fields:

| Field | Values | Purpose |
|---|---|---|
| category | naming, config, aras_specific, general, security | Groups related rules |
| routing | auto_fail, needs_review, auto_pass | Determines what happens when violated |
| reviewer_role | ArasArchitect, SecurityTeam, null | Who gets assigned in ADO PR |

### Routing Logic

| routing | LLM finds violation | Result |
|---|---|---|
| auto_fail | yes | Issue marked AUTO_FAIL — PR blocked, no human needed |
cd "/d/AI LLM/ARAS CODING/Tools/aras-analyzer" && C*/Python313/python.exe test_run.py
| auto_pass | yes | Informational only — never blocks anything |
| any | no | Issue marked AUTO_PASS |

### Rule Categories and Their Routing

| Category | Default Routing | Reviewer |
|---|---|---|
| naming | auto_fail | none |
| config | auto_fail | none |
| general (C# / JS) | auto_fail | none |
| aras_specific | needs_review | ArasArchitect |
| security | needs_review | SecurityTeam |

