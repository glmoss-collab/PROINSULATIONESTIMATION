// studio_wrapper.js
// Minimal Node wrapper to call Gemini model with a PDF file in Google AI Studio or locally.
// NOTE: Paste the full systemInstruction and spec/drawing schema from services/geminiService.ts
// into the SYSTEM_INSTRUCTION and SPEC_SCHEMA / DRAWING_SCHEMA constants below before running in Studio.

import fs from 'fs';
import path from 'path';
import { GoogleGenAI } from '@google/genai';

// Replace with your API key in environment or Studio settings
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || process.env.GEMINI_API_KEY });

// TODO: Paste full system instruction string from services/geminiService.ts
const SYSTEM_INSTRUCTION = `PASTE_SYSTEM_INSTRUCTION_HERE`;

// TODO: Paste the full JSON schema object for spec analysis
const SPEC_SCHEMA = {};

async function fileToGenerativePart(filePath) {
  const data = fs.readFileSync(filePath);
  return { inlineData: { data: data.toString('base64'), mimeType: 'application/pdf' } };
}

export async function analyzeSpec(filePath) {
  const filePart = await fileToGenerativePart(filePath);

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: { parts: [filePart] },
    config: {
      systemInstruction: SYSTEM_INSTRUCTION,
      responseMimeType: 'application/json',
      responseSchema: SPEC_SCHEMA,
    },
  });

  return JSON.parse(response.text);
}

// CLI convenience
if (require.main === module) {
  const arg = process.argv[2];
  if (!arg) {
    console.error('Usage: node studio_wrapper.js <spec.pdf>');
    process.exit(2);
  }
  analyzeSpec(arg).then(res => console.log(JSON.stringify(res, null, 2))).catch(err => console.error(err));
}
