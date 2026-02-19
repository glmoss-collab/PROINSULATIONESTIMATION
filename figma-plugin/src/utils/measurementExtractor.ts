/**
 * Measurement extraction utilities for Figma nodes.
 *
 * Traverses the Figma scene graph, classifies HVAC elements by layer name
 * and geometry, and converts Figma coordinates to real-world measurements
 * using the configured drawing scale.
 */

import type {
  FigmaMeasurement,
  DrawingScale,
  NodeClassification,
} from '../types';
import { SYSTEM_KEYWORDS } from '../types';

// ---------------------------------------------------------------------------
// Node Classification
// ---------------------------------------------------------------------------

/**
 * Classify a Figma node as an HVAC system element based on its name.
 *
 * Searches the node name (and ancestor path) for keywords that map to
 * duct, pipe, or equipment system types.
 */
export function classifyNode(
  nodeName: string,
  ancestorNames: string[] = []
): NodeClassification {
  const searchText = [nodeName, ...ancestorNames].join(' ').toLowerCase();

  for (const [systemType, keywords] of Object.entries(SYSTEM_KEYWORDS)) {
    for (const keyword of keywords) {
      if (searchText.includes(keyword)) {
        return {
          systemType: systemType as 'duct' | 'pipe' | 'equipment',
          confidence: nodeName.toLowerCase().includes(keyword) ? 0.9 : 0.6,
          sizeInferred: inferSizeFromName(nodeName),
          reason: `Matched keyword "${keyword}" in ${
            nodeName.toLowerCase().includes(keyword) ? 'node name' : 'ancestor'
          }`,
        };
      }
    }
  }

  return {
    systemType: 'unknown',
    confidence: 0.1,
    sizeInferred: '',
    reason: 'No HVAC keywords matched',
  };
}

/**
 * Attempt to infer a size label from the node name.
 *
 * Matches patterns like "24x20", "24\"x20\"", "2\" pipe", "12 inch", etc.
 */
export function inferSizeFromName(name: string): string {
  // Rectangular duct: "24x20", "24\"x20\""
  const rectMatch = name.match(/(\d+)\s*[""x×]\s*(\d+)/i);
  if (rectMatch) {
    return `${rectMatch[1]}x${rectMatch[2]}`;
  }

  // Round duct or pipe diameter: "12\" round", "2\" pipe", "12 inch"
  const diamMatch = name.match(/(\d+\.?\d*)\s*[""]\s*(round|pipe|dia)/i);
  if (diamMatch) {
    return `${diamMatch[1]}"`;
  }

  // Bare number with inch mark: "24\""
  const bareMatch = name.match(/(\d+\.?\d*)\s*[""](?!\s*[x×])/);
  if (bareMatch) {
    return `${bareMatch[1]}"`;
  }

  return '';
}

// ---------------------------------------------------------------------------
// Geometry Helpers
// ---------------------------------------------------------------------------

/** Calculate the length of a vector line node in Figma units. */
function vectorLength(node: SceneNode): number {
  if ('width' in node && 'height' in node) {
    return Math.sqrt(node.width ** 2 + node.height ** 2);
  }
  return 0;
}

/** Get the longer dimension of a rectangular node in Figma units. */
function longerDimension(node: SceneNode): number {
  if ('width' in node && 'height' in node) {
    return Math.max(node.width, node.height);
  }
  return 0;
}

/** Get the shorter dimension of a rectangular node in Figma units. */
function shorterDimension(node: SceneNode): number {
  if ('width' in node && 'height' in node) {
    return Math.min(node.width, node.height);
  }
  return 0;
}

/** Convert Figma units to feet using the drawing scale. */
export function figmaUnitsToFeet(
  units: number,
  scale: DrawingScale
): number {
  if (scale.figmaUnitsPerFoot <= 0) return 0;
  return Math.round((units / scale.figmaUnitsPerFoot) * 100) / 100;
}

/** Convert Figma units to inches using the drawing scale. */
export function figmaUnitsToInches(
  units: number,
  scale: DrawingScale
): number {
  return figmaUnitsToFeet(units, scale) * 12;
}

// ---------------------------------------------------------------------------
// Ancestor Path
// ---------------------------------------------------------------------------

/** Build the layer path string from a node up to the page root. */
function getLayerPath(node: SceneNode): string {
  const parts: string[] = [];
  let current: BaseNode | null = node;
  while (current && current.type !== 'PAGE') {
    parts.unshift(current.name);
    current = current.parent;
  }
  return parts.join(' / ');
}

/** Collect ancestor names for keyword classification. */
function getAncestorNames(node: SceneNode): string[] {
  const names: string[] = [];
  let current: BaseNode | null = node.parent;
  while (current && current.type !== 'PAGE') {
    names.push(current.name);
    current = current.parent;
  }
  return names;
}

// ---------------------------------------------------------------------------
// Fitting Detection
// ---------------------------------------------------------------------------

/**
 * Detect fittings (elbows, tees) near a line-like node by checking
 * for sibling nodes with fitting keywords in their name.
 */
function detectFittings(node: SceneNode): Record<string, number> {
  const fittings: Record<string, number> = {};

  const parent = node.parent;
  if (!parent || !('children' in parent)) return fittings;

  const fittingKeywords: Record<string, string[]> = {
    elbow: ['elbow', '90', '45', 'bend', 'turn'],
    tee: ['tee', 'branch', 'takeoff'],
    reducer: ['reducer', 'transition', 'reducing'],
    valve: ['valve', 'damper', 'balancing'],
  };

  for (const sibling of parent.children) {
    if (sibling.id === node.id) continue;
    const sibName = sibling.name.toLowerCase();
    for (const [fittingType, keywords] of Object.entries(fittingKeywords)) {
      if (keywords.some((kw) => sibName.includes(kw))) {
        fittings[fittingType] = (fittings[fittingType] || 0) + 1;
      }
    }
  }

  return fittings;
}

// ---------------------------------------------------------------------------
// Node Filtering
// ---------------------------------------------------------------------------

/** Determine whether a node should be considered for measurement. */
function isMeasurableNode(node: SceneNode): boolean {
  // Skip hidden or zero-size nodes
  if ('visible' in node && !node.visible) return false;
  if ('width' in node && 'height' in node) {
    if (node.width === 0 && node.height === 0) return false;
  }

  const validTypes: string[] = [
    'LINE',
    'VECTOR',
    'RECTANGLE',
    'ELLIPSE',
    'POLYGON',
    'FRAME',
    'GROUP',
    'COMPONENT',
    'INSTANCE',
  ];
  return validTypes.includes(node.type);
}

// ---------------------------------------------------------------------------
// Main Extraction
// ---------------------------------------------------------------------------

/**
 * Extract HVAC measurements from a flat list of Figma scene nodes.
 *
 * Each qualifying node is classified, its geometry converted to
 * real-world units using the provided scale, and fitting counts
 * are inferred from sibling nodes.
 */
export function extractMeasurements(
  nodes: readonly SceneNode[],
  scale: DrawingScale
): FigmaMeasurement[] {
  const measurements: FigmaMeasurement[] = [];

  for (const node of nodes) {
    if (!isMeasurableNode(node)) continue;

    const ancestorNames = getAncestorNames(node);
    const classification = classifyNode(node.name, ancestorNames);

    // Only keep nodes that matched an HVAC keyword
    if (classification.systemType === 'unknown') continue;

    const lengthFigma = longerDimension(node);
    const widthFigma = shorterDimension(node);

    const lengthFt = figmaUnitsToFeet(lengthFigma, scale);
    // Skip negligible elements
    if (lengthFt < 0.5) continue;

    const widthIn = figmaUnitsToInches(widthFigma, scale);

    const measurement: FigmaMeasurement = {
      nodeId: node.id,
      nodeName: node.name,
      systemType: classification.systemType === 'equipment' ? 'equipment' : classification.systemType,
      size: classification.sizeInferred || (widthIn > 0 ? `${Math.round(widthIn)}"` : 'unknown'),
      lengthFt,
      widthIn: classification.systemType === 'duct' ? widthIn : null,
      heightIn: classification.systemType === 'duct' ? widthIn : null,
      diameterIn: classification.systemType === 'pipe' ? widthIn : null,
      fittings: detectFittings(node),
      location: '',
      layerPath: getLayerPath(node),
    };

    measurements.push(measurement);
  }

  return measurements;
}

/**
 * Recursively collect all scene nodes from a given root.
 *
 * This is called in the Figma sandbox (code.ts) where we have
 * access to the scene graph.
 */
export function flattenNodes(root: SceneNode): SceneNode[] {
  const result: SceneNode[] = [root];
  if ('children' in root) {
    for (const child of root.children) {
      result.push(...flattenNodes(child));
    }
  }
  return result;
}
