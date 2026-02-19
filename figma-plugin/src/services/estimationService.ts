/**
 * Estimation Service for the Figma Plugin.
 *
 * Connects to the Pro Insulation Estimation backend API to calculate
 * material quantities, labor, and generate professional quotes from
 * measurements extracted from Figma drawings.
 *
 * Supports two modes:
 *  1. API mode — sends measurements to a running backend instance
 *  2. Local mode — uses the built-in TypeScript estimation engine
 *     (same logic as the React app's estimator.ts)
 */

import type {
  FigmaMeasurement,
  EstimationRequest,
  EstimationResult,
  EstimationPreferences,
  ProjectInfo,
  QuoteLineItem,
  AlternativeOption,
  DrawingScale,
} from '../types';

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const DEFAULT_API_URL = 'http://localhost:8501/api/estimate';

// Pricing constants mirrored from constants.ts in the main app
const DUCT_PRICING: Record<string, number> = {
  '1.5_fiberglass_fsk': 2.52,
};

const PIPE_PRICING: Record<string, number> = {
  '1.0_elastomeric': 7.18,
  '1.5_fiberglass': 3.74,
};

const LABOR_RATES: Record<string, number> = {
  duct_rectangular_medium: 22.5,
  pipe_medium: 17.5,
  equipment: 10.0,
};

// ---------------------------------------------------------------------------
// API Mode
// ---------------------------------------------------------------------------

/**
 * Send measurements to the backend estimation API and return the result.
 *
 * Falls back to local estimation if the API is unreachable.
 */
export async function estimateViaAPI(
  apiUrl: string,
  request: EstimationRequest
): Promise<EstimationResult> {
  try {
    const response = await fetch(apiUrl || DEFAULT_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`API returned ${response.status}: ${response.statusText}`);
    }

    const data = (await response.json()) as EstimationResult;
    return data;
  } catch (err) {
    // Fall back to local estimation
    console.warn('API unreachable, using local estimation:', err);
    return estimateLocally(request);
  }
}

// ---------------------------------------------------------------------------
// Local Estimation Engine
// ---------------------------------------------------------------------------

/**
 * Perform estimation locally using the built-in pricing engine.
 *
 * This mirrors the logic in estimator.ts and the Python PricingEngine,
 * allowing the Figma plugin to work offline.
 */
export function estimateLocally(request: EstimationRequest): EstimationResult {
  const { projectInfo, measurements, preferences } = request;
  const lineItems: QuoteLineItem[] = [];
  const warnings: string[] = [];
  let materialTotal = 0;
  let laborHours = 0;

  // --- Material Calculation ---
  for (const m of measurements) {
    if (m.systemType === 'unknown') {
      warnings.push(`Skipped "${m.nodeName}" — could not classify system type.`);
      continue;
    }

    // Determine unit price
    let unitPrice = 0;
    let unitLabel = 'LF';
    let description = '';

    if (m.systemType === 'duct') {
      unitPrice = DUCT_PRICING['1.5_fiberglass_fsk'] || 2.52;
      description = `Duct Insulation — ${m.size}`;
    } else if (m.systemType === 'pipe') {
      unitPrice = PIPE_PRICING['1.0_elastomeric'] || 7.18;
      description = `Pipe Insulation — ${m.size}`;
    } else {
      unitPrice = 5.0;
      unitLabel = 'SF';
      description = `Equipment Insulation — ${m.nodeName}`;
    }

    // Account for fittings (add equivalent linear feet)
    const fittingLF = Object.entries(m.fittings).reduce((acc, [type, count]) => {
      const equiv = type === 'elbow' ? 1.5 : type === 'tee' ? 2.0 : 1.0;
      return acc + equiv * count;
    }, 0);

    const totalLength = m.lengthFt + fittingLF;
    const wasteFactor = 1.1; // 10% waste
    const quantity = Math.ceil(totalLength * wasteFactor * 100) / 100;
    const total = Math.round(quantity * unitPrice * 100) / 100;

    lineItems.push({
      description,
      details: `${m.lengthFt} LF + ${fittingLF.toFixed(1)} LF fittings, 10% waste`,
      quantity,
      unit: unitLabel,
      unitPrice,
      total,
      type: 'material',
      category: m.systemType,
    });

    materialTotal += total;

    // Labor hours
    const rate =
      m.systemType === 'duct'
        ? LABOR_RATES['duct_rectangular_medium']
        : m.systemType === 'pipe'
          ? LABOR_RATES['pipe_medium']
          : LABOR_RATES['equipment'];
    laborHours += totalLength / rate;
  }

  // Apply markups
  materialTotal = Math.round(materialTotal * (1 + preferences.materialMarkup / 100) * 100) / 100;
  laborHours = Math.round(laborHours * 1.2 * 100) / 100; // 20% overhead
  const laborCost = Math.round(laborHours * preferences.laborRate * 100) / 100;
  const laborTotal = Math.round(laborCost * (1 + preferences.laborMarkup / 100) * 100) / 100;

  // Add labor line item
  lineItems.push({
    description: 'Installation Labor',
    details: `${laborHours} hours @ $${preferences.laborRate}/hr`,
    quantity: laborHours,
    unit: 'HR',
    unitPrice: preferences.laborRate,
    total: laborTotal,
    type: 'labor',
    category: 'labor',
  });

  const subtotal = materialTotal + laborTotal;
  const ohp = Math.round(subtotal * (preferences.overheadProfit / 100) * 100) / 100;
  const contingencyAmount = Math.round((subtotal + ohp) * (preferences.contingency / 100) * 100) / 100;
  const grandTotal = Math.round((subtotal + ohp + contingencyAmount) * 100) / 100;

  // Quote number
  const now = new Date();
  const quoteNumber = `FQ${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}-${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;

  // Summary line items
  lineItems.push(
    {
      description: 'Overhead & Profit',
      details: `${preferences.overheadProfit}%`,
      quantity: 1,
      unit: 'LS',
      unitPrice: ohp,
      total: ohp,
      type: 'summary',
      category: 'overhead',
    },
    {
      description: 'Contingency',
      details: `${preferences.contingency}%`,
      quantity: 1,
      unit: 'LS',
      unitPrice: contingencyAmount,
      total: contingencyAmount,
      type: 'summary',
      category: 'contingency',
    }
  );

  // Generate alternatives
  const alternatives = generateAlternatives(measurements, materialTotal, preferences);

  return {
    success: true,
    quoteNumber,
    projectName: projectInfo.projectName,
    lineItems,
    materialTotal,
    laborTotal,
    subtotal,
    contingencyAmount,
    grandTotal,
    laborHours,
    warnings,
    alternatives,
  };
}

// ---------------------------------------------------------------------------
// Alternatives Generator
// ---------------------------------------------------------------------------

function generateAlternatives(
  measurements: FigmaMeasurement[],
  materialTotal: number,
  preferences: EstimationPreferences
): AlternativeOption[] {
  const alternatives: AlternativeOption[] = [];

  const hasDuct = measurements.some((m) => m.systemType === 'duct');
  const hasPipe = measurements.some((m) => m.systemType === 'pipe');

  if (hasDuct) {
    const fiberglassCost = materialTotal * 0.6; // Approx duct portion
    const elastomericCost = fiberglassCost * 1.4;
    alternatives.push({
      description: 'Upgrade duct insulation to elastomeric (closed-cell)',
      currentCost: fiberglassCost,
      alternativeCost: elastomericCost,
      savings: fiberglassCost - elastomericCost,
      tradeoff: 'Higher upfront cost but better moisture resistance and longevity',
    });
  }

  if (hasPipe) {
    const currentPipeCost = materialTotal * 0.4;
    const altPipeCost = currentPipeCost * 0.75;
    alternatives.push({
      description: 'Use fiberglass pipe insulation instead of elastomeric',
      currentCost: currentPipeCost,
      alternativeCost: altPipeCost,
      savings: currentPipeCost - altPipeCost,
      tradeoff: 'Lower cost but requires vapor barrier and more careful installation',
    });
  }

  return alternatives;
}

// ---------------------------------------------------------------------------
// Utility: Build Request
// ---------------------------------------------------------------------------

/**
 * Build an EstimationRequest from plugin state.
 */
export function buildEstimationRequest(
  projectInfo: ProjectInfo,
  measurements: FigmaMeasurement[],
  scale: DrawingScale,
  preferences: EstimationPreferences
): EstimationRequest {
  return {
    projectInfo,
    measurements,
    scale,
    preferences,
  };
}
