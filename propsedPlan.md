╔══════════════════════════════════════════════════════════════════════╗
║                        SINGLE ANALYSIS ENGINE                        ║
║                                                                      ║
║   rules.yaml  ──►  LLM Agent  ◄──  extracted code (.cs / .js)        ║
║                        │                                             ║
║               analysis_report.json                                   ║
║               ┌─────────────┬──────────────┐────────────┐            ║
║               │  AUTO_FAIL  │ NEEDS_REVIEW │  AUTO_PASS │            ║
║               └─────────────┴──────────────┘────────────┘            ║
║                        │                │                            ║
╚════════════════════════╪════════════════╪════════════════════════════╝
                         │                │
          ┌──────────────▼──┐    ┌────────▼───────────────────┐
          │  LOCAL WEB UI   │    │   AZURE DEVOPS PIPELINE    │
          │                 │    │                            │
          │ • Load report   │    │ • Triggered on PR open     │
          │ • See all issues│    │ • Runs same engine         │
          │ • Reviewer      │    │ • Posts AUTO results as    │
          │   decides on    │    │   inline PR comments       │
          │   NEEDS_REVIEW  │    │ • NEEDS_REVIEW → assigned  │
          │ • Export final  │    │   to specific reviewer     │
          │   JSON          │    │ • AUTO_FAIL blocks merge   │
          └─────────────────┘    └────────────────────────────┘