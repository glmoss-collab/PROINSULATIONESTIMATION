/**
 * Figma Plugin Sandbox Code (main thread).
 *
 * Runs inside the Figma sandbox with access to the Figma API and scene graph.
 * Communicates with the UI iframe via figma.ui.postMessage / onmessage.
 *
 * Responsibilities:
 *  - Extract measurements from the current page or selection
 *  - Highlight nodes for user review
 *  - Apply insulation annotation layers to selected elements
 *  - Export annotated drawings as SVG
 */

import type {
  UIToPluginMessage,
  PluginToUIMessage,
  InsulationLayerSpec,
  FigmaMeasurement,
  DrawingScale,
} from './types';
import {
  extractMeasurements,
  flattenNodes,
} from './utils/measurementExtractor';

// ---------------------------------------------------------------------------
// Plugin Initialization
// ---------------------------------------------------------------------------

figma.showUI(__html__, {
  width: 480,
  height: 640,
  themeColors: true,
  title: 'Pro Insulation Estimator',
});

// Send initial page info to the UI
sendPageInfo();

// ---------------------------------------------------------------------------
// Message Handler
// ---------------------------------------------------------------------------

figma.ui.onmessage = (msg: UIToPluginMessage) => {
  switch (msg.type) {
    case 'extract-measurements':
      handleExtractMeasurements(msg.scale);
      break;
    case 'extract-selected':
      handleExtractSelected(msg.scale);
      break;
    case 'highlight-node':
      handleHighlightNode(msg.nodeId);
      break;
    case 'apply-insulation-layer':
      handleApplyInsulationLayer(msg.nodeIds, msg.spec);
      break;
    case 'export-annotations':
      handleExportAnnotations();
      break;
    case 'get-page-info':
      sendPageInfo();
      break;
    case 'resize':
      figma.ui.resize(msg.width, msg.height);
      break;
  }
};

// Listen for selection changes and notify the UI
figma.on('selectionchange', () => {
  sendPageInfo();
});

// ---------------------------------------------------------------------------
// Measurement Extraction
// ---------------------------------------------------------------------------

/**
 * Extract measurements from all nodes on the current page.
 */
function handleExtractMeasurements(scale: DrawingScale): void {
  try {
    const page = figma.currentPage;
    const allNodes: SceneNode[] = [];

    for (const child of page.children) {
      allNodes.push(...flattenNodes(child));
    }

    const measurements = extractMeasurements(allNodes, scale);

    postToUI({
      type: 'measurements-extracted',
      measurements,
      pageName: page.name,
    });
  } catch (err) {
    postToUI({
      type: 'error',
      message: `Extraction failed: ${err instanceof Error ? err.message : String(err)}`,
    });
  }
}

/**
 * Extract measurements only from the user's current selection.
 */
function handleExtractSelected(scale: DrawingScale): void {
  try {
    const selection = figma.currentPage.selection;
    if (selection.length === 0) {
      postToUI({ type: 'error', message: 'No elements selected. Select HVAC elements first.' });
      return;
    }

    const allNodes: SceneNode[] = [];
    for (const node of selection) {
      allNodes.push(...flattenNodes(node));
    }

    const measurements = extractMeasurements(allNodes, scale);

    postToUI({
      type: 'measurements-extracted',
      measurements,
      pageName: figma.currentPage.name,
    });
  } catch (err) {
    postToUI({
      type: 'error',
      message: `Extraction failed: ${err instanceof Error ? err.message : String(err)}`,
    });
  }
}

// ---------------------------------------------------------------------------
// Node Highlighting
// ---------------------------------------------------------------------------

/**
 * Select and zoom to a specific node so the user can review it.
 */
function handleHighlightNode(nodeId: string): void {
  try {
    const node = figma.getNodeById(nodeId);
    if (!node || node.type === 'DOCUMENT' || node.type === 'PAGE') {
      postToUI({ type: 'error', message: `Node ${nodeId} not found on this page.` });
      return;
    }

    const sceneNode = node as SceneNode;
    figma.currentPage.selection = [sceneNode];
    figma.viewport.scrollAndZoomIntoView([sceneNode]);

    postToUI({ type: 'node-highlighted', nodeId });
  } catch (err) {
    postToUI({
      type: 'error',
      message: `Could not highlight node: ${err instanceof Error ? err.message : String(err)}`,
    });
  }
}

// ---------------------------------------------------------------------------
// Insulation Annotation Layer
// ---------------------------------------------------------------------------

/**
 * Apply a visual insulation layer (colored outline) to selected nodes
 * to annotate them in the Figma drawing.
 */
function handleApplyInsulationLayer(
  nodeIds: string[],
  spec: InsulationLayerSpec
): void {
  try {
    let applied = 0;

    for (const nodeId of nodeIds) {
      const node = figma.getNodeById(nodeId);
      if (!node || !('strokes' in node)) continue;

      const geometryNode = node as GeometryMixin & SceneNode;

      // Add a colored stroke representing the insulation layer
      geometryNode.strokes = [
        {
          type: 'SOLID',
          color: spec.color,
          opacity: spec.opacity,
        },
      ];
      geometryNode.strokeWeight = Math.max(2, spec.thickness * 4);
      geometryNode.dashPattern = [8, 4];

      applied++;
    }

    postToUI({ type: 'insulation-layer-applied', count: applied });
  } catch (err) {
    postToUI({
      type: 'error',
      message: `Failed to apply insulation layer: ${err instanceof Error ? err.message : String(err)}`,
    });
  }
}

// ---------------------------------------------------------------------------
// Export Annotations
// ---------------------------------------------------------------------------

/**
 * Export the current page as SVG so annotated drawings can be shared.
 */
async function handleExportAnnotations(): Promise<void> {
  try {
    const page = figma.currentPage;
    if (page.children.length === 0) {
      postToUI({ type: 'error', message: 'Current page is empty.' });
      return;
    }

    // Export the entire frame / page content
    const nodes = page.children;
    const exportNode = nodes.length === 1 ? nodes[0] : figma.flatten(nodes as readonly SceneNode[]);

    const svgBytes = await exportNode.exportAsync({ format: 'SVG' });
    const svgString = String.fromCharCode(...svgBytes);

    postToUI({ type: 'annotations-exported', svg: svgString });
  } catch (err) {
    postToUI({
      type: 'error',
      message: `Export failed: ${err instanceof Error ? err.message : String(err)}`,
    });
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Send current page info to the UI. */
function sendPageInfo(): void {
  const page = figma.currentPage;
  let nodeCount = 0;
  for (const child of page.children) {
    nodeCount += countNodes(child);
  }

  postToUI({
    type: 'page-info',
    pageName: page.name,
    nodeCount,
    hasSelection: page.selection.length > 0,
  });
}

/** Recursively count nodes under a root. */
function countNodes(node: SceneNode): number {
  let count = 1;
  if ('children' in node) {
    for (const child of node.children) {
      count += countNodes(child);
    }
  }
  return count;
}

/** Type-safe wrapper for posting messages to the UI. */
function postToUI(msg: PluginToUIMessage): void {
  figma.ui.postMessage(msg);
}
