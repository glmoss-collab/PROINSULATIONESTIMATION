<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/15RabTSs7Ap3rBj_xjSgY0L7x0ibyC596

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

## Process PDF Specifications Locally

If you have project specification PDFs that you want to scan for mechanical insulation
details, use the included helper script:

1. Install the dependency:
   `pip install pdfplumber`
2. Run the script with your PDF path:
   `python process_my_pdfs.py /path/to/specifications.pdf`

The script saves the extracted text alongside the PDF and highlights insulation-related
keywords, material types, and thickness references in the terminal output.
