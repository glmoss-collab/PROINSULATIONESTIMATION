
import { GoogleGenAI, Type, GenerateContentResponse } from "@google/genai";
import type { GeminiSpecAnalysis, GeminiDrawingAnalysis, ProjectInfo, TakeoffItem } from '../types';
import { generateQuoteFromUI } from '../estimator';

// Enhanced pattern matching from process_my_pdfs.py
const INSULATION_KEYWORDS = [
    'insulation', 'thermal insulation', 'mechanical insulation',
    'duct insulation', 'pipe insulation', 'fiberglass', 'elastomeric',
    'FSK', 'ASJ', 'mastic', 'vapor barrier', 'jacketing'
];

const THICKNESS_PATTERNS = [
    /(\d+\.?\d*)\s*["\']?\s*thick/i,
    /thickness.*?(\d+\.?\d*)\s*["\']/i,
    /(\d+\.?\d*)\s*inch.*?insulation/i,
];

const MATERIALS = ['fiberglass', 'mineral wool', 'elastomeric', 'cellular glass', 'polyisocyanurate'];
const FACINGS = ['FSK', 'ASJ', 'All Service Jacket', 'Foil Scrim Kraft', 'white jacket', 'PVJ'];

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

// Helper to extract text content from PDF file
async function extractTextFromPDF(file: File): Promise<string> {
    // Convert PDF to text using the PDF file reader parts from the generateContent API
    const filePart = await fileToGenerativePart(file);
    const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: { parts: [filePart] },
        config: {
            systemInstruction: 'Extract all text content from this PDF file.',
            responseMimeType: 'text/plain',
        },
    });
    return response.text;
}

// Helper to validate and enhance spec analysis with pattern matching
function enhanceSpecAnalysis(text: string, analysis: GeminiSpecAnalysis): GeminiSpecAnalysis {
    // Look for additional thickness specs
    const thicknessMatches = new Set<string>();
    for (const pattern of THICKNESS_PATTERNS) {
        const matches = text.matchAll(pattern);
        for (const match of matches) {
            thicknessMatches.add(match[0]);
        }
    }

    // Look for additional materials
    const materialMatches = new Set<string>();
    for (const material of MATERIALS) {
        if (text.toLowerCase().includes(material)) {
            materialMatches.add(material);
        }
    }

    // Look for additional facings
    const facingMatches = new Set<string>();
    for (const facing of FACINGS) {
        if (text.toLowerCase().includes(facing.toLowerCase())) {
            facingMatches.add(facing);
        }
    }

    // Add any found specs not already in the analysis
    for (const system of analysis.ductworkSystems) {
        if (!system.thickness) {
            const foundThickness = Array.from(thicknessMatches)[0];
            if (foundThickness) {
                const match = foundThickness.match(/(\d+\.?\d*)/);
                if (match) system.thickness = match[1];
            }
        }
        if (!system.material && materialMatches.size > 0) {
            system.material = Array.from(materialMatches)[0];
        }
        if (!system.facing && facingMatches.size > 0) {
            system.facing = Array.from(facingMatches)[0];
        }
    }

    for (const system of analysis.pipingSystems) {
        if (!system.thickness) {
            const foundThickness = Array.from(thicknessMatches)[0];
            if (foundThickness) {
                const match = foundThickness.match(/(\d+\.?\d*)/);
                if (match) system.thickness = match[1];
            }
        }
        if (!system.material && materialMatches.size > 0) {
            system.material = Array.from(materialMatches)[0];
        }
        if (!system.jacket && facingMatches.size > 0) {
            system.jacket = Array.from(facingMatches)[0];
        }
    }

    return analysis;
}

// Helper to generate preview quote from spec analysis
function generatePreviewQuoteFromSpec(analysis: GeminiSpecAnalysis): { takeoff: TakeoffItem[], projectInfo: ProjectInfo } {
    // Create example takeoff items based on spec systems
    const takeoff: TakeoffItem[] = [];

    analysis.ductworkSystems.forEach((system, i) => {
        // Create a reasonable example size based on system type
        const size = system.systemType.toLowerCase().includes('return') ? '24x16' : '18x12';
        takeoff.push({
            id: `DUCT_PREVIEW_${i}`,
            size,
            length: 100, // Example length
            fittings: 4,  // Example fitting count
        });
    });

    analysis.pipingSystems.forEach((system, i) => {
        // Parse size range for a reasonable example
        const size = system.sizeRange ? system.sizeRange.match(/\d+/)?.[0] || '2' : '2';
        takeoff.push({
            id: `PIPE_PREVIEW_${i}`,
            size: `${size}" ${system.systemType}`,
            length: 75, // Example length
            fittings: 6, // Example fitting count
        });
    });

    // Create project info from analysis
    const projectInfo: ProjectInfo = {
        projectName: analysis.projectInfo?.projectName || 'New Project',
        location: analysis.projectInfo?.location || 'TBD',
        customer: analysis.projectInfo?.customer || 'TBD',
        date: analysis.projectInfo?.date || new Date().toISOString().split('T')[0],
        quoteNumber: `PREV-${Math.floor(Math.random() * 10000)}`,
    };

    return { takeoff, projectInfo };
}

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

    // Extract raw text and enhance the analysis
    const rawText = await extractTextFromPDF(file);
    const initialAnalysis = JSON.parse(response.text.trim()) as GeminiSpecAnalysis;
    const enhancedAnalysis = enhanceSpecAnalysis(rawText, initialAnalysis);

    return enhancedAnalysis;
};

// New function to get a preview quote right after spec analysis
export const generatePreviewFromSpec = async (specAnalysis: GeminiSpecAnalysis) => {
    const { takeoff, projectInfo } = generatePreviewQuoteFromSpec(specAnalysis);
    const quote = generateQuoteFromUI(
        projectInfo,
        takeoff.filter(t => t.id.startsWith('DUCT')),
        takeoff.filter(t => t.id.startsWith('PIPE')),
        specAnalysis
    );
    return { quote, takeoff, projectInfo };
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
