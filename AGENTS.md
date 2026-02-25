# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is an HVAC insulation estimation system with two independent frontend surfaces and a Python core engine. See `CLAUDE.md` for comprehensive architecture and API docs.

### Services

| Service | Command | Port | Notes |
|---|---|---|---|
| Streamlit (primary UI) | `PYTHONPATH=/workspace streamlit run agent_estimation_app.py` | 8501 | Requires `ANTHROPIC_API_KEY` for AI features |
| React/Vite (alternate UI) | `npm run dev` | 3000 | Requires `GEMINI_API_KEY` for AI features |

### Running tests

```bash
# All Python tests (must set PYTHONPATH)
PYTHONPATH=/workspace pytest tests/ test_easiest_workflow.py -v

# TypeScript build check
npx vite build
```

### Important gotchas

- **Pydantic version**: The codebase uses Pydantic v1-style validators (`@root_validator`, `@validator`). You must use `pydantic==1.10.x` (not v2). The `requirements.txt` says `>=2.0.0` but tests fail with any Pydantic v2 version due to the deprecated `@root_validator` without `skip_on_failure=True`.
- **PYTHONPATH**: Must be set to `/workspace` when running tests or the Streamlit app, otherwise `pydantic_models` and other root-level modules won't be found.
- **`~/.local/bin` on PATH**: pip installs `streamlit`, `pytest`, etc. to `~/.local/bin`. Ensure it's on `PATH`.
- **API keys are optional for dev**: Both apps load and serve their UIs without API keys. AI features (chat, PDF analysis) require `ANTHROPIC_API_KEY` (Streamlit) and `GEMINI_API_KEY` (React app).
- **Figma plugin** (`figma-plugin/`) is optional and only usable inside Figma Desktop. Its TypeScript won't pass `tsc --noEmit` from the root because it depends on `@figma/plugin-typings`.
- **GCP services** (Firestore, GCS, Secret Manager) all have local fallbacks — no GCP project needed for local dev.
