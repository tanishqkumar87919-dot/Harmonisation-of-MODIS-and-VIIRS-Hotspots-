# Development Roadmap and Antigravity Agent Rules
## 1. Development Philosophy
Build the smallest scientifically correct end-to-end workflow first. Add the interface and advanced features only after the data pipeline and validation rules work.

## 2. Phased Roadmap
### Phase 0: Confirm requirements
Deliverables:
- Confirm study area and dates.
- Select exact MODIS and VIIRS products and versions.
- Confirm the research objective.
- Select sample datasets and document their fields.
- Approve the first matching policy and evaluation plan.

Acceptance: The team can explain what is being harmonised and how success will be measured.

### Phase 1: Repository and environment
Deliverables:
- Project folder structure.
- Dependency files.
- `.env.example` without real secrets.
- README with setup instructions.
- Formatting and test configuration.

Acceptance: A clean environment can install dependencies and run a health check.

### Phase 2: Data inspection and ingestion
Deliverables:
- Load sample source files.
- Validate schemas and values.
- Generate a quality report.
- Preserve source metadata.

Acceptance: Good, bad, empty, and unsupported files are handled predictably.

### Phase 3: Standardization
Deliverables:
- Product-specific field mappings.
- UTC timestamp handling.
- Coordinate validation.
- Raw-field preservation.

Acceptance: Standardized records remain traceable to original rows.

### Phase 4: Matching engine
Deliverables:
- Candidate generation.
- Configurable spatial/temporal rules.
- Ambiguity policy.
- Matched/unmatched outputs.
- Reproducible run metadata.

Acceptance: Unit tests cover thresholds, multiple candidates, and missing fields.

### Phase 5: Evaluation
Deliverables:
- Baseline comparisons.
- Threshold sensitivity analysis.
- Summary statistics and plots.
- Limitations statement.

Acceptance: Metrics are calculated from actual outputs, with definitions and denominators documented.

### Phase 6: API and persistence
Deliverables:
- API schemas.
- Processing-run endpoints.
- Database migrations if using a database.
- Error handling and logging.

Acceptance: API tests cover valid and invalid requests.

### Phase 7: Frontend and map
Deliverables:
- Dashboard.
- Dataset explorer.
- Harmonisation setup.
- Map layers and record details.
- Comparison and export views.

Acceptance: UI values match backend results and all states are handled.

### Phase 8: Integration and hardening
Deliverables:
- End-to-end tests.
- Security review.
- Performance check using a realistic dataset.
- Deployment guide.

Acceptance: A fresh setup can reproduce the demo from documented steps.

## 3. Antigravity Instructions
Use the following rules as persistent project guidance:
1. Read all documents in `docs/` before implementing features.
2. Treat the scientific methodology and product data dictionary as authoritative unless the team explicitly revises them.
3. Do not invent datasets, API responses, evaluation results, model accuracy, or citations.
4. Do not use mock data in production views. If mock data is used for layout testing, label it clearly and keep it separate from real processing.
5. Do not silently fall back to mock data when a source or API fails.
6. Preserve original observations and provenance.
7. Do not merge ambiguous detections without the documented policy.
8. Keep processing logic separate from UI components.
9. Add or update tests for every meaningful algorithm change.
10. Run tests and report their actual result; do not claim tests passed without running them.
11. Update the relevant document when a requirement or schema changes.
12. Do not overwrite or delete existing project files, data, configuration, or history without first inspecting and explaining the impact.
13. Use environment variables for secrets and keep `.env` files out of version control.
14. Implement one phase at a time and stop to report blockers or unresolved scientific decisions.
15. Commit changes in small, understandable units if Git is configured and the user requests or approves commits.

## 4. Suggested Repository Layout
```text
project/
  docs/
  frontend/
  backend/
    app/
      api/
      services/
      schemas/
      db/
    tests/
  data/
    samples/       # small, licensed and clearly labelled test fixtures only
  scripts/
  .env.example
  .gitignore
  README.md
```

Adapt this layout to the actual framework; do not create empty folders that serve no purpose.

## 5. Task Tracker Template
For each task record:
- Task ID
- Description
- Owner
- Status: pending / in progress / blocked / complete
- Dependencies
- Acceptance criteria
- Test evidence
- Related document

Never mark a task complete merely because code was generated.
