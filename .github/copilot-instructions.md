# Copilot instructions for HVAC Insulation Estimator

Purpose: Help an AI coding assistant be productive quickly in this repository by documenting the architecture, developer workflows, conventions, and integration points.

Quick start (developer-focused)
- Frontend: Node + Vite (React). Install and run:
  - npm install
  - npm run dev
- Backend / CLI utilities (Python): create a venv and install required PDF/CV libs when needed. Typical packages used by scripts:
  - pdfplumber, pdf2image, pillow, numpy, opencv-python
  - Example (macOS): python -m venv .venv && .venv/bin/pip install pdfplumber pdf2image pillow numpy opencv-python
- Environment: Frontend expects a Gemini API key in a local env file. README references `.env.local` and the UI code (services/geminiService.ts) reads process.env.API_KEY — confirm which key name to set (GEMINI_API_KEY vs API_KEY) before testing.

Big-picture architecture
- Single-repo multi-runtime project:
  - Frontend: React + Vite (TypeScript). Key entry points: `index.tsx`, `App.tsx`, and `estimator.ts`.
  - Browser AI integration: `services/geminiService.ts` orchestrates calls to Google GenAI, defines JSON schemas used by the UI, and contains the canonical extraction prompts and validation schema.
  - Python CLI/processing: `hvac_insulation_estimator.py` and `process_my_pdfs.py` provide offline/CLI tools for PDF spec parsing, drawing measurement (optional CV), pricing and quote generation.

Key files and responsibilities (use these as anchors when making edits)
- `hvac_insulation_estimator.py` — core Python domain model (dataclasses: InsulationSpec, MeasurementItem, MaterialItem, ProjectQuote), extraction logic (pdfplumber), optional CV-based measurement (pdf2image + cv2), pricing engine and quote generation. Prefer touching here for algorithm changes.
- `process_my_pdfs.py` — helper script to extract text from spec PDFs (non-AI path). Good for adding rule-based patterns.
- `services/geminiService.ts` — front-end AI orchestration. Contains the JSON response schemas used by the UI and functions: `analyzeSpecification`, `analyzeDrawings`, `generatePreviewFromSpec`. If you change JSON shapes, update `types.ts` and the UI consumer code.
- `types.ts` — TypeScript data shapes used throughout the frontend. Keep these consistent with the schemas in `geminiService.ts`.
- `estimator.ts` — front-end logic that converts AI outputs / UI inputs into quotes via the same business rules as the Python `PricingEngine`.

Patterns & conventions you should follow
- Data models are explicit: Python uses dataclasses; frontend uses typed interfaces in `types.ts`. When adding fields, update both sides if cross-runtime compatibility is required.
- Pricing keys are string-concatenations like `"{material}_{thickness}"` (e.g., `fiberglass_1.5`) — ensure thickness formatting matches keys in `PricingEngine._load_prices`.
- Optional dependency pattern: `hvac_insulation_estimator.py` dynamically imports `cv2` and `numpy` with fallbacks; new features that require optional native libs should follow this pattern and degrade gracefully.
- AI schema-first approach: `services/geminiService.ts` defines strict response schemas for spec/drawing analysis. When changing prompts or expected JSON fields, update the schema and the consumer code that parses it.

Developer workflows and debugging
- Frontend dev: use `npm run dev` (Vite). Build artifacts: `npm run build` and preview with `npm run preview`.
- Python CLI: run the main demo with the project's venv Python: `.venv/bin/python hvac_insulation_estimator.py` or `python hvac_insulation_estimator.py` after activating your virtualenv. For PDF processing tests use `python process_my_pdfs.py /path/to/spec.pdf` (README shows this flow).
- If adding CV features, test in an environment with `opencv-python` and `pdf2image` plus the `poppler` system dependency (pdf2image requires poppler on macOS: `brew install poppler`).

Integration notes & gotchas
- Environment variable mismatch: README suggests `GEMINI_API_KEY` but `services/geminiService.ts` reads `process.env.API_KEY`. Verify which variable the deployed environment uses and align `.env.local` accordingly.
- AI contract: `geminiService.ts` enforces a JSON schema. AI responses are parsed as JSON — keep prompts deterministic and schemas strict to avoid parsing errors.
- Pricebook location: `PricingEngine._load_prices` can read a JSON file if provided; otherwise it uses the built-in default price map. Use a well-formatted JSON file with keys like `fiberglass_1.5` to override prices.
- Scale detection: drawing scale parsing in Python uses simple regexes and returns a default (48) if detection fails. Be cautious when modifying `_parse_scale` — many drawing formats exist.

When opening PRs
- Update both runtime sides for shared contracts (types/schema). Example: if adding `special_requirements` detail that frontend needs, change `hvac_insulation_estimator.py`, `services/geminiService.ts` schema, and `types.ts`.
- Add a short test or example run: for Python changes include a tiny script/CLI example that demonstrates the behavior using local JSON or the manual examples already in `hvac_insulation_estimator.py`.

If something is missing
- Ask for the expected runtime (local dev vs production) and whether AI key naming should be `API_KEY` or `GEMINI_API_KEY`. Also request sample PDFs or pricebook JSON when implementing new extraction or pricing rules.

End — ask me what parts you'd like expanded or to include example commands for (venv setup, Poppler install, or example pricebook file).
