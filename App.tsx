


import React, { useState, useCallback, useMemo, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import {
  Step,
  ProjectInfo,
  TakeoffItem,
  PricingSettings,
  CalculatedLineItem,
  BillOfMaterialsItem,
  GeminiSpecAnalysis,
  GeminiDrawingAnalysis,
  DuctworkSpecItem,
  PipingSpecItem
} from './types';
import { analyzeSpecification, analyzeDrawings } from './services/geminiService';
import { generateDemoQuote, generateQuoteFromUI } from './estimator';
import {
  DUCT_PRICING,
  PIPE_PRICING,
  JACKETING_PRICING,
  ACCESSORY_PRICING,
  LABOR_RATES,
  TAKEOFF_FACTORS,
  ACCESSORY_COVERAGE,
  TYPICAL_PROJECT_STANDARDS
} from './constants';


// --- HELPER & UI COMPONENTS (Defined within App.tsx to keep file count low) ---

const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`bg-gray-800/50 backdrop-blur-sm shadow-lg rounded-xl p-6 md:p-8 border border-gray-700/50 ${className}`}>
    {children}
  </div>
);

// FIX: Changed HTMLButtonButtonElement to HTMLButtonElement to fix typo.
const Button: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary', size?: 'normal' | 'sm' }> = ({ children, className = '', variant = 'primary', size = 'normal', ...props }) => {
  const baseClasses = 'font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed rounded-md';
  const variantClasses = {
    primary: 'bg-blue-600 hover:bg-blue-500 text-white focus:ring-blue-500',
    secondary: 'bg-gray-600 hover:bg-gray-500 text-gray-200 focus:ring-gray-500',
  };
  const sizeClasses = {
    normal: 'px-6 py-2',
    sm: 'px-3 py-1 text-sm'
  };
  return <button className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`} {...props}>{children}</button>;
};

const ProjectDashboard: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [projects, setProjects] = useState<any[]>(() => {
    try {
      const raw = localStorage.getItem('gi_projects');
      return raw ? JSON.parse(raw) : [];
    } catch (e) { return []; }
  });

  const refresh = () => {
    try {
      const raw = localStorage.getItem('gi_projects');
      setProjects(raw ? JSON.parse(raw) : []);
    } catch (e) { setProjects([]); }
  };

  const downloadProject = (project: any) => {
    const blob = new Blob([project.quote.quoteText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `quote_${project.id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const deleteProject = (id: string) => {
    const filtered = projects.filter(p => p.id !== id);
    localStorage.setItem('gi_projects', JSON.stringify(filtered));
    setProjects(filtered);
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <Card className="max-w-3xl w-full">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold">Project Dashboard</h3>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={refresh}>Refresh</Button>
            <Button variant="secondary" size="sm" onClick={onClose}>Close</Button>
          </div>
        </div>

        {projects.length === 0 ? (
          <p className="text-sm text-gray-400">No saved projects. Use "Save to Dashboard" in the Generated Documents area to save quotes.</p>
        ) : (
          <div className="space-y-4 max-h-[60vh] overflow-y-auto">
            {projects.map((p) => (
              <div key={p.id} className="p-3 bg-gray-800 rounded border border-gray-700 flex justify-between items-center">
                <div>
                  <div className="font-semibold">{p.projectName}</div>
                  <div className="text-xs text-gray-400">Saved: {new Date(p.date).toLocaleString()}</div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="primary" onClick={() => downloadProject(p)}>Download Quote</Button>
                  <Button size="sm" variant="secondary" onClick={() => {
                    const blob = new Blob([JSON.stringify(p, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `project_${p.id}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                  }}>Export JSON</Button>
                  <Button size="sm" variant="secondary" onClick={() => deleteProject(p.id)}>Delete</Button>
                </div>
              </div>
            ))}
          </div>
        )}

      </Card>
    </div>
  );
};

const Input: React.FC<React.InputHTMLAttributes<HTMLInputElement> & { label: string }> = ({ label, id, ...props }) => (
  <div>
    <label htmlFor={id} className="block text-sm font-medium text-gray-300 mb-1">{label}</label>
    <input id={id} className="w-full bg-gray-900 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:ring-blue-500 focus:border-blue-500" {...props} />
  </div>
);

const Spinner: React.FC = () => (
  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
  </svg>
);

const Alert: React.FC<{ message: string; type: 'error' | 'info' }> = ({ message, type }) => {
  const colors = {
    error: 'bg-red-900/50 border-red-500 text-red-200',
    info: 'bg-blue-900/50 border-blue-500 text-blue-200',
  };
  return <div className={`p-4 rounded-md border ${colors[type]}`}>{message}</div>;
};

// --- MAIN APPLICATION ---

export default function App() {
  const [currentStep, setCurrentStep] = useState<Step>(Step.Documents);
  const [error, setError] = useState<string | null>(null);

  // State for all quote data
  const [projectInfo, setProjectInfo] = useState<ProjectInfo>({
    projectName: 'Example Commercial Building',
    location: 'Athens, GA',
    customer: 'Stiles Air',
    date: new Date().toISOString().split('T')[0],
    quoteNumber: `GI-${Math.floor(1000 + Math.random() * 9000)}`,
  });
  const [specAnalysis, setSpecAnalysis] = useState<GeminiSpecAnalysis | null>(null);
  const [drawingAnalysis, setDrawingAnalysis] = useState<GeminiDrawingAnalysis | null>(null);
  const [isSpecLoading, setIsSpecLoading] = useState(false);
  const [isDrawingLoading, setIsDrawingLoading] = useState(false);

  const [ductworkTakeoff, setDuctworkTakeoff] = useState<TakeoffItem[]>([
    { id: uuidv4(), size: '24x20', length: 180, fittings: 4 },
    { id: uuidv4(), size: '18x14', length: 225, fittings: 6 },
  ]);
  const [pipingTakeoff, setPipingTakeoff] = useState<TakeoffItem[]>([
    { id: uuidv4(), size: '2" CHW', length: 240, fittings: 12 },
  ]);

  const [pricing, setPricing] = useState<PricingSettings>({
    materialMarkup: 15,
    laborMarkup: 10,
    overheadProfit: 10,
    contingency: 5,
    laborAdjustment: 1.0,
    laborRate: 70,
  });

  const [quoteTemplate, setQuoteTemplate] = useState<'detailed' | 'summary' | 'budget'>('detailed');
  const [dashboardOpen, setDashboardOpen] = useState(false);


  const nextStep = () => setCurrentStep(s => Math.min(s + 1, Object.keys(Step).length / 2 - 1));
  const prevStep = () => setCurrentStep(s => Math.max(s - 1, 0));

  const handleSpecUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsSpecLoading(true);
    setError(null);
    try {
      const result = await analyzeSpecification(file);
      setSpecAnalysis(result);

      if (result.projectInfo) {
        const updates: Partial<ProjectInfo> = {};
        if (result.projectInfo.projectName) updates.projectName = result.projectInfo.projectName;
        if (result.projectInfo.location) updates.location = result.projectInfo.location;
        if (result.projectInfo.customer) updates.customer = result.projectInfo.customer;
        if (result.projectInfo.date) updates.date = result.projectInfo.date;

        setProjectInfo(prev => ({ ...prev, ...updates }));
      }

    } catch (err) {
      setError('Failed to analyze specifications. Please check your API key and file format.');
      console.error(err);
    } finally {
      setIsSpecLoading(false);
    }
  };

  const handleDrawingUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsDrawingLoading(true);
    setError(null);
    try {
      const result = await analyzeDrawings(file);
      setDrawingAnalysis(result);
      if (result.ductwork?.length > 0) {
        setDuctworkTakeoff(result.ductwork.map(d => ({ ...d, id: uuidv4() })));
      }
      if (result.piping?.length > 0) {
        setPipingTakeoff(result.piping.map(p => ({ ...p, id: uuidv4() })));
      }
    } catch (err) {
      setError('Failed to analyze drawings. Please check your API key and file format.');
      console.error(err);
    } finally {
      setIsDrawingLoading(false);
    }
  };

  // Render logic for each step
  const renderStep = () => {
    switch (currentStep) {
      case Step.Documents:
        return <DocumentUploadStep
          onSpecUpload={handleSpecUpload}
          onDrawingUpload={handleDrawingUpload}
          specAnalysis={specAnalysis}
          drawingAnalysis={drawingAnalysis}
          isSpecLoading={isSpecLoading}
          isDrawingLoading={isDrawingLoading}
        />;
      case Step.ProjectInfo:
        return <ProjectInfoStep projectInfo={projectInfo} setProjectInfo={setProjectInfo} />;
      case Step.Takeoff:
        return <TakeoffEntryStep
          ductwork={ductworkTakeoff}
          setDuctwork={setDuctworkTakeoff}
          piping={pipingTakeoff}
          setPiping={setPipingTakeoff}
        />;
      case Step.Review:
        return <ReviewAndPriceStep
          pricing={pricing}
          setPricing={setPricing}
          ductwork={ductworkTakeoff}
          piping={pipingTakeoff}
          specAnalysis={specAnalysis}
        />;
      case Step.Quote:
        return <GeneratedQuoteStep
          projectInfo={projectInfo}
          ductwork={ductworkTakeoff}
          piping={pipingTakeoff}
          pricing={pricing}
          specAnalysis={specAnalysis}
          quoteTemplate={quoteTemplate}
          setQuoteTemplate={setQuoteTemplate}
        />;
      default:
        return <div>Unknown Step</div>;
    }
  };

  const stepNames = ["Documents", "Project Info", "Takeoff", "Review & Price", "Generate Quote"];

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-4 sm:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white">Guaranteed Insulation</h1>
          <p className="text-xl text-blue-300">AI-Powered Quote Generator</p>
        </header>

        {/* Stepper */}
        <div className="flex items-center justify-center mb-8">
          {stepNames.map((name, index) => (
            <React.Fragment key={index}>
              <div className="flex items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg ${currentStep >= index ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400'}`}>
                  {index + 1}
                </div>
                <p className={`ml-3 ${currentStep >= index ? 'text-white' : 'text-gray-500'}`}>{name}</p>
              </div>
              {index < stepNames.length - 1 && <div className={`flex-auto border-t-2 mx-4 ${currentStep > index ? 'border-blue-600' : 'border-gray-700'}`}></div>}
            </React.Fragment>
          ))}
        </div>

        {error && <Alert message={error} type="error" />}

        <main className="mt-6">
          {renderStep()}
        </main>

        <footer className="mt-8 flex justify-between">
          <div className="flex gap-2">
            <Button variant="secondary" onClick={prevStep} disabled={currentStep === 0}>Previous</Button>
            <Button onClick={nextStep} disabled={currentStep === stepNames.length - 1}>Next</Button>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setDashboardOpen(true)}>Project Dashboard</Button>
          </div>
        </footer>
        {dashboardOpen && <ProjectDashboard onClose={() => setDashboardOpen(false)} />}
      </div>
    </div>
  );
}


// --- STEP COMPONENTS ---

const ProjectInfoStep: React.FC<{ projectInfo: ProjectInfo, setProjectInfo: React.Dispatch<React.SetStateAction<ProjectInfo>> }> = ({ projectInfo, setProjectInfo }) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setProjectInfo(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  return (
    <Card>
      <h2 className="text-2xl font-bold text-white mb-6">Project Information</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Input label="Project Name" id="projectName" name="projectName" value={projectInfo.projectName} onChange={handleChange} />
        <Input label="Location" id="location" name="location" value={projectInfo.location} onChange={handleChange} />
        <Input label="Customer" id="customer" name="customer" value={projectInfo.customer} onChange={handleChange} />
        <Input label="Date" id="date" name="date" type="date" value={projectInfo.date} onChange={handleChange} />
        <Input label="Quote #" id="quoteNumber" name="quoteNumber" value={projectInfo.quoteNumber} onChange={handleChange} />
      </div>
    </Card>
  );
};

const AnalysisSection: React.FC<{ title: string; items: string[] | undefined; itemClass?: string; symbol?: string }> = ({ title, items, itemClass = 'text-gray-300', symbol = '•' }) => {
  if (!items || items.length === 0) return null;
  return (
    <div className="mt-4">
      <h5 className="font-semibold text-blue-300">{title}</h5>
      <ul className="list-none text-sm space-y-1 mt-1 pl-2">
        {items.map((item, index) => <li key={index} className={`flex ${itemClass}`}><span className="mr-2 flex-shrink-0">{symbol}</span><span>{item}</span></li>)}
      </ul>
    </div>
  );
};

const ComparisonModal: React.FC<{
  results: { unusual: string[], questions: string[] };
  onClose: () => void;
}> = ({ results, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <Card className="max-w-2xl w-full">
        <h2 className="text-2xl font-bold text-white mb-4">Comparison to Standards</h2>
        <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
          <AnalysisSection
            title="🚩 Unusual Requirements Flagged"
            items={results.unusual.length > 0 ? results.unusual : ["None. All specified materials and thicknesses align with typical standards."]}
            itemClass={results.unusual.length > 0 ? "text-yellow-300" : "text-green-300"}
            symbol="🚩"
          />
          <AnalysisSection
            title="🤔 Suggested Clarification Questions"
            items={results.questions}
            itemClass="text-purple-300"
            symbol="🤔"
          />
        </div>
        <div className="text-right mt-6">
          <Button onClick={onClose}>Close</Button>
        </div>
      </Card>
    </div>
  );
};


const DocumentUploadStep: React.FC<{
  onSpecUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onDrawingUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  specAnalysis: GeminiSpecAnalysis | null;
  drawingAnalysis: GeminiDrawingAnalysis | null;
  isSpecLoading: boolean;
  isDrawingLoading: boolean;
}> = ({ onSpecUpload, onDrawingUpload, specAnalysis, drawingAnalysis, isSpecLoading, isDrawingLoading }) => {
  const specFileInputRef = useRef<HTMLInputElement>(null);
  const drawingFileInputRef = useRef<HTMLInputElement>(null);
  const [showComparison, setShowComparison] = useState(false);
  const [comparisonResults, setComparisonResults] = useState<{ unusual: string[], questions: string[] }>({ unusual: [], questions: [] });

  const compareSpecsToStandards = (analysis: GeminiSpecAnalysis) => {
    const unusual: string[] = [];
    const questions = [...TYPICAL_PROJECT_STANDARDS.commonClarifications];

    analysis.ductworkSystems.forEach(system => {
      const material = system.material?.toLowerCase();
      const standardMaterial = TYPICAL_PROJECT_STANDARDS.ductwork.material.toLowerCase();
      if (material && !material.includes(standardMaterial)) {
        unusual.push(`Duct System '${system.systemType}' specifies '${system.material}', which is non-standard (typical: ${TYPICAL_PROJECT_STANDARDS.ductwork.material}).`);
      }
      const thickness = parseFloat(system.thickness);
      if (!isNaN(thickness) && thickness !== TYPICAL_PROJECT_STANDARDS.ductwork.thickness) {
        unusual.push(`Duct System '${system.systemType}' specifies ${thickness}" thickness, which is non-standard (typical: ${TYPICAL_PROJECT_STANDARDS.ductwork.thickness}").`);
      }
    });

    analysis.pipingSystems.forEach(system => {
      const material = system.material?.toLowerCase();
      const standardMaterial = TYPICAL_PROJECT_STANDARDS.piping.material.toLowerCase();
      if (material && !material.includes(standardMaterial)) {
        unusual.push(`Pipe System '${system.systemType}' specifies '${system.material}', which is non-standard (typical: ${TYPICAL_PROJECT_STANDARDS.piping.material}).`);
      }
      const thickness = parseFloat(system.thickness);
      if (!isNaN(thickness) && thickness !== TYPICAL_PROJECT_STANDARDS.piping.thickness) {
        unusual.push(`Pipe System '${system.systemType}' specifies ${thickness}" thickness, which is non-standard (typical: ${TYPICAL_PROJECT_STANDARDS.piping.thickness}").`);
      }
    });

    setComparisonResults({ unusual, questions });
    setShowComparison(true);
  };

  return (
    <>
      {showComparison && <ComparisonModal results={comparisonResults} onClose={() => setShowComparison(false)} />}
      <Card>
        <h2 className="text-2xl font-bold text-white mb-6">Upload & Analyze Documents</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Specifications Column */}
          <div>
            <h3 className="text-lg font-semibold text-blue-300 mb-3">Specifications (PDF)</h3>
            <div className="flex gap-2">
              <Button onClick={() => specFileInputRef.current?.click()} disabled={isSpecLoading} className="flex-grow">
                {isSpecLoading ? <><Spinner /> Analyzing...</> : "Extract Specs"}
              </Button>
              <input ref={specFileInputRef} type="file" accept=".pdf" onChange={onSpecUpload} disabled={isSpecLoading} className="hidden" />
              <Button variant="secondary" onClick={() => compareSpecsToStandards(specAnalysis!)} disabled={!specAnalysis}>Compare to Standards</Button>
            </div>

            {specAnalysis && (
              <div className="mt-4 p-4 bg-gray-900/50 rounded-lg border border-gray-700 max-h-[40rem] overflow-y-auto">
                <h4 className="font-bold text-white">Analysis Results:</h4>

                {/* Ductwork Table */}
                <h5 className="font-semibold text-blue-300 mt-4">Ductwork Systems</h5>
                {specAnalysis.ductworkSystems?.length > 0 ? (
                  <div className="overflow-x-auto mt-2">
                    <table className="w-full text-xs whitespace-nowrap">
                      <thead className="bg-gray-800">
                        <tr>
                          <th className="p-2 text-left">System Type</th>
                          <th className="p-2 text-left">Thickness</th>
                          <th className="p-2 text-left">Material</th>
                          <th className="p-2 text-left">Facing</th>
                          <th className="p-2 text-left">Location</th>
                        </tr>
                      </thead>
                      <tbody>
                        {specAnalysis.ductworkSystems.map((s, i) => (
                          <tr key={i} className="border-b border-gray-700">
                            <td className="p-2 font-semibold">{s.systemType}</td>
                            <td className="p-2">{s.thickness}</td>
                            <td className="p-2">{s.material}</td>
                            <td className="p-2">{s.facing}</td>
                            <td className="p-2">{s.location}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : <p className="text-sm text-gray-500 mt-2">No ductwork systems found.</p>}

                {/* Piping Table */}
                <h5 className="font-semibold text-blue-300 mt-4">Piping Systems</h5>
                {specAnalysis.pipingSystems?.length > 0 ? (
                  <div className="overflow-x-auto mt-2">
                    <table className="w-full text-xs whitespace-nowrap">
                      <thead className="bg-gray-800">
                        <tr>
                          <th className="p-2 text-left">System Type</th>
                          <th className="p-2 text-left">Thickness</th>
                          <th className="p-2 text-left">Material</th>
                          <th className="p-2 text-left">Jacket</th>
                          <th className="p-2 text-left">Location</th>
                        </tr>
                      </thead>
                      <tbody>
                        {specAnalysis.pipingSystems.map((s, i) => (
                          <tr key={i} className="border-b border-gray-700">
                            <td className="p-2 font-semibold">{s.systemType}</td>
                            <td className="p-2">{s.thickness}</td>
                            <td className="p-2">{s.material}</td>
                            <td className="p-2">{s.jacket}</td>
                            <td className="p-2">{s.location}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : <p className="text-sm text-gray-500 mt-2">No piping systems found.</p>}

                {/* Summary Sections */}
                <AnalysisSection title="✓ Confirmed Requirements" items={specAnalysis.summary.confirmed} itemClass="text-green-300" symbol="✓" />
                <AnalysisSection title="⚠️ Needs Clarification" items={specAnalysis.summary.clarificationNeeded} itemClass="text-yellow-300" symbol="⚠️" />
                <AnalysisSection title="💡 Assumptions Made" items={specAnalysis.summary.assumptions} itemClass="text-purple-300" symbol="💡" />
                <AnalysisSection title="📋 Special Requirements" items={specAnalysis.specialRequirements} symbol="📋" />
                <AnalysisSection title="❓ Ambiguities Found" items={specAnalysis.ambiguities} itemClass="text-red-400" symbol="❓" />
              </div>
            )}
          </div>
          {/* Drawings Column */}
          <div>
            <h3 className="text-lg font-semibold text-blue-300 mb-3">Drawings (PDF)</h3>
            <Button onClick={() => drawingFileInputRef.current?.click()} disabled={isDrawingLoading} className="w-full">
              {isDrawingLoading ? <><Spinner /> Analyzing...</> : "Perform AI Takeoff"}
            </Button>
            <input ref={drawingFileInputRef} type="file" accept=".pdf" onChange={onDrawingUpload} disabled={isDrawingLoading} className="hidden" />

            {drawingAnalysis && (
              <div className="mt-4 p-4 bg-gray-900/50 rounded-lg border border-gray-700 max-h-60 overflow-y-auto">
                <h4 className="font-bold text-white">Takeoff Summary:</h4>
                <p className="text-sm text-gray-300 mt-2"><strong>Scale:</strong> {drawingAnalysis.scale}</p>
                <p className="text-sm text-gray-300 mt-2"><strong>Ductwork Found:</strong></p>
                <ul className="list-disc list-inside text-sm text-gray-400">
                  {drawingAnalysis.ductwork.map((d, i) => <li key={i}>{d.length} LF of {d.size} ({d.fittings} fittings)</li>)}
                </ul>
                <p className="text-sm text-gray-300 mt-2"><strong>Piping Found:</strong></p>
                <ul className="list-disc list-inside text-sm text-gray-400">
                  {drawingAnalysis.piping.map((p, i) => <li key={i}>{p.length} LF of {p.size} ({p.fittings} fittings)</li>)}
                </ul>
                <p className="text-sm text-gray-300 mt-2"><i><strong>Notes:</strong> {drawingAnalysis.notes}</i></p>
              </div>
            )}
          </div>
        </div>
      </Card>
    </>
  );
};

const TakeoffEntryStep: React.FC<{
  ductwork: TakeoffItem[];
  setDuctwork: React.Dispatch<React.SetStateAction<TakeoffItem[]>>;
  piping: TakeoffItem[];
  setPiping: React.Dispatch<React.SetStateAction<TakeoffItem[]>>;
}> = ({ ductwork, setDuctwork, piping, setPiping }) => {

  // FIX: Updated function signature to be more type-safe, which resolves a TypeScript error at the call sites.
  const handleItemChange = <T extends TakeoffItem, K extends keyof Omit<T, 'id'>>(id: string, field: K, value: T[K], setter: React.Dispatch<React.SetStateAction<T[]>>) => {
    setter(prev => prev.map(item => item.id === id ? { ...item, [field]: value } : item));
  };

  const addItem = <T extends TakeoffItem,>(setter: React.Dispatch<React.SetStateAction<T[]>>, newItem: T) => {
    setter(prev => [...prev, newItem]);
  };

  const removeItem = <T extends TakeoffItem,>(id: string, setter: React.Dispatch<React.SetStateAction<T[]>>) => {
    setter(prev => prev.filter(item => item.id !== id));
  };

  // FIX: Removed generic <T> from renderTakeoffTable and used TakeoffItem directly. This fixes type inference issues in the nested handleItemChange calls.
  const renderTakeoffTable = (title: string, items: TakeoffItem[], setter: React.Dispatch<React.SetStateAction<TakeoffItem[]>>, newItem: TakeoffItem) => (
    <div>
      <h3 className="text-lg font-semibold text-blue-300 mb-3">{title}</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-gray-700/50">
            <tr>
              <th className="p-3">Size</th>
              <th className="p-3">Length (LF)</th>
              <th className="p-3">Fittings (Qty)</th>
              <th className="p-3"></th>
            </tr>
          </thead>
          <tbody>
            {items.map(item => (
              <tr key={item.id} className="border-b border-gray-700">
                <td className="p-1"><input type="text" value={item.size} onChange={e => handleItemChange(item.id, 'size', e.target.value, setter)} className="w-full bg-gray-800 p-2 rounded" /></td>
                <td className="p-1"><input type="number" value={item.length} onChange={e => handleItemChange(item.id, 'length', parseFloat(e.target.value) || 0, setter)} className="w-full bg-gray-800 p-2 rounded" /></td>
                <td className="p-1"><input type="number" value={item.fittings} onChange={e => handleItemChange(item.id, 'fittings', parseInt(e.target.value, 10) || 0, setter)} className="w-full bg-gray-800 p-2 rounded" /></td>
                <td className="p-1 text-right"><Button variant="secondary" size="sm" onClick={() => removeItem(item.id, setter)}>Remove</Button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Button className="mt-4" onClick={() => addItem(setter, newItem)}>Add Row</Button>
    </div>
  );

  return (
    <Card>
      <h2 className="text-2xl font-bold text-white mb-6">Manual Takeoff Entry</h2>
      <div className="space-y-8">
        {renderTakeoffTable('Ductwork', ductwork, setDuctwork, { id: uuidv4(), size: '', length: 0, fittings: 0 })}
        {renderTakeoffTable('Piping', piping, setPiping, { id: uuidv4(), size: '', length: 0, fittings: 0 })}
      </div>
    </Card>
  );
};


const getDuctSurfaceArea = (size: string, length: number): number => {
  try {
    const [width, height] = size.toLowerCase().split('x').map(Number);
    if (!isNaN(width) && !isNaN(height)) {
      return ((width + height) * 2 / 12) * length;
    }
  } catch (e) {
    // Ignore parsing errors for non-standard sizes
  }
  return 0; // Return 0 if size format is wrong
};

const useQuoteCalculator = (ductwork: TakeoffItem[], piping: TakeoffItem[], pricing: PricingSettings) => {
  return useMemo(() => {
    const lineItems: CalculatedLineItem[] = [];
    const bom: BillOfMaterialsItem[] = [];
    let totalMaterialCost = 0;
    let totalLaborHours = 0;

    // --- Ductwork Calculation ---
    let totalDuctLf = 0;
    let totalDuctSurfaceArea = 0;
    ductwork.forEach(d => {
      const lengthWithWaste = d.length * TAKEOFF_FACTORS.duct_straight_waste;
      const materialCost = lengthWithWaste * DUCT_PRICING['1.5_fiberglass_fsk']; // Assuming 1.5" FSK
      totalMaterialCost += materialCost;
      lineItems.push({
        category: 'DUCTWORK INSULATION',
        description: `Supply/Return Ductwork - 1.5" Fiberglass FSK`,
        details: `${d.size} (includes fittings)`,
        quantity: lengthWithWaste,
        unit: 'LF',
        unitPrice: DUCT_PRICING['1.5_fiberglass_fsk'],
        total: materialCost,
        type: 'material'
      });

      const laborHours = (lengthWithWaste / LABOR_RATES.duct_rectangular_medium) + (d.fittings * LABOR_RATES.duct_fitting);
      totalLaborHours += laborHours;
      totalDuctLf += lengthWithWaste;
      totalDuctSurfaceArea += getDuctSurfaceArea(d.size, lengthWithWaste);
    });

    if (totalDuctSurfaceArea > 0) {
      const DUCT_WRAP_ROLL_SQFT_COVERAGE = 300;
      const ductWrapRolls = Math.ceil(totalDuctSurfaceArea / DUCT_WRAP_ROLL_SQFT_COVERAGE);
      bom.push({
        category: 'DUCT INSULATION',
        item: `1.5" Fiberglass Duct Wrap w/ FSK`,
        quantity: `${ductWrapRolls} rolls (approx ${Math.round(totalDuctSurfaceArea)} SF coverage)`
      });
    }

    // --- Piping Calculation ---
    const pipeBomItems: Record<string, { material: string, totalLength: number, sizes: Record<string, number> }> = {};
    piping.forEach(p => {
      const adjustedLength = p.length + (p.fittings * TAKEOFF_FACTORS.pipe_elbow_equivalent_lf);
      const materialCost = adjustedLength * PIPE_PRICING['1.0_elastomeric'];
      totalMaterialCost += materialCost;
      lineItems.push({
        category: 'PIPING INSULATION',
        description: `Chilled Water - 1" Elastomeric`,
        details: `${p.size} pipe (includes fittings)`,
        quantity: adjustedLength,
        unit: 'LF',
        unitPrice: PIPE_PRICING['1.0_elastomeric'],
        total: materialCost,
        type: 'material'
      });

      const laborHours = (adjustedLength / LABOR_RATES.pipe_medium) + (p.fittings * LABOR_RATES.pipe_fitting);
      totalLaborHours += laborHours;

      const pipeMaterial = '1" Elastomeric Pipe Insulation, 1/2" wall';
      if (!pipeBomItems[pipeMaterial]) {
        pipeBomItems[pipeMaterial] = { material: pipeMaterial, totalLength: 0, sizes: {} };
      }
      pipeBomItems[pipeMaterial].totalLength += adjustedLength;
      pipeBomItems[pipeMaterial].sizes[p.size] = (pipeBomItems[pipeMaterial].sizes[p.size] || 0) + adjustedLength;
    });

    Object.values(pipeBomItems).forEach(group => {
      const sizeDetails = Object.entries(group.sizes)
        .map(([size, length]) => `  ${size} pipe size: ${Math.ceil(length)} LF`)
        .join('\n');
      bom.push({
        category: 'PIPE INSULATION',
        item: `${group.material}\n${sizeDetails}`,
        quantity: ``
      });
    });

    // --- Accessories ---
    const accessoryLineItems: CalculatedLineItem[] = [];
    const accessoryBom: BillOfMaterialsItem[] = [];
    const adhesiveGallons = Math.ceil(totalDuctLf / ACCESSORY_COVERAGE.adhesive_gallon_per_lf);
    if (adhesiveGallons > 0) {
      const adhesiveCost = adhesiveGallons * ACCESSORY_PRICING.adhesive_gallon;
      totalMaterialCost += adhesiveCost;
      accessoryLineItems.push({ category: 'ACCESSORIES & MATERIALS', description: 'Adhesive', details: '', quantity: adhesiveGallons, unit: 'GAL', unitPrice: ACCESSORY_PRICING.adhesive_gallon, total: adhesiveCost, type: 'material' });
      accessoryBom.push({ category: 'ACCESSORIES', item: 'Duct Insulation Adhesive', quantity: `${adhesiveGallons} gallons` });
    }
    const masticGallons = Math.ceil(totalDuctSurfaceArea / ACCESSORY_COVERAGE.mastic_gallon_per_sf);
    if (masticGallons > 0) {
      const masticCost = masticGallons * ACCESSORY_PRICING.mastic_gallon;
      totalMaterialCost += masticCost;
      accessoryLineItems.push({ category: 'ACCESSORIES & MATERIALS', description: 'Mastic Vapor Seal', details: '', quantity: masticGallons, unit: 'GAL', unitPrice: ACCESSORY_PRICING.mastic_gallon, total: masticCost, type: 'material' });
      accessoryBom.push({ category: 'ACCESSORIES', item: 'Mastic Vapor Seal', quantity: `${masticGallons} gallons` });
    }
    const tapeRolls = Math.ceil(totalDuctLf / ACCESSORY_COVERAGE.fsk_tape_roll_per_lf);
    if (tapeRolls > 0) {
      accessoryBom.push({ category: 'ACCESSORIES', item: 'FSK Tape, 3" wide', quantity: `${tapeRolls} rolls` });
    }
    lineItems.push(...accessoryLineItems);
    bom.push(...accessoryBom);

    // --- Totals ---
    const baseMaterialCost = totalMaterialCost;
    const materialWithMarkup = baseMaterialCost * (1 + pricing.materialMarkup / 100);

    const adjustedLaborHours = totalLaborHours * pricing.laborAdjustment;
    const baseLaborCost = adjustedLaborHours * pricing.laborRate;
    const laborWithMarkup = baseLaborCost * (1 + pricing.laborMarkup / 100);

    const subtotal = materialWithMarkup + laborWithMarkup;
    const overheadAndProfitAmount = subtotal * (pricing.overheadProfit / 100);
    const totalBeforeContingency = subtotal + overheadAndProfitAmount;
    const contingencyAmount = totalBeforeContingency * (pricing.contingency / 100);
    const grandTotal = totalBeforeContingency + contingencyAmount;

    return { lineItems, bom, baseMaterialCost, materialWithMarkup, baseLaborCost, laborWithMarkup, subtotal, overheadAndProfitAmount, contingencyAmount, grandTotal, adjustedLaborHours };

  }, [ductwork, piping, pricing]);
};

// Consistency Validation Rules
const validateQuoteConsistency = (
  specAnalysis: GeminiSpecAnalysis | null,
  ductwork: TakeoffItem[],
  piping: TakeoffItem[],
  calculatedData: { lineItems: CalculatedLineItem[], adjustedLaborHours: number }
): string[] => {
  const issues: string[] = [];

  // Check 1: Spec systems vs. Takeoff quantities
  if (specAnalysis) {
    if (specAnalysis.ductworkSystems.length > 0 && ductwork.reduce((sum, item) => sum + item.length, 0) === 0) {
      issues.push("⚠️ Ductwork is specified in the specs, but no takeoff quantities have been entered.");
    }
    if (specAnalysis.pipingSystems.length > 0 && piping.reduce((sum, item) => sum + item.length, 0) === 0) {
      issues.push("⚠️ Piping is specified in the specs, but no takeoff quantities have been entered.");
    }
  }

  // Check 2: All takeoff items have pricing
  calculatedData.lineItems.forEach(item => {
    if (item.type === 'material' && item.total === 0 && item.quantity > 0) {
      issues.push(`⚠️ "${item.description}" has a quantity but the total price is zero. Check pricing constants.`);
    }
  });

  // Check 3: Labor hours reasonable
  const totalLF = [...ductwork, ...piping].reduce((sum, item) => sum + item.length, 0);
  const totalHours = calculatedData.adjustedLaborHours;

  if (totalLF > 50 && totalHours > 0) { // Only check for non-trivial amounts
    const ductLF = ductwork.reduce((sum, item) => sum + item.length, 0);
    const pipeLF = piping.reduce((sum, item) => sum + item.length, 0);

    // Use a weighted average production rate for more accuracy
    const expectedDuctHours = ductLF / LABOR_RATES.duct_rectangular_medium;
    const expectedPipeHours = pipeLF / LABOR_RATES.pipe_medium;
    const expectedHours = expectedDuctHours + expectedPipeHours;

    // Allow for a 40% variance to account for fittings, complexity, and adjustments
    if (Math.abs(totalHours - expectedHours) / expectedHours > 0.4) {
      issues.push(`⚠️ Labor hours (${totalHours.toFixed(1)} hrs) seem ${totalHours > expectedHours ? 'high' : 'low'} for the scope (${totalLF} LF). Consider the Labor Adjustment Factor.`);
    }
  } else if (totalLF > 0 && totalHours === 0) {
    issues.push("⚠️ Takeoff quantities exist but no labor hours were calculated.");
  }

  return issues;
};

const ReviewAndPriceStep: React.FC<{
  pricing: PricingSettings;
  setPricing: React.Dispatch<React.SetStateAction<PricingSettings>>;
  ductwork: TakeoffItem[];
  piping: TakeoffItem[];
  specAnalysis: GeminiSpecAnalysis | null;
}> = ({ pricing, setPricing, ductwork, piping, specAnalysis }) => {

  const calculatedData = useQuoteCalculator(ductwork, piping, pricing);
  const { grandTotal, baseMaterialCost, materialWithMarkup, baseLaborCost, laborWithMarkup, subtotal, overheadAndProfitAmount, contingencyAmount } = calculatedData;
  const consistencyIssues = validateQuoteConsistency(specAnalysis, ductwork, piping, calculatedData);
  const [validationVisible, setValidationVisible] = useState(false);


  const handlePricingChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPricing(prev => ({ ...prev, [e.target.name]: parseFloat(e.target.value) || 0 }));
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div className="md:col-span-2 space-y-8">
        <Card>
          <h2 className="text-2xl font-bold text-white mb-6">Pricing Settings</h2>
          <div className="space-y-4">
            {[
              { name: 'materialMarkup', label: 'Material Markup (%)', value: pricing.materialMarkup },
              { name: 'laborMarkup', label: 'Labor Markup (%)', value: pricing.laborMarkup },
              { name: 'overheadProfit', label: 'Overhead & Profit (%)', value: pricing.overheadProfit },
              { name: 'contingency', label: 'Contingency (%)', value: pricing.contingency },
              { name: 'laborAdjustment', label: 'Labor Adjustment Factor', value: pricing.laborAdjustment, step: 0.05 },
              { name: 'laborRate', label: 'Burdened Labor Rate ($/hr)', value: pricing.laborRate },
            ].map(p => (
              <div key={p.name}>
                <label htmlFor={p.name} className="block text-sm font-medium text-gray-300">{p.label}: {p.value}{p.name.includes('Rate') ? '' : p.name.includes('Factor') ? 'x' : '%'}</label>
                <input type="range" id={p.name} name={p.name} min="0" max={p.name.includes('Factor') ? "2" : "50"} step={p.step || 1} value={p.value} onChange={handlePricingChange} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer" />
              </div>
            ))}
          </div>
        </Card>
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-white">Consistency Check</h2>
            <Button onClick={() => setValidationVisible(true)}>Validate Consistency</Button>
          </div>
          {validationVisible && (
            <>
              {consistencyIssues.length > 0 ? (
                <ul className="space-y-2">
                  {consistencyIssues.map((issue, index) => (
                    <li key={index} className="text-yellow-300 text-sm">{issue}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-green-400 font-semibold">✅ All consistency checks passed.</p>
              )}
            </>
          )}
        </Card>
      </div>
      <div>
        <Card className="sticky top-8">
          <h3 className="text-xl font-bold text-white mb-4">Quote Summary</h3>
          <div className="space-y-2 text-gray-300">
            <div className="flex justify-between"><span>Base Materials:</span> <span>{baseMaterialCost.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
            <div className="flex justify-between"><span>Material Markup:</span> <span>{(materialWithMarkup - baseMaterialCost).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
            <hr className="border-gray-600" />
            <div className="flex justify-between font-semibold"><span>Total Materials:</span> <span>{materialWithMarkup.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
            <div className="h-4"></div>
            <div className="flex justify-between"><span>Base Labor:</span> <span>{baseLaborCost.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
            <div className="flex justify-between"><span>Labor Markup:</span> <span>{(laborWithMarkup - baseLaborCost).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
            <hr className="border-gray-600" />
            <div className="flex justify-between font-semibold"><span>Total Labor:</span> <span>{laborWithMarkup.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
            <div className="h-4"></div>
            <hr className="border-gray-600" />
            <div className="flex justify-between"><span>Subtotal:</span> <span>{subtotal.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
            <div className="flex justify-between"><span>Overhead & Profit:</span> <span>{overheadAndProfitAmount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
            <div className="flex justify-between"><span>Contingency:</span> <span>{contingencyAmount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
            <hr className="border-t-2 border-gray-500 my-2" />
            <div className="flex justify-between text-2xl font-bold text-white">
              <span>Grand Total:</span>
              <span>{grandTotal.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

const GeneratedQuoteStep: React.FC<{
  projectInfo: ProjectInfo;
  ductwork: TakeoffItem[];
  piping: TakeoffItem[];
  pricing: PricingSettings;
  specAnalysis: GeminiSpecAnalysis | null;
  quoteTemplate: 'detailed' | 'summary' | 'budget';
  setQuoteTemplate: React.Dispatch<React.SetStateAction<'detailed' | 'summary' | 'budget'>>;
}> = (props) => {
  const { lineItems, bom, grandTotal, materialWithMarkup, laborWithMarkup, subtotal, overheadAndProfitAmount, contingencyAmount } = useQuoteCalculator(props.ductwork, props.piping, props.pricing);

  const [view, setView] = useState<'quote' | 'bom'>('quote');

  const handlePrint = () => {
    window.print();
  };

  const QuoteHeader = () => (
    <div className="flex justify-between items-start mb-8">
      <div>
        <h1 className="text-3xl font-bold">GUARANTEED INSULATION</h1>
        <p className="text-sm">123 Insulation Way, Athens, GA 30601</p>
      </div>
      <div className="text-right text-sm">
        <p><strong>Contact:</strong> Glen Moss</p>
        <p><strong>Phone:</strong> (706) 123-4567</p>
        <p><strong>Email:</strong> glmoss@guaranteedinsulation.com</p>
      </div>
    </div>
  );

  const ProjectInfoTable = () => (
    <table className="w-full text-sm mb-8">
      <tbody>
        <tr>
          <td className="font-bold pr-4 py-1">Project:</td>
          <td className="py-1">{props.projectInfo.projectName}</td>
          <td className="font-bold pr-4 py-1 text-right">Date:</td>
          <td className="py-1 w-1/4">{props.projectInfo.date}</td>
        </tr>
        <tr>
          <td className="font-bold pr-4 py-1">Location:</td>
          <td className="py-1">{props.projectInfo.location}</td>
          <td className="font-bold pr-4 py-1 text-right">Quote #:</td>
          <td className="py-1">{props.projectInfo.quoteNumber}</td>
        </tr>
        <tr>
          <td className="font-bold pr-4 py-1">Customer:</td>
          <td className="py-1">{props.projectInfo.customer}</td>
          <td className="font-bold pr-4 py-1 text-right">Valid:</td>
          <td className="py-1">30 Days</td>
        </tr>
      </tbody>
    </table>
  );

  const SummaryQuote = () => (
    <div className="bg-white text-black p-8 font-sans printable-area">
      <QuoteHeader />
      <h2 className="text-2xl font-semibold mt-4 text-center border-b-2 border-black pb-2 mb-6">BUDGET PROPOSAL</h2>
      <ProjectInfoTable />

      <div className="mb-8">
        <h3 className="font-bold text-lg border-b border-gray-400 mb-2">SUMMARY SCOPE OF WORK</h3>
        <p className="text-sm">Guaranteed Insulation proposes to furnish and install mechanical insulation for the systems listed below, based on the project specifications provided.</p>
        {props.specAnalysis && (
          <ul className="text-sm list-disc list-inside mt-2 space-y-1">
            {props.specAnalysis.summary.confirmed.map((item, index) => <li key={index}>{item}</li>)}
          </ul>
        )}
      </div>

      <div className="my-10 text-center">
        <p className="text-gray-700 uppercase tracking-wider">Total Project Investment</p>
        <p className="text-5xl font-bold tracking-tight mt-2">{grandTotal.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</p>
      </div>

      <div className="text-xs text-gray-600 mt-8 space-y-2">
        <div>
          <h4 className="font-bold uppercase">Exclusions & Qualifications:</h4>
          <p>This budget proposal excludes scaffolding, lifts, demolition, permits, and sales tax. Pricing is based on project specifications dated {props.projectInfo.date} and assumes clear access to work areas during normal business hours. This quote is valid for 30 days.</p>
        </div>
      </div>
    </div>
  );

  const BudgetQuote = () => {
    const budgetRangeLower = grandTotal - contingencyAmount;
    const budgetRangeUpper = grandTotal + contingencyAmount;

    return (
      <div className="bg-white text-black p-8 font-sans printable-area">
        <QuoteHeader />
        <h2 className="text-2xl font-semibold mt-4 text-center border-b-2 border-black pb-2 mb-6">BUDGETARY ESTIMATE</h2>
        <ProjectInfoTable />

        <div className="mb-8">
          <h3 className="font-bold text-lg border-b border-gray-400 mb-2">HIGH-LEVEL SCOPE</h3>
          <p className="text-sm">This budgetary estimate covers the furnishing and installation of mechanical insulation for the primary HVAC systems as understood from preliminary documents. The scope generally includes:</p>
          <ul className="text-sm list-disc list-inside mt-2 space-y-1">
            {props.ductwork.length > 0 && <li>Insulation for rectangular and round ductwork (supply, return, exhaust).</li>}
            {props.piping.length > 0 && <li>Insulation for mechanical piping (chilled water, heating water, etc.).</li>}
            <li>Associated fittings, vapor barriers, and sealants as per standard industry practice.</li>
          </ul>
        </div>

        <div className="my-10 text-center bg-gray-100 p-6 rounded-lg">
          <p className="text-gray-700 uppercase tracking-wider">Estimated Project Budget Range</p>
          <p className="text-4xl font-bold tracking-tight mt-2">
            {budgetRangeLower.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })} - {budgetRangeUpper.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}
          </p>
          <p className="text-sm text-gray-600 mt-2">Final pricing subject to detailed takeoff and final specifications.</p>
        </div>

        <div className="text-xs text-gray-600 mt-8 space-y-2">
          <h4 className="font-bold uppercase">Allowances & Clarifications:</h4>
          <p>This estimate includes allowances for typical quantities of fittings and accessories. It excludes work on existing systems, demolition, premium time, and specialized access equipment unless otherwise noted. This is for planning purposes and is not a firm bid.</p>
        </div>
      </div>
    );
  };

  const DetailedQuote = () => {
    // FIX: Correctly typed the accumulator for the reduce function to resolve 'map' does not exist on type 'unknown' error.
    const groupedLineItems = lineItems.reduce<Record<string, CalculatedLineItem[]>>((acc, item) => {
      const category = item.category || 'Miscellaneous';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(item);
      return acc;
    }, {});

    return (
      <div className="bg-white text-black p-8 font-sans printable-area">
        <QuoteHeader />
        <h2 className="text-2xl font-semibold mt-4 text-center border-b-2 border-black pb-2 mb-6">MECHANICAL INSULATION PROPOSAL</h2>
        <ProjectInfoTable />

        {/* Scope of Work */}
        <div className="mb-8">
          <h3 className="font-bold text-lg border-b border-gray-400 mb-2">SCOPE OF WORK</h3>
          <p className="text-sm">Guaranteed Insulation shall furnish and install mechanical insulation per project specifications. All work to be performed in a neat and workmanlike manner, conforming to industry standards such as ASTM and SMACNA.</p>
          {props.specAnalysis && (
            <ul className="text-sm list-disc list-inside mt-2 space-y-1">
              {props.specAnalysis.summary.confirmed.map((item, index) => <li key={index}>{item}</li>)}
            </ul>
          )}
        </div>

        {/* Pricing Table */}
        <table className="w-full text-sm mb-4">
          <thead className="bg-gray-200">
            <tr>
              <th className="text-left p-2 font-bold">ITEM DESCRIPTION</th>
              <th className="text-right p-2 font-bold">QTY</th>
              <th className="text-right p-2 font-bold">UNIT</th>
              <th className="text-right p-2 font-bold">UNIT PRICE</th>
              <th className="text-right p-2 font-bold">TOTAL</th>
            </tr>
          </thead>
          <tbody>
            {(Object.entries(groupedLineItems) as [string, CalculatedLineItem[]][]).map(([category, items]) => (
              <React.Fragment key={category}>
                <tr>
                  <td colSpan={5} className="p-2 font-bold bg-gray-100">{category}</td>
                </tr>
                {items.map((item, index) => (
                  <tr key={index} className="border-b border-gray-200">
                    <td className="p-2">{item.description} <span className="text-gray-600">{item.details}</span></td>
                    <td className="text-right p-2">{item.quantity.toFixed(1)}</td>
                    <td className="text-right p-2">{item.unit}</td>
                    <td className="text-right p-2">{item.unitPrice.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</td>
                    <td className="text-right p-2">{item.total.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</td>
                  </tr>
                ))}
              </React.Fragment>
            ))}
          </tbody>
        </table>

        {/* Summary Totals */}
        <div className="flex justify-end mt-4">
          <div className="w-full max-w-sm text-sm">
            <div className="flex justify-between p-2"><span className="font-semibold">MATERIAL TOTAL:</span> <span>{materialWithMarkup.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
            <div className="flex justify-between p-2"><span className="font-semibold">LABOR TOTAL:</span> <span>{laborWithMarkup.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
            <div className="flex justify-between p-2 border-t border-gray-400"><span className="font-semibold">SUBTOTAL:</span> <span>{subtotal.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
            <div className="flex justify-between p-2"><span className="">Overhead & Profit:</span> <span>{overheadAndProfitAmount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
            <div className="flex justify-between p-2"><span className="">Contingency:</span> <span>{contingencyAmount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
            <div className="flex justify-between bg-gray-200 p-2 text-lg font-bold"><span >TOTAL QUOTE:</span> <span >{grandTotal.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
          </div>
        </div>

        {/* Fine Print */}
        <div className="text-xs text-gray-600 mt-8 space-y-2">
          <div>
            <h4 className="font-bold uppercase">Inclusions:</h4>
            <p>All materials and labor for installation as listed above; Normal cleanup and debris removal; Standard 1-year workmanship warranty.</p>
          </div>
          <div>
            <h4 className="font-bold uppercase">Exclusions:</h4>
            <p>Scaffolding, staging, lifts, or access equipment; Insulation removal or demolition; Permits and inspections; Work outside normal business hours (unless specified); Final cleaning beyond normal construction cleanup; Sales tax (if applicable).</p>
          </div>
          <div>
            <h4 className="font-bold uppercase">Qualifications:</h4>
            <p>Pricing is based on project specifications dated {props.projectInfo.date}. Assumes clear and ready access to all work areas during normal business hours.</p>
          </div>
          <div>
            <h4 className="font-bold uppercase">Terms & Conditions:</h4>
            <p>Quote valid for 30 days from date. Payment terms: Net 30 days. Required schedule notice: 2 weeks. Contractor carries required liability and workers comp insurance.</p>
          </div>
        </div>
      </div>
    );
  }

  const Quote = () => {
    if (props.quoteTemplate === 'summary') return <SummaryQuote />;
    if (props.quoteTemplate === 'budget') return <BudgetQuote />;
    return <DetailedQuote />;
  };

  // Save current UI-generated quote to dashboard (localStorage)
  const saveToDashboard = () => {
    const generated = generateQuoteFromUI(props.projectInfo, props.ductwork, props.piping, props.specAnalysis);
    const projectsJson = localStorage.getItem('gi_projects');
    const projects = projectsJson ? JSON.parse(projectsJson) : [];
    const projectRecord = {
      id: generated.quoteNumber,
      projectName: props.projectInfo.projectName,
      date: new Date().toISOString(),
      quote: generated,
      projectInfo: props.projectInfo,
    };
    projects.unshift(projectRecord);
    localStorage.setItem('gi_projects', JSON.stringify(projects));
    alert('Saved project to dashboard');
  };

  const BillOfMaterials = () => {
    // FIX: Correctly typed the accumulator for the reduce function to resolve 'map' does not exist on type 'unknown' error.
    const bomByCategory = bom.reduce<Record<string, BillOfMaterialsItem[]>>((acc, item) => {
      const category = item.category;
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(item);
      return acc;
    }, {});

    return (
      <div className="bg-white text-black p-8 font-sans printable-area">
        <h1 className="text-2xl font-bold mb-2">GUARANTEED INSULATION - MATERIAL ORDER LIST</h1>
        <p><strong>Project:</strong> {props.projectInfo.projectName}</p>
        <p><strong>Quote:</strong> {props.projectInfo.quoteNumber}</p>
        <p><strong>Date:</strong> {props.projectInfo.date}</p>

        <div className="mt-8 space-y-6">
          {(Object.entries(bomByCategory) as [string, BillOfMaterialsItem[]][]).sort(([categoryA], [categoryB]) => categoryA.localeCompare(categoryB)).map(([category, items]) => (
            <div key={category}>
              <h3 className="font-bold text-lg border-b border-gray-400 mb-2">{category}:</h3>
              <ul className="list-none space-y-2">
                {items.map((item, index) => (
                  <li key={index} className="whitespace-pre-line">
                    - {item.quantity && <>{' '}<span className="font-bold">{item.quantity}</span> -</>}{' '}
                    {item.item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 pt-4 border-t border-black">
          <p><strong>DELIVERY:</strong> [Date Needed]</p>
          <p><strong>SHIP TO:</strong> {props.projectInfo.location}</p>
        </div>
      </div>
    );
  };


  return (
    <Card>
      <div className="flex justify-between items-center mb-6 print:hidden">
        <div>
          <h2 className="text-2xl font-bold text-white mb-4">Generated Documents</h2>
          <div className="flex items-center gap-4">
            <div className="flex gap-2 items-center">
              <span className="text-gray-400 self-center text-sm">View:</span>
              <Button variant={view === 'quote' ? 'primary' : 'secondary'} onClick={() => setView('quote')} size="sm">Quote</Button>
              <Button variant={view === 'bom' ? 'primary' : 'secondary'} onClick={() => setView('bom')} size="sm">BOM</Button>
            </div>
            <div className="border-l border-gray-600 h-6"></div>
            <div className="flex gap-2 items-center">
              <label htmlFor="quoteTemplate" className="text-gray-400 self-center text-sm">Template:</label>
              <select
                id="quoteTemplate"
                value={props.quoteTemplate}
                onChange={(e) => props.setQuoteTemplate(e.target.value as any)}
                className="bg-gray-800 border border-gray-600 rounded-md px-3 py-1 text-sm text-gray-100 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
                disabled={view !== 'quote'}
              >
                <option value="detailed">Detailed</option>
                <option value="summary">Summary</option>
                <option value="budget">Budget</option>
              </select>
            </div>
            <div className="ml-2 flex items-center gap-2">
              <Button variant="secondary" size="sm" onClick={() => {
                const result = generateDemoQuote();
                // download quote
                const blob = new Blob([result.quoteText], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `quote_${result.quoteNumber}.txt`;
                a.click();
                URL.revokeObjectURL(url);

                const mb = new Blob([result.materialListText], { type: 'text/plain' });
                const mu = URL.createObjectURL(mb);
                const b = document.createElement('a');
                b.href = mu;
                b.download = `material_list_${result.quoteNumber}.txt`;
                b.click();
                URL.revokeObjectURL(mu);
              }}>Run Demo Estimator</Button>

              <Button variant="primary" size="sm" onClick={() => {
                const generated = generateQuoteFromUI(props.projectInfo, props.ductwork, props.piping, props.specAnalysis);
                // Download files directly
                const qb = new Blob([generated.quoteText], { type: 'text/plain' });
                const qu = URL.createObjectURL(qb);
                const a2 = document.createElement('a');
                a2.href = qu;
                a2.download = `quote_${generated.quoteNumber}.txt`;
                a2.click();
                URL.revokeObjectURL(qu);

                const mb2 = new Blob([generated.materialListText], { type: 'text/plain' });
                const mu2 = URL.createObjectURL(mb2);
                const b2 = document.createElement('a');
                b2.href = mu2;
                b2.download = `material_list_${generated.quoteNumber}.txt`;
                b2.click();
                URL.revokeObjectURL(mu2);
              }}>Export Quote</Button>

              <Button variant="secondary" size="sm" onClick={() => { saveToDashboard(); }}>Save to Dashboard</Button>
            </div>
          </div>
        </div>
        <Button onClick={handlePrint}>Print</Button>
      </div>
      <div className="bg-gray-700 p-2 rounded-lg">
        {view === 'quote' ? <Quote /> : <BillOfMaterials />}
      </div>
      <style>{`
              @media print {
                body {
                  background-color: white !important;
                }
                .printable-area {
                  display: block;
                  width: 100%;
                  margin: 0;
                  padding: 0;
                  box-shadow: none;
                  border: none;
                }
                .print-hidden, .print\:hidden {
                  display: none !important;
                }
                div:not(.printable-area), header, footer, main > div:not(.bg-gray-700) {
                    display: none !important;
                }
                .bg-gray-700 {
                    background: transparent !important;
                    padding: 0 !important;
                }
              }
            `}</style>
    </Card>
  );
};