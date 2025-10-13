import { GoogleGenAI, Type, GenerateContentResponse } from "@google/genai";
import type { GeminiSpecAnalysis, GeminiDrawingAnalysis } from '../types';

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

const fileToGenerativePart = async (file: File) => {
  const base64EncodedDataPromise = new Promise<string>((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
    reader.readAsDataURL(file);
  });
  return {
    inlineData: { data: await base64EncodedDataPromise, mimeType: file.type },
  };
};

const specAnalysisSchema = {
  type: Type.OBJECT,
  properties: {
    ductwork: {
      type: Type.OBJECT,
      properties: {
        material: { type: Type.STRING },
        thickness: { type: Type.STRING },
        facing: { type: Type.STRING },
      },
    },
    piping: {
      type: Type.OBJECT,
      properties: {
        material: { type: Type.STRING },
        thickness: { type: Type.STRING },
        jacketing: { type: Type.STRING },
      },
    },
    outdoor: {
        type: Type.OBJECT,
        properties: {
            jacketing: { type: Type.STRING },
            requirements: { type: Type.STRING },
        },
    },
    summary: {
      type: Type.STRING,
      description: "A brief summary of all key insulation requirements.",
    },
  },
};

const drawingAnalysisSchema = {
    type: Type.OBJECT,
    properties: {
        ductwork: {
            type: Type.ARRAY,
            items: {
                type: Type.OBJECT,
                properties: {
                    size: { type: Type.STRING, description: "e.g., '24x20'" },
                    length: { type: Type.NUMBER, description: "Linear feet" },
                    fittings: { type: Type.NUMBER, description: "Count of elbows, tees, etc." },
                }
            }
        },
        piping: {
            type: Type.ARRAY,
            items: {
                type: Type.OBJECT,
                properties: {
                    size: { type: Type.STRING, description: "e.g., '2\" CHW'" },
                    length: { type: Type.NUMBER, description: "Linear feet" },
                    fittings: { type: Type.NUMBER, description: "Count of elbows, valves, etc." },
                }
            }
        },
        scale: { type: Type.STRING, description: "Drawing scale, e.g., '1/4\" = 1'-0\"'" },
        notes: { type: Type.STRING, description: "Any important notes, ambiguities, or areas of concern." }
    }
};

const sanitizeJsonText = (raw: string): string => {
  let cleaned = raw.trim();

  if (cleaned.startsWith('```')) {
    cleaned = cleaned.replace(/^```(?:json)?/i, '').replace(/```$/, '').trim();
  }

  const braceStart = cleaned.indexOf('{');
  const braceEnd = cleaned.lastIndexOf('}');
  const bracketStart = cleaned.indexOf('[');
  const bracketEnd = cleaned.lastIndexOf(']');

  if (braceStart !== -1 && braceEnd !== -1 && braceStart < braceEnd) {
    cleaned = cleaned.slice(braceStart, braceEnd + 1);
  } else if (bracketStart !== -1 && bracketEnd !== -1 && bracketStart < bracketEnd) {
    cleaned = cleaned.slice(bracketStart, bracketEnd + 1);
  }

  return cleaned.trim();
};

const extractResponseText = (response: GenerateContentResponse): string => {
  if (response.promptFeedback?.blockReason) {
    throw new Error(`Gemini blocked the request: ${response.promptFeedback.blockReason}`);
  }

  const segments: string[] = [];

  if (response.text?.trim()) {
    segments.push(response.text.trim());
  }

  const candidates = response.candidates;
  if (candidates) {
    for (const candidate of candidates) {
      const parts = candidate.content?.parts;
      if (!parts) continue;
      for (const part of parts) {
        if ('text' in part && part.text?.trim()) {
          segments.push(part.text.trim());
        }
      }
    }
  }

  const combined = segments.join('\n').trim();

  if (!combined) {
    throw new Error('Gemini response did not include any text content to parse.');
  }

  return combined;
};

const parseJsonResponse = <T>(response: GenerateContentResponse): T => {
  const rawText = extractResponseText(response);
  const jsonText = sanitizeJsonText(rawText);

  try {
    return JSON.parse(jsonText) as T;
  } catch (error) {
    console.error('Failed to parse Gemini JSON response:', error, '\nRaw response:', rawText);
    throw new Error('Unable to parse Gemini response as JSON.');
  }
};

export const analyzeSpecification = async (file: File): Promise<GeminiSpecAnalysis> => {
  const systemInstruction = "You are an AI-powered HVAC mechanical insulation estimation service for Guaranteed Insulation. Respond ONLY with the JSON object as defined by the schema.";
  
  const userPrompt = `Analyze this specification PDF (Division 23) and extract key insulation requirements.
    Focus on material types, thickness, and facing/jacketing for each system (ductwork, piping).
    Note any special requirements like mastic, vapor barriers, or outdoor weatherproofing. Provide a concise summary.`;

  const parts = [
    { text: userPrompt },
    await fileToGenerativePart(file),
  ];
  
  const response: GenerateContentResponse = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: [{ role: 'user', parts: parts }],
    config: {
      systemInstruction: systemInstruction,
      responseMimeType: 'application/json',
      responseSchema: specAnalysisSchema,
    },
  });

  return parseJsonResponse<GeminiSpecAnalysis>(response);
};

export const analyzeDrawings = async (file: File): Promise<GeminiDrawingAnalysis> => {
    const systemInstruction = "You are an AI-powered HVAC mechanical insulation estimation service. Your goal is to perform a takeoff for ductwork and piping from the provided drawings. Respond ONLY with the JSON object as defined by the schema.";
    
    const userPrompt = `Analyze these construction drawings (PDF).
      Identify sizes (e.g., "18x12" or '2" CHW'), measure linear feet for each size, and count fittings (elbows, tees).
      Note the drawing scale. Summarize your findings in the JSON format.
      Be as accurate as possible with quantities. If a scale is not present, assume 1/4" = 1'-0" for mechanical plans.`;

    const parts = [
      { text: userPrompt },
      await fileToGenerativePart(file),
    ];

    const response: GenerateContentResponse = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: [{ role: 'user', parts: parts }],
        config: {
            systemInstruction: systemInstruction,
            responseMimeType: 'application/json',
            responseSchema: drawingAnalysisSchema,
        }
    });

    return parseJsonResponse<GeminiDrawingAnalysis>(response);
};