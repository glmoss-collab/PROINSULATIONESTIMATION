/**
 * Figma Plugin UI (runs in an iframe).
 *
 * Provides a tabbed interface for:
 *  - Extract: Pull HVAC measurements from the Figma drawing
 *  - Estimate: Configure pricing and run the estimation engine
 *  - Quote: View, review, and export the generated quote
 *  - Settings: Configure drawing scale, API URL, and preferences
 *
 * Communicates with code.ts via parent.postMessage / onmessage.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { createRoot } from 'react-dom/client';

import type {
  PluginTab,
  PluginToUIMessage,
  FigmaMeasurement,
  DrawingScale,
  EstimationPreferences,
  ProjectInfo,
  EstimationResult,
} from './types';
import { SCALE_PRESETS } from './types';
import {
  estimateLocally,
  estimateViaAPI,
  buildEstimationRequest,
} from './services/estimationService';

// ---------------------------------------------------------------------------
// Styles (inline to keep the plugin self-contained)
// ---------------------------------------------------------------------------

const styles = {
  container: {
    fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
    fontSize: 12,
    color: '#e0e0e0',
    background: '#2c2c2c',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column' as const,
  },
  tabs: {
    display: 'flex',
    borderBottom: '1px solid #444',
    background: '#333',
  },
  tab: (active: boolean) => ({
    flex: 1,
    padding: '10px 8px',
    textAlign: 'center' as const,
    cursor: 'pointer',
    fontWeight: active ? 600 : 400,
    color: active ? '#6ea8fe' : '#999',
    borderBottom: active ? '2px solid #6ea8fe' : '2px solid transparent',
    background: 'transparent',
    border: 'none',
    fontSize: 12,
  }),
  content: {
    flex: 1,
    padding: 16,
    overflowY: 'auto' as const,
  },
  card: {
    background: '#383838',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    border: '1px solid #444',
  },
  label: {
    display: 'block',
    fontSize: 11,
    color: '#aaa',
    marginBottom: 4,
  },
  input: {
    width: '100%',
    padding: '6px 8px',
    background: '#2c2c2c',
    border: '1px solid #555',
    borderRadius: 4,
    color: '#e0e0e0',
    fontSize: 12,
    marginBottom: 8,
    boxSizing: 'border-box' as const,
  },
  select: {
    width: '100%',
    padding: '6px 8px',
    background: '#2c2c2c',
    border: '1px solid #555',
    borderRadius: 4,
    color: '#e0e0e0',
    fontSize: 12,
    marginBottom: 8,
  },
  btnPrimary: {
    width: '100%',
    padding: '8px 12px',
    background: '#4a7fff',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: 12,
    marginBottom: 8,
  },
  btnSecondary: {
    width: '100%',
    padding: '8px 12px',
    background: '#555',
    color: '#e0e0e0',
    border: 'none',
    borderRadius: 6,
    cursor: 'pointer',
    fontSize: 12,
    marginBottom: 8,
  },
  badge: (color: string) => ({
    display: 'inline-block',
    padding: '2px 6px',
    borderRadius: 4,
    fontSize: 10,
    fontWeight: 600,
    background: color,
    color: '#fff',
    marginRight: 4,
  }),
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    fontSize: 11,
  },
  th: {
    textAlign: 'left' as const,
    padding: '6px 4px',
    borderBottom: '1px solid #555',
    color: '#aaa',
    fontWeight: 600,
  },
  td: {
    padding: '5px 4px',
    borderBottom: '1px solid #3a3a3a',
  },
  error: {
    background: '#5c2020',
    border: '1px solid #a03030',
    borderRadius: 6,
    padding: 10,
    marginBottom: 12,
    color: '#ffaaaa',
    fontSize: 11,
  },
  info: {
    background: '#1a3a5c',
    border: '1px solid #2a5a8c',
    borderRadius: 6,
    padding: 10,
    marginBottom: 12,
    color: '#aaccff',
    fontSize: 11,
  },
  stat: {
    textAlign: 'center' as const,
    padding: 8,
  },
  statValue: {
    fontSize: 20,
    fontWeight: 700,
    color: '#6ea8fe',
  },
  statLabel: {
    fontSize: 10,
    color: '#888',
    marginTop: 2,
  },
};

const SYSTEM_COLORS: Record<string, string> = {
  duct: '#4a90d9',
  pipe: '#50b86c',
  equipment: '#d4a843',
  unknown: '#888',
};

// ---------------------------------------------------------------------------
// Main App
// ---------------------------------------------------------------------------

function App() {
  const [activeTab, setActiveTab] = useState<PluginTab>('extract');
  const [pageName, setPageName] = useState('');
  const [nodeCount, setNodeCount] = useState(0);
  const [hasSelection, setHasSelection] = useState(false);

  const [measurements, setMeasurements] = useState<FigmaMeasurement[]>([]);
  const [estimationResult, setEstimationResult] = useState<EstimationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Drawing scale
  const [scalePreset, setScalePreset] = useState('quarter_inch');
  const [customScale, setCustomScale] = useState(24);
  const scale: DrawingScale =
    scalePreset === 'custom'
      ? { figmaUnitsPerFoot: customScale, label: `Custom (${customScale} units/ft)` }
      : SCALE_PRESETS[scalePreset];

  // Project info
  const [projectInfo, setProjectInfo] = useState<ProjectInfo>({
    projectName: '',
    location: '',
    customer: '',
    date: new Date().toISOString().slice(0, 10),
    quoteNumber: '',
  });

  // Preferences
  const [preferences, setPreferences] = useState<EstimationPreferences>({
    materialMarkup: 15,
    laborMarkup: 10,
    overheadProfit: 15,
    contingency: 10,
    laborRate: 85,
    includeAlternatives: true,
  });

  // API settings
  const [apiUrl, setApiUrl] = useState('');
  const [useApi, setUseApi] = useState(false);

  // -------------------------------------------------------------------------
  // Message listener
  // -------------------------------------------------------------------------

  useEffect(() => {
    const handler = (event: MessageEvent) => {
      const msg = event.data.pluginMessage as PluginToUIMessage;
      if (!msg) return;

      switch (msg.type) {
        case 'page-info':
          setPageName(msg.pageName);
          setNodeCount(msg.nodeCount);
          setHasSelection(msg.hasSelection);
          break;
        case 'measurements-extracted':
          setMeasurements(msg.measurements);
          setIsLoading(false);
          if (msg.measurements.length === 0) {
            setError('No HVAC elements found. Ensure layers are named with HVAC keywords (duct, pipe, supply, return, chw, etc.).');
          } else {
            setError(null);
            setActiveTab('estimate');
          }
          break;
        case 'error':
          setError(msg.message);
          setIsLoading(false);
          break;
        case 'node-highlighted':
          break;
        case 'insulation-layer-applied':
          setError(null);
          break;
        case 'annotations-exported':
          downloadSVG(msg.svg);
          break;
      }
    };

    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, []);

  // Request page info on mount
  useEffect(() => {
    postToPlugin({ type: 'get-page-info' });
  }, []);

  // -------------------------------------------------------------------------
  // Actions
  // -------------------------------------------------------------------------

  const extractAll = useCallback(() => {
    setIsLoading(true);
    setError(null);
    postToPlugin({ type: 'extract-measurements', scale });
  }, [scale]);

  const extractSelected = useCallback(() => {
    setIsLoading(true);
    setError(null);
    postToPlugin({ type: 'extract-selected', scale });
  }, [scale]);

  const runEstimation = useCallback(async () => {
    if (measurements.length === 0) {
      setError('No measurements to estimate. Extract measurements first.');
      return;
    }
    setIsLoading(true);
    setError(null);

    const request = buildEstimationRequest(projectInfo, measurements, scale, preferences);

    try {
      const result = useApi
        ? await estimateViaAPI(apiUrl, request)
        : estimateLocally(request);
      setEstimationResult(result);
      setActiveTab('quote');
    } catch (err) {
      setError(`Estimation failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsLoading(false);
    }
  }, [measurements, projectInfo, scale, preferences, useApi, apiUrl]);

  const highlightNode = useCallback((nodeId: string) => {
    postToPlugin({ type: 'highlight-node', nodeId });
  }, []);

  const applyAnnotations = useCallback(() => {
    const nodeIds = measurements.map((m) => m.nodeId);
    postToPlugin({
      type: 'apply-insulation-layer',
      nodeIds,
      spec: {
        thickness: 1.5,
        material: 'fiberglass',
        color: { r: 0.3, g: 0.6, b: 1.0 },
        opacity: 0.7,
      },
    });
  }, [measurements]);

  const exportSVG = useCallback(() => {
    postToPlugin({ type: 'export-annotations' });
  }, []);

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div style={styles.container}>
      {/* Tab Bar */}
      <div style={styles.tabs}>
        {(['extract', 'estimate', 'quote', 'settings'] as PluginTab[]).map((tab) => (
          <button key={tab} style={styles.tab(activeTab === tab)} onClick={() => setActiveTab(tab)}>
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Error Banner */}
      {error && (
        <div style={styles.error}>
          {error}
          <button
            onClick={() => setError(null)}
            style={{ float: 'right', background: 'none', border: 'none', color: '#ffaaaa', cursor: 'pointer' }}
          >
            X
          </button>
        </div>
      )}

      {/* Tab Content */}
      <div style={styles.content}>
        {activeTab === 'extract' && (
          <ExtractTab
            pageName={pageName}
            nodeCount={nodeCount}
            hasSelection={hasSelection}
            measurements={measurements}
            isLoading={isLoading}
            onExtractAll={extractAll}
            onExtractSelected={extractSelected}
            onHighlight={highlightNode}
            scalePreset={scalePreset}
            onScalePresetChange={setScalePreset}
            customScale={customScale}
            onCustomScaleChange={setCustomScale}
          />
        )}
        {activeTab === 'estimate' && (
          <EstimateTab
            measurements={measurements}
            projectInfo={projectInfo}
            onProjectInfoChange={setProjectInfo}
            preferences={preferences}
            onPreferencesChange={setPreferences}
            isLoading={isLoading}
            onRunEstimation={runEstimation}
            onApplyAnnotations={applyAnnotations}
          />
        )}
        {activeTab === 'quote' && (
          <QuoteTab
            result={estimationResult}
            onExportSVG={exportSVG}
          />
        )}
        {activeTab === 'settings' && (
          <SettingsTab
            apiUrl={apiUrl}
            onApiUrlChange={setApiUrl}
            useApi={useApi}
            onUseApiChange={setUseApi}
          />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Extract Tab
// ---------------------------------------------------------------------------

interface ExtractTabProps {
  pageName: string;
  nodeCount: number;
  hasSelection: boolean;
  measurements: FigmaMeasurement[];
  isLoading: boolean;
  onExtractAll: () => void;
  onExtractSelected: () => void;
  onHighlight: (nodeId: string) => void;
  scalePreset: string;
  onScalePresetChange: (v: string) => void;
  customScale: number;
  onCustomScaleChange: (v: number) => void;
}

function ExtractTab(props: ExtractTabProps) {
  return (
    <>
      {/* Page Info */}
      <div style={styles.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
          <div style={styles.stat}>
            <div style={styles.statValue}>{props.nodeCount}</div>
            <div style={styles.statLabel}>Total Nodes</div>
          </div>
          <div style={styles.stat}>
            <div style={styles.statValue}>{props.measurements.length}</div>
            <div style={styles.statLabel}>HVAC Elements</div>
          </div>
        </div>
        <div style={{ fontSize: 11, color: '#888', textAlign: 'center' }}>
          Page: <strong style={{ color: '#ccc' }}>{props.pageName || '—'}</strong>
        </div>
      </div>

      {/* Scale Configuration */}
      <div style={styles.card}>
        <label style={styles.label}>Drawing Scale</label>
        <select
          style={styles.select}
          value={props.scalePreset}
          onChange={(e) => props.onScalePresetChange(e.target.value)}
        >
          {Object.entries(SCALE_PRESETS).map(([key, val]) => (
            <option key={key} value={key}>{val.label}</option>
          ))}
        </select>
        {props.scalePreset === 'custom' && (
          <>
            <label style={styles.label}>Figma units per foot</label>
            <input
              type="number"
              style={styles.input}
              value={props.customScale}
              onChange={(e) => props.onCustomScaleChange(Number(e.target.value))}
              min={1}
            />
          </>
        )}
      </div>

      {/* Extract Buttons */}
      <button style={styles.btnPrimary} onClick={props.onExtractAll} disabled={props.isLoading}>
        {props.isLoading ? 'Extracting...' : 'Extract All from Page'}
      </button>
      <button
        style={styles.btnSecondary}
        onClick={props.onExtractSelected}
        disabled={props.isLoading || !props.hasSelection}
      >
        Extract from Selection
      </button>

      {/* Measurement Results */}
      {props.measurements.length > 0 && (
        <div style={styles.card}>
          <h3 style={{ margin: '0 0 8px', fontSize: 13 }}>Extracted Measurements</h3>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Type</th>
                <th style={styles.th}>Name</th>
                <th style={styles.th}>Size</th>
                <th style={styles.th}>Length</th>
                <th style={styles.th}></th>
              </tr>
            </thead>
            <tbody>
              {props.measurements.map((m) => (
                <tr key={m.nodeId}>
                  <td style={styles.td}>
                    <span style={styles.badge(SYSTEM_COLORS[m.systemType])}>{m.systemType}</span>
                  </td>
                  <td style={{ ...styles.td, maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {m.nodeName}
                  </td>
                  <td style={styles.td}>{m.size}</td>
                  <td style={styles.td}>{m.lengthFt} ft</td>
                  <td style={styles.td}>
                    <button
                      onClick={() => props.onHighlight(m.nodeId)}
                      style={{ background: 'none', border: 'none', color: '#6ea8fe', cursor: 'pointer', fontSize: 11 }}
                    >
                      Locate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Estimate Tab
// ---------------------------------------------------------------------------

interface EstimateTabProps {
  measurements: FigmaMeasurement[];
  projectInfo: ProjectInfo;
  onProjectInfoChange: (p: ProjectInfo) => void;
  preferences: EstimationPreferences;
  onPreferencesChange: (p: EstimationPreferences) => void;
  isLoading: boolean;
  onRunEstimation: () => void;
  onApplyAnnotations: () => void;
}

function EstimateTab(props: EstimateTabProps) {
  const { projectInfo, onProjectInfoChange, preferences, onPreferencesChange } = props;

  const updateProject = (field: keyof ProjectInfo, value: string) => {
    onProjectInfoChange({ ...projectInfo, [field]: value });
  };
  const updatePref = (field: keyof EstimationPreferences, value: number | boolean) => {
    onPreferencesChange({ ...preferences, [field]: value });
  };

  // Summary counts
  const ductCount = props.measurements.filter((m) => m.systemType === 'duct').length;
  const pipeCount = props.measurements.filter((m) => m.systemType === 'pipe').length;
  const totalLF = props.measurements.reduce((sum, m) => sum + m.lengthFt, 0);

  return (
    <>
      {/* Summary */}
      <div style={styles.card}>
        <div style={{ display: 'flex', justifyContent: 'space-around' }}>
          <div style={styles.stat}>
            <div style={styles.statValue}>{ductCount}</div>
            <div style={styles.statLabel}>Duct Runs</div>
          </div>
          <div style={styles.stat}>
            <div style={styles.statValue}>{pipeCount}</div>
            <div style={styles.statLabel}>Pipe Runs</div>
          </div>
          <div style={styles.stat}>
            <div style={styles.statValue}>{Math.round(totalLF)}</div>
            <div style={styles.statLabel}>Total LF</div>
          </div>
        </div>
      </div>

      {/* Project Info */}
      <div style={styles.card}>
        <h3 style={{ margin: '0 0 8px', fontSize: 13 }}>Project Info</h3>
        <label style={styles.label}>Project Name</label>
        <input style={styles.input} value={projectInfo.projectName} onChange={(e) => updateProject('projectName', e.target.value)} />
        <label style={styles.label}>Customer</label>
        <input style={styles.input} value={projectInfo.customer} onChange={(e) => updateProject('customer', e.target.value)} />
        <label style={styles.label}>Location</label>
        <input style={styles.input} value={projectInfo.location} onChange={(e) => updateProject('location', e.target.value)} />
      </div>

      {/* Pricing Preferences */}
      <div style={styles.card}>
        <h3 style={{ margin: '0 0 8px', fontSize: 13 }}>Pricing</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div>
            <label style={styles.label}>Material Markup %</label>
            <input type="number" style={styles.input} value={preferences.materialMarkup} onChange={(e) => updatePref('materialMarkup', Number(e.target.value))} />
          </div>
          <div>
            <label style={styles.label}>Labor Markup %</label>
            <input type="number" style={styles.input} value={preferences.laborMarkup} onChange={(e) => updatePref('laborMarkup', Number(e.target.value))} />
          </div>
          <div>
            <label style={styles.label}>OH&P %</label>
            <input type="number" style={styles.input} value={preferences.overheadProfit} onChange={(e) => updatePref('overheadProfit', Number(e.target.value))} />
          </div>
          <div>
            <label style={styles.label}>Contingency %</label>
            <input type="number" style={styles.input} value={preferences.contingency} onChange={(e) => updatePref('contingency', Number(e.target.value))} />
          </div>
        </div>
        <label style={styles.label}>Labor Rate ($/hr)</label>
        <input type="number" style={styles.input} value={preferences.laborRate} onChange={(e) => updatePref('laborRate', Number(e.target.value))} />
      </div>

      {/* Actions */}
      <button style={styles.btnPrimary} onClick={props.onRunEstimation} disabled={props.isLoading || props.measurements.length === 0}>
        {props.isLoading ? 'Estimating...' : 'Generate Estimate'}
      </button>
      <button style={styles.btnSecondary} onClick={props.onApplyAnnotations} disabled={props.measurements.length === 0}>
        Annotate Drawing in Figma
      </button>
    </>
  );
}

// ---------------------------------------------------------------------------
// Quote Tab
// ---------------------------------------------------------------------------

interface QuoteTabProps {
  result: EstimationResult | null;
  onExportSVG: () => void;
}

function QuoteTab({ result, onExportSVG }: QuoteTabProps) {
  if (!result) {
    return <div style={styles.info}>Run an estimation to see the quote here.</div>;
  }

  const materialItems = result.lineItems.filter((li) => li.type === 'material');
  const laborItems = result.lineItems.filter((li) => li.type === 'labor');
  const summaryItems = result.lineItems.filter((li) => li.type === 'summary');

  const downloadQuote = () => {
    const lines = [
      `INSULATION ESTIMATE — ${result.quoteNumber}`,
      `Project: ${result.projectName}`,
      `Date: ${new Date().toLocaleDateString()}`,
      '',
      'MATERIALS',
      '-'.repeat(60),
      ...materialItems.map((li) => `${li.description.padEnd(35)} ${li.quantity.toFixed(1)} ${li.unit.padEnd(4)} $${li.total.toFixed(2)}`),
      '',
      'LABOR',
      '-'.repeat(60),
      ...laborItems.map((li) => `${li.description.padEnd(35)} ${li.quantity.toFixed(1)} ${li.unit.padEnd(4)} $${li.total.toFixed(2)}`),
      '',
      '-'.repeat(60),
      `Material Total:     $${result.materialTotal.toFixed(2)}`,
      `Labor Total:        $${result.laborTotal.toFixed(2)}`,
      ...summaryItems.map((li) => `${li.description.padEnd(20)} $${li.total.toFixed(2)}`),
      '-'.repeat(60),
      `GRAND TOTAL:        $${result.grandTotal.toFixed(2)}`,
    ];

    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `estimate_${result.quoteNumber}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <>
      {/* Totals */}
      <div style={styles.card}>
        <div style={{ textAlign: 'center', marginBottom: 8 }}>
          <div style={{ fontSize: 10, color: '#888' }}>Quote #{result.quoteNumber}</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: '#6ea8fe' }}>
            ${result.grandTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-around' }}>
          <div style={styles.stat}>
            <div style={{ ...styles.statValue, fontSize: 14 }}>${result.materialTotal.toFixed(2)}</div>
            <div style={styles.statLabel}>Materials</div>
          </div>
          <div style={styles.stat}>
            <div style={{ ...styles.statValue, fontSize: 14 }}>${result.laborTotal.toFixed(2)}</div>
            <div style={styles.statLabel}>Labor</div>
          </div>
          <div style={styles.stat}>
            <div style={{ ...styles.statValue, fontSize: 14 }}>{result.laborHours.toFixed(1)}</div>
            <div style={styles.statLabel}>Hours</div>
          </div>
        </div>
      </div>

      {/* Line Items */}
      <div style={styles.card}>
        <h3 style={{ margin: '0 0 8px', fontSize: 13 }}>Line Items</h3>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Description</th>
              <th style={{ ...styles.th, textAlign: 'right' }}>Qty</th>
              <th style={{ ...styles.th, textAlign: 'right' }}>Total</th>
            </tr>
          </thead>
          <tbody>
            {result.lineItems.map((li, i) => (
              <tr key={i} style={li.type === 'summary' ? { fontStyle: 'italic' } : {}}>
                <td style={styles.td}>{li.description}</td>
                <td style={{ ...styles.td, textAlign: 'right' }}>
                  {li.type !== 'summary' ? `${li.quantity.toFixed(1)} ${li.unit}` : ''}
                </td>
                <td style={{ ...styles.td, textAlign: 'right', fontWeight: li.type === 'summary' ? 600 : 400 }}>
                  ${li.total.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Warnings */}
      {result.warnings.length > 0 && (
        <div style={styles.card}>
          <h3 style={{ margin: '0 0 8px', fontSize: 13, color: '#ffa' }}>Warnings</h3>
          <ul style={{ margin: 0, paddingLeft: 16, fontSize: 11, color: '#dda' }}>
            {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}

      {/* Alternatives */}
      {result.alternatives.length > 0 && (
        <div style={styles.card}>
          <h3 style={{ margin: '0 0 8px', fontSize: 13 }}>Cost Alternatives</h3>
          {result.alternatives.map((alt, i) => (
            <div key={i} style={{ marginBottom: 8, fontSize: 11 }}>
              <div style={{ fontWeight: 600, color: '#ccc' }}>{alt.description}</div>
              <div style={{ color: '#888' }}>
                {alt.savings > 0
                  ? `Save $${alt.savings.toFixed(2)}`
                  : `Additional $${Math.abs(alt.savings).toFixed(2)}`}
                {' — '}
                {alt.tradeoff}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Export */}
      <button style={styles.btnPrimary} onClick={downloadQuote}>
        Download Quote (.txt)
      </button>
      <button style={styles.btnSecondary} onClick={onExportSVG}>
        Export Annotated Drawing (SVG)
      </button>
    </>
  );
}

// ---------------------------------------------------------------------------
// Settings Tab
// ---------------------------------------------------------------------------

interface SettingsTabProps {
  apiUrl: string;
  onApiUrlChange: (v: string) => void;
  useApi: boolean;
  onUseApiChange: (v: boolean) => void;
}

function SettingsTab({ apiUrl, onApiUrlChange, useApi, onUseApiChange }: SettingsTabProps) {
  return (
    <>
      <div style={styles.card}>
        <h3 style={{ margin: '0 0 8px', fontSize: 13 }}>Estimation Backend</h3>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8, gap: 8 }}>
          <input
            type="checkbox"
            checked={useApi}
            onChange={(e) => onUseApiChange(e.target.checked)}
            id="useApi"
          />
          <label htmlFor="useApi" style={{ fontSize: 12, color: '#ccc' }}>
            Use remote API (falls back to local if unavailable)
          </label>
        </div>
        {useApi && (
          <>
            <label style={styles.label}>API URL</label>
            <input
              style={styles.input}
              value={apiUrl}
              onChange={(e) => onApiUrlChange(e.target.value)}
              placeholder="http://localhost:8501/api/estimate"
            />
          </>
        )}
        <div style={styles.info}>
          <strong>Local mode:</strong> Estimates are calculated entirely within the plugin using
          built-in pricing data. No API key or network connection required.
          <br /><br />
          <strong>API mode:</strong> Connects to the Pro Insulation Estimation backend for
          advanced AI-powered analysis with Claude. Requires a running backend instance.
        </div>
      </div>

      <div style={styles.card}>
        <h3 style={{ margin: '0 0 8px', fontSize: 13 }}>About</h3>
        <div style={{ fontSize: 11, color: '#888' }}>
          <strong>Pro Insulation Estimator</strong> v1.0.0
          <br />
          Figma plugin for HVAC insulation estimation.
          <br /><br />
          Extract measurements from Figma drawings, calculate material quantities,
          and generate professional quotes — all without leaving Figma.
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function postToPlugin(msg: Record<string, unknown>): void {
  parent.postMessage({ pluginMessage: msg }, '*');
}

function downloadSVG(svg: string): void {
  const blob = new Blob([svg], { type: 'image/svg+xml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'insulation_annotated.svg';
  a.click();
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Mount
// ---------------------------------------------------------------------------

const rootEl = document.getElementById('root');
if (rootEl) {
  createRoot(rootEl).render(<App />);
}
