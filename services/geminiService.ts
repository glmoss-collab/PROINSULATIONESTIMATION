
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
        projectInfo: {
            type: Type.OBJECT,
            description: "Project identification details, typically found on the cover sheet.",
            properties: {
                projectName: { type: Type.STRING, description: "The official name of the project." },
                location: { type: Type.STRING, description: "The city and state, or full address of the project." },
                customer: { type: Type.STRING, description: "The name of the client, General Contractor, or Mechanical Contractor." },
                date: { type: Type.STRING, description: "The specification issue date, in YYYY-MM-DD format." },
            }
        },
        ductworkSystems: {
            type: Type.ARRAY,
            description: "Detailed insulation requirements for each type of ductwork system.",
            items: {
                type: Type.OBJECT,
                properties: {
                    systemType: { type: Type.STRING, description: "e.g., Supply, Return, Exhaust, Outdoor" },
                    sizeRange: { type: Type.STRING, description: "Applicable duct sizes, e.g., 'All' or '> 24\"'" },
                    thickness: { type: Type.STRING, description: "Insulation thickness, e.g., '1.5 inches'" },
                    material: { type: Type.STRING, description: "Insulation material, e.g., 'Fiberglass'" },
                    facing: { type: Type.STRING, description: "Facing material, e.g., 'FSK'" },
                    location: { type: Type.STRING, description: "e.g., 'Interior', 'Unconditioned space', 'Exterior'" },
                    specialReq: { type: Type.STRING, description: "Any special requirements for this system." },
                },
                required: ["systemType", "thickness", "material"],
            },
        },
        pipingSystems: {
            type: Type.ARRAY,
            description: "Detailed insulation requirements for each type of piping system.",
            items: {
                type: Type.OBJECT,
                properties: {
                    systemType: { type: Type.STRING, description: "e.g., CHW Supply, HW Return, Condensate" },
                    sizeRange: { type: Type.STRING, description: "Applicable pipe sizes, e.g., 'Up to 2\"' or 'All'" },
                    thickness: { type: Type.STRING, description: "Insulation thickness, e.g., '1 inch'" },
                    material: { type: Type.STRING, description: "Insulation material, e.g., 'Elastomeric' or 'Fiberglass'" },
                    jacket: { type: Type.STRING, description: "Jacket type, e.g., 'ASJ' or 'Aluminum'" },
                    location: { type: Type.STRING, description: "e.g., 'Interior', 'Exterior'" },
                    specialReq: { type: Type.STRING, description: "Any special requirements for this system." },
                },
                required: ["systemType", "thickness", "material"],
            },
        },
        specialRequirements: {
            type: Type.ARRAY,
            description: "A list of general special requirements not tied to a specific system.",
            items: { type: Type.STRING },
        },
        ambiguities: {
            type: Type.ARRAY,
            description: "A list of ambiguities, conflicts, or missing information found in the document.",
            items: { type: Type.STRING },
        },
        summary: {
            type: Type.OBJECT,
            description: "A final summary of findings.",
            properties: {
                confirmed: { type: Type.ARRAY, items: { type: Type.STRING }, description: "List of clearly specified requirements." },
                clarificationNeeded: { type: Type.ARRAY, items: { type: Type.STRING }, description: "List of items that need clarification." },
                assumptions: { type: Type.ARRAY, items: { type: Type.STRING }, description: "List of assumptions made." },
            },
            required: ["confirmed", "clarificationNeeded", "assumptions"],
        }
    },
    required: ["ductworkSystems", "pipingSystems", "specialRequirements", "ambiguities", "summary"],
};

const drawingAnalysisSchema = {
    type: Type.OBJECT,
    properties: {
        ductwork: {
            type: Type.ARRAY,
            items: {
                type: Type.OBJECT,
                required: ["size", "length", "fittings"],
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
                required: ["size", "length", "fittings"],
                properties: {
                    size: { type: Type.STRING, description: "e.g., '2\" CHW'" },
                    length: { type: Type.NUMBER, description: "Linear feet" },
                    fittings: { type: Type.NUMBER, description: "Count of elbows, valves, etc." },
                }
            }
        },
        scale: { type: Type.STRING, description: "Drawing scale, e.g., '1/4\" = 1'-0\"'" },
        notes: { type: Type.STRING, description: "Any important notes, ambiguities, or areas of concern." }
    },
    required: ["ductwork", "piping", "scale", "notes"],
};

export const analyzeSpecification = async (file: File): Promise<GeminiSpecAnalysis> => {
    const systemInstruction = `You are an AI-powered HVAC mechanical insulation estimation service for Guaranteed Insulation. Your role is to act as a senior estimator reviewing a new project specification. You must analyze the attached document and provide a full JSON output that adheres to the provided schema.

SPECIFICATION EXTRACTION PROTOCOL:

When analyzing the uploaded project specification PDF, follow this exact sequence:

STEP 1: LOCATE INSULATION SECTION
- Search for: "Division 23", "23 07 19", "HVAC Insulation", "Mechanical Insulation"
- If not found, search for: "insulation" in Division 15, 22, or 23

STEP 2: EXTRACT BY SYSTEM TYPE
- Populate the 'ductworkSystems' and 'pipingSystems' arrays. Create one object for each distinct system type found in the specification.
- For each system, fill in all fields (Size Range, Thickness, Material, etc.) as specified in the document. If information is not available for a field, leave it as an empty string.

STEP 3: EXTRACT SPECIAL REQUIREMENTS
- Identify and list general requirements that apply across multiple systems.
- Examples: Vapor barrier details, mastic application rules, outdoor jacketing specifics, fire rating needs, acoustic performance, access panel insulation, equipment insulation.
- Populate the 'specialRequirements' array with these findings.

STEP 4: IDENTIFY AMBIGUITIES
- Carefully read for any conflicting or missing information.
- Flag issues like:
    - "Insulation thickness not specified for [system]"
    - "Material type unclear for [system]"
    - "Indoor vs outdoor requirements are not distinguished"
    - "Conflicting requirements found in different sections"
- Populate the 'ambiguities' array with these flagged issues.

STEP 5: CREATE EXTRACTION SUMMARY
- Populate the 'summary' object with three distinct lists:
- 'confirmed': A list of all requirements that are clearly specified.
- 'clarificationNeeded': A list of all ambiguities and conflicts that require clarification from the client.
- 'assumptions': A list of any assumptions you had to make (e.g., "Assumed standard FSK facing where not specified").`;
    
  const filePart = await fileToGenerativePart(file);
  
  const response: GenerateContentResponse = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: { parts: [filePart] },
    config: {
      systemInstruction: systemInstruction,
      responseMimeType: 'application/json',
      responseSchema: specAnalysisSchema,
    },
  });

  const jsonText = response.text.trim();
  return JSON.parse(jsonText);
};

export const analyzeDrawings = async (file: File): Promise<GeminiDrawingAnalysis> => {
    const systemInstruction = `You are an AI-powered HVAC mechanical insulation estimation service. Your goal is to perform a takeoff for ductwork and piping from the provided drawings. Respond ONLY with the JSON object as defined by the schema.

Analyze the construction drawings (PDF).
Identify sizes (e.g., "18x12" or '2" CHW'), measure linear feet for each size, and count fittings (elbows, tees).
Note the drawing scale. Summarize your findings in the JSON format.
Be as accurate as possible with quantities. If a scale is not present, assume 1/4" = 1'-0" for mechanical plans.`;

    const filePart = await fileToGenerativePart(file);

    const response: GenerateContentResponse = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: { parts: [filePart] },
        config: {
            systemInstruction: systemInstruction,
            responseMimeType: 'application/json',
            responseSchema: drawingAnalysisSchema,
        },
    });

    const jsonText = response.text.trim();
    return JSON.parse(jsonText);
};
