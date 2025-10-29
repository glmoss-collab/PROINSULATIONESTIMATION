Google AI Studio upload package

Contents included:
- services/geminiService.ts           # canonical prompts & JSON schemas (spec + drawing)
- types.ts                            # TypeScript shapes used by frontend
- hvac_insulation_estimator.py        # Python estimator (demo runner)
- process_my_pdfs.py                  # PDF helper script
- pricebook_sample.json               # sample pricebook (fallback)
- .github/copilot-instructions.md     # AI-assistant onboarding (helpful in Studio)
- studio_wrapper.js                   # lightweight Node wrapper (paste schema & instruction into file)

How to use in Google AI Studio
1. Upload this ZIP to Studio Files.
2. Open a new Studio code cell (Node runtime) and paste the contents of `studio_wrapper.js` or upload it.
3. Open `services/geminiService.ts` and copy the `systemInstruction` string for `analyzeSpecification` into the wrapper's SYSTEM_INSTRUCTION variable.
4. Copy the `specAnalysisSchema` (and/or `drawingAnalysisSchema`) into the wrapper SPEC_SCHEMA variable.
5. Upload a sample PDF spec (spec_example.pdf) or drawing and call the wrapper function to get JSON output.

Notes
- If you have a supplier JSON pricebook (e.g., distribution_international_pricebook_2025_list.json), upload it to Studio Files too and reference it when running local demos.
- The wrapper is intentionally minimal — paste the full schema and instruction from `services/geminiService.ts` for strict JSON output.

Local testing
- To run locally you can use Node (install @google/genai) or run the Python estimator directly:

  .venv/bin/python hvac_insulation_estimator.py

If you'd like, I can also pre-fill the wrapper with the exact strings from `services/geminiService.ts` and create the final ZIP for you. Reply 'prefill' to have me embed the schema/instruction directly into the wrapper.
