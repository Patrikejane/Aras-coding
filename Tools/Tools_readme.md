# Tools README

## 📁 Folder Structure

```
Tools/
├── CodeExtractor.py
├── XMLAnalyzer.py
├── rules.yaml
├── analysis_report.json
├── extraction_manifest.json
├── __pycache__/
│   └── XMLAnalyzer.cpython-313.pyc
└── extracted/
		├── cs/
		│   ├── HRDEESMthAutoGenerateCustomPartNumber.cs
		│   └── HRDEESMthValidatePartName.cs
		└── js/
				├── HRDEECMthCalculateTotalCost.js
				└── HRDEECMthShowPartInfo.js
```

## 🛠️  What the Tools Do

- `XMLAnalyzer.py` — The main analysis engine. It:
	- Parses Aras Innovator Method XML files.
	- Checks naming conventions (prefix `HRDEE`, indicators `SMth`/`CMth`, `Mth` presence, PascalCase).
	- Validates configuration completeness (`method_type`, `execution_allowed_to`, `language`, `method_code`).
	- Enforces Aras best practices (use of `getInnovator()`, presence of `return` statements, Server methods returning an `Item`).
	- Outputs a JSON report (`analysis_report.json`).

- `CodeExtractor.py` — Extracts raw method code from XML files and:
	- Saves C# methods to `extracted/cs/`.
	- Saves JavaScript methods to `extracted/js/`.
	- Produces an extraction manifest (`extraction_manifest.json`).

## Rules file (`rules.yaml`)

The analyzer's behavior is driven by `rules.yaml`. Key sections include:

- `naming_conventions` — checks naming rules and severities (e.g. `prefix: HRDEE`, presence of `SMth`/`CMth`, `Mth` token, PascalCase after `Mth`).
- `configuration_completeness` — enforces required XML configuration fields and their valid values (for example `method_type`, `execution_allowed_to`, `language`, and minimum `method_code` length).
- `aras_best_practices` — language-specific best-practice checks (e.g. `getInnovator()` usage for C#, presence of `return` statements, server methods returning an `Item`).

Example excerpt from `rules.yaml`:

```yaml
naming_conventions:
	prefix:
		value: "HRDEE"
		severity: "warning"
		message: "Method name does not follow HRDEE prefix convention"
	indicator:
		patterns: ["SMth", "CMth"]
		severity: "warning"
		message: "Method name lacks SMth/CMth indicator"

configuration_completeness:
	method_type:
		required: true
		valid_values: ["Server", "Client"]
		severity_missing: "error"
		severity_invalid: "warning"

aras_best_practices:
	getInnovator:
		language: "C#"
		method_type: "Server"
		severity: "info"
		message: "Server method should typically use getInnovator()"
	must_return_item:
		languages: ["C#"]
		method_type: "Server"
		severity: "error"
		message: "Server methods must return an Item object on every execution path"
```

Adjust `rules.yaml` to tune severities, required fields, or to add new checks for your environment.


## Notes
- The `extracted/` folder contains language-separated artifacts ready for static analysis (linters, security scanners, or CI pipelines).
- Use `analysis_report.json` for a summary of XML-based quality checks and to drive remediation prioritization.
- Use `extraction_manifest.json` to track extracted files and their paths.
