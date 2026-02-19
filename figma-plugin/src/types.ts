/**
 * Type definitions for the Pro Insulation Estimator Figma Plugin.
 *
 * Follows the project convention of centralized type definitions
 * with full type safety. Mirrors types.ts from the main React app
 * where applicable, adding Figma-specific types.
 */

// ---------------------------------------------------------------------------
// Figma Node Measurement Types
// ---------------------------------------------------------------------------

/** A single measurement extracted from a Figma drawing element. */
export interface FigmaMeasurement {
  nodeId: string;
  nodeName: string;
  systemType: 'duct' | 'pipe' | 'equipment' | 'unknown';
  size: string;
  lengthFt: number;
  widthIn: number | null;
  heightIn: number | null;
  diameterIn: number | null;
  fittings: Record<string, number>;
  location: string;
  layerPath: string;
}

/** Scale configuration for converting Figma units to real-world measurements. */
export interface DrawingScale {
  figmaUnitsPerFoot: number;
  label: string;
}

/** Predefined scale presets for common architectural drawing scales. */
export const SCALE_PRESETS: Record<string, DrawingScale> = {
  'quarter_inch': { figmaUnitsPerFoot: 24, label: '1/4" = 1\'-0"' },
  'eighth_inch': { figmaUnitsPerFoot: 12, label: '1/8" = 1\'-0"' },
  'three_sixteenths': { figmaUnitsPerFoot: 18, label: '3/16" = 1\'-0"' },
  'half_inch': { figmaUnitsPerFoot: 48, label: '1/2" = 1\'-0"' },
  'custom': { figmaUnitsPerFoot: 1, label: 'Custom' },
};

// ---------------------------------------------------------------------------
// Estimation Request / Response Types
// ---------------------------------------------------------------------------

/** Request payload sent to the estimation API backend. */
export interface EstimationRequest {
  projectInfo: ProjectInfo;
  measurements: FigmaMeasurement[];
  scale: DrawingScale;
  preferences: EstimationPreferences;
}

/** User preferences for estimation behavior. */
export interface EstimationPreferences {
  materialMarkup: number;
  laborMarkup: number;
  overheadProfit: number;
  contingency: number;
  laborRate: number;
  includeAlternatives: boolean;
}

/** Project metadata. Mirrors the main app's ProjectInfo. */
export interface ProjectInfo {
  projectName: string;
  location: string;
  customer: string;
  date: string;
  quoteNumber: string;
}

/** A single line item in the generated quote. */
export interface QuoteLineItem {
  description: string;
  details: string;
  quantity: number;
  unit: string;
  unitPrice: number;
  total: number;
  type: 'material' | 'labor' | 'summary';
  category: string;
}

/** Complete estimation result from the backend. */
export interface EstimationResult {
  success: boolean;
  quoteNumber: string;
  projectName: string;
  lineItems: QuoteLineItem[];
  materialTotal: number;
  laborTotal: number;
  subtotal: number;
  contingencyAmount: number;
  grandTotal: number;
  laborHours: number;
  warnings: string[];
  alternatives: AlternativeOption[];
}

/** Cost-saving alternative suggestion. */
export interface AlternativeOption {
  description: string;
  currentCost: number;
  alternativeCost: number;
  savings: number;
  tradeoff: string;
}

// ---------------------------------------------------------------------------
// Plugin Message Types (code.ts <-> ui.tsx communication)
// ---------------------------------------------------------------------------

/** Messages sent from the UI iframe to the Figma sandbox. */
export type UIToPluginMessage =
  | { type: 'extract-measurements'; scale: DrawingScale }
  | { type: 'extract-selected'; scale: DrawingScale }
  | { type: 'highlight-node'; nodeId: string }
  | { type: 'apply-insulation-layer'; nodeIds: string[]; spec: InsulationLayerSpec }
  | { type: 'export-annotations' }
  | { type: 'get-page-info' }
  | { type: 'resize'; width: number; height: number };

/** Messages sent from the Figma sandbox to the UI iframe. */
export type PluginToUIMessage =
  | { type: 'measurements-extracted'; measurements: FigmaMeasurement[]; pageName: string }
  | { type: 'page-info'; pageName: string; nodeCount: number; hasSelection: boolean }
  | { type: 'node-highlighted'; nodeId: string }
  | { type: 'insulation-layer-applied'; count: number }
  | { type: 'annotations-exported'; svg: string }
  | { type: 'error'; message: string };

/** Spec for visual insulation layer annotation in Figma. */
export interface InsulationLayerSpec {
  thickness: number;
  material: string;
  color: RGB;
  opacity: number;
}

/** RGB color value for Figma node styling. */
export interface RGB {
  r: number;
  g: number;
  b: number;
}

// ---------------------------------------------------------------------------
// Plugin UI State
// ---------------------------------------------------------------------------

/** Active tab in the plugin UI. */
export type PluginTab = 'extract' | 'estimate' | 'quote' | 'settings';

/** Complete plugin UI state. */
export interface PluginState {
  activeTab: PluginTab;
  projectInfo: ProjectInfo;
  measurements: FigmaMeasurement[];
  scale: DrawingScale;
  preferences: EstimationPreferences;
  estimationResult: EstimationResult | null;
  isLoading: boolean;
  error: string | null;
  pageName: string;
}

// ---------------------------------------------------------------------------
// Figma Node Classification
// ---------------------------------------------------------------------------

/** Classification result for a Figma node as an HVAC element. */
export interface NodeClassification {
  systemType: 'duct' | 'pipe' | 'equipment' | 'unknown';
  confidence: number;
  sizeInferred: string;
  reason: string;
}

/** Keywords used to classify Figma layers by name. */
export const SYSTEM_KEYWORDS: Record<string, string[]> = {
  duct: [
    'duct', 'supply', 'return', 'exhaust', 'sa', 'ra', 'ea', 'oa',
    'outside air', 'fresh air', 'rectangular', 'round duct',
  ],
  pipe: [
    'pipe', 'chw', 'chilled', 'hw', 'hot water', 'steam', 'condensate',
    'refrigerant', 'cwp', 'hwp', 'dhw', 'domestic',
  ],
  equipment: [
    'ahu', 'air handler', 'fcu', 'fan coil', 'vav', 'chiller',
    'boiler', 'pump', 'tank', 'vessel', 'heat exchanger',
  ],
};
