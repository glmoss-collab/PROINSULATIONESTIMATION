
import React, { useState, useCallback, useMemo } from 'react';
import { v4 as uuidv4 } from 'uuid';
import {
  Step,
  ProjectInfo,
  TakeoffItem,
  PricingSettings,
  CalculatedLineItem,
  BillOfMaterialsItem,
  GeminiSpecAnalysis,
  GeminiDrawingAnalysis
} from './types';
import { analyzeSpecification, analyzeDrawings } from './services/geminiService';
import {
  DUCT_PRICING,
  PIPE_PRICING,
  JACKETING_PRICING,
  ACCESSORY_PRICING,
  LABOR_RATES,
  TAKEOFF_FACTORS,
  ACCESSORY_COVERAGE
} from './constants';


// --- HELPER & UI COMPONENTS (Defined within App.tsx to keep file count low) ---

const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`bg-gray-800/50 backdrop-blur-sm shadow-lg rounded-xl p-6 md:p-8 border border-gray-700/50 ${className}`}>
    {children}
  </div>
);

const Button: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' }> = ({ children, className = '', variant = 'primary', ...props }) => {
  const baseClasses = 'px-6 py-2 rounded-md font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed';
  const variantClasses = {
    primary: 'bg-blue-600 hover:bg-blue-500 text-white focus:ring-blue-500',
    secondary: 'bg-gray-600 hover:bg-gray-500 text-gray-200 focus:ring-gray-500',
  };
  return <button className={`${baseClasses} ${variantClasses[variant]} ${className}`} {...props}>{children}</button>;
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
            />;
      case Step.Quote:
        return <GeneratedQuoteStep
            projectInfo={projectInfo}
            ductwork={ductworkTakeoff}
            piping={pipingTakeoff}
            pricing={pricing}
            specAnalysis={specAnalysis}
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
          <Button variant="secondary" onClick={prevStep} disabled={currentStep === 0}>Previous</Button>
          <Button onClick={nextStep} disabled={currentStep === stepNames.length - 1}>Next</Button>
        </footer>
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

const DocumentUploadStep: React.FC<{
  onSpecUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onDrawingUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  specAnalysis: GeminiSpecAnalysis | null;
  drawingAnalysis: GeminiDrawingAnalysis | null;
  isSpecLoading: boolean;
  isDrawingLoading: boolean;
}> = ({ onSpecUpload, onDrawingUpload, specAnalysis, drawingAnalysis, isSpecLoading, isDrawingLoading }) => {
  return (
    <Card>
      <h2 className="text-2xl font-bold text-white mb-6">Upload & Analyze Documents</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Specifications Column */}
        <div>
          <h3 className="text-lg font-semibold text-blue-300 mb-3">Specifications (PDF)</h3>
          <Input label="Upload Spec File" id="specFile" type="file" accept=".pdf" onChange={onSpecUpload} disabled={isSpecLoading} />
          {isSpecLoading && <div className="flex items-center mt-4 text-blue-300"><Spinner />Analyzing Specs...</div>}
          {specAnalysis && (
            <div className="mt-4 p-4 bg-gray-900/50 rounded-lg border border-gray-700">
              <h4 className="font-bold text-white">Analysis Summary:</h4>
              <p className="text-sm text-gray-300 mt-2"><strong>Duct:</strong> {specAnalysis.ductwork.thickness} {specAnalysis.ductwork.material} w/ {specAnalysis.ductwork.facing}</p>
              <p className="text-sm text-gray-300"><strong>Pipe:</strong> {specAnalysis.piping.thickness} {specAnalysis.piping.material} w/ {specAnalysis.piping.jacketing}</p>
              <p className="text-sm text-gray-300 mt-2"><i>{specAnalysis.summary}</i></p>
            </div>
          )}
        </div>
        {/* Drawings Column */}
        <div>
          <h3 className="text-lg font-semibold text-blue-300 mb-3">Drawings (PDF)</h3>
          <Input label="Upload Drawing File" id="drawingFile" type="file" accept=".pdf" onChange={onDrawingUpload} disabled={isDrawingLoading} />
          {isDrawingLoading && <div className="flex items-center mt-4 text-blue-300"><Spinner />Analyzing Drawings...</div>}
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
  );
};

const TakeoffEntryStep: React.FC<{
  ductwork: TakeoffItem[];
  setDuctwork: React.Dispatch<React.SetStateAction<TakeoffItem[]>>;
  piping: TakeoffItem[];
  setPiping: React.Dispatch<React.SetStateAction<TakeoffItem[]>>;
}> = ({ ductwork, setDuctwork, piping, setPiping }) => {
  
  const handleItemChange = <T extends TakeoffItem, >(id: string, field: keyof Omit<T, 'id'>, value: string | number, setter: React.Dispatch<React.SetStateAction<T[]>>) => {
    setter(prev => prev.map(item => item.id === id ? { ...item, [field]: value } : item));
  };
  
  const addItem = <T extends TakeoffItem, >(setter: React.Dispatch<React.SetStateAction<T[]>>, newItem: T) => {
      setter(prev => [...prev, newItem]);
  };
  
  const removeItem = <T extends TakeoffItem, >(id: string, setter: React.Dispatch<React.SetStateAction<T[]>>) => {
    setter(prev => prev.filter(item => item.id !== id));
  };
  
  const renderTakeoffTable = <T extends TakeoffItem, >(title: string, items: T[], setter: React.Dispatch<React.SetStateAction<T[]>>, newItem: T) => (
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
                <td className="p-1 text-right"><Button variant="secondary" className="px-3 py-1 text-xs" onClick={() => removeItem(item.id, setter)}>Remove</Button></td>
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


const useQuoteCalculator = (ductwork: TakeoffItem[], piping: TakeoffItem[], pricing: PricingSettings) => {
    return useMemo(() => {
        const lineItems: CalculatedLineItem[] = [];
        const bom: BillOfMaterialsItem[] = [];
        let totalMaterialCost = 0;
        let totalLaborHours = 0;

        // --- Ductwork Calculation ---
        let totalDuctLf = 0;
        ductwork.forEach(d => {
            const materialCost = d.length * DUCT_PRICING['1.5_fiberglass_fsk']; // Assuming 1.5" FSK for simplicity
            totalMaterialCost += materialCost;
            lineItems.push({ description: `Ductwork Insulation - 1.5" FSK`, details: d.size, quantity: d.length, unit: 'LF', unitPrice: DUCT_PRICING['1.5_fiberglass_fsk'], total: materialCost, type: 'material' });
            
            const laborHours = (d.length / LABOR_RATES.duct_rectangular_medium) + (d.fittings * LABOR_RATES.duct_fitting);
            totalLaborHours += laborHours;
            totalDuctLf += d.length;
        });
        bom.push({ category: 'Duct Insulation', item: '1.5" Fiberglass Duct Board w/ FSK', quantity: `${Math.ceil(totalDuctLf * 1.1 / 40)} sheets` });

        // --- Piping Calculation ---
        let totalPipeLf = 0;
        piping.forEach(p => {
            const adjustedLength = p.length + (p.fittings * TAKEOFF_FACTORS.pipe_elbow_equivalent_lf); // Simplified fittings calc
            const materialCost = adjustedLength * PIPE_PRICING['1.0_elastomeric']; // Assuming 1" Elastomeric
            totalMaterialCost += materialCost;
            lineItems.push({ description: `Piping Insulation - 1" Elastomeric`, details: p.size, quantity: adjustedLength, unit: 'LF', unitPrice: PIPE_PRICING['1.0_elastomeric'], total: materialCost, type: 'material' });

            const laborHours = (adjustedLength / LABOR_RATES.pipe_medium) + (p.fittings * LABOR_RATES.pipe_fitting);
            totalLaborHours += laborHours;
            totalPipeLf += adjustedLength;
        });
        bom.push({ category: 'Pipe Insulation', item: '1" Elastomeric Pipe Insulation', quantity: `${Math.ceil(totalPipeLf * 1.05)} LF`});

        // --- Accessories ---
        const adhesiveGallons = Math.ceil(totalDuctLf / ACCESSORY_COVERAGE.adhesive_gallon_per_lf);
        if(adhesiveGallons > 0) {
            const adhesiveCost = adhesiveGallons * ACCESSORY_PRICING.adhesive_gallon;
            totalMaterialCost += adhesiveCost;
            lineItems.push({ description: 'Adhesive', details: '', quantity: adhesiveGallons, unit: 'GAL', unitPrice: ACCESSORY_PRICING.adhesive_gallon, total: adhesiveCost, type: 'material' });
            bom.push({ category: 'Accessories', item: 'Duct Insulation Adhesive', quantity: `${adhesiveGallons} gallons` });
        }
        
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


const ReviewAndPriceStep: React.FC<{
  pricing: PricingSettings;
  setPricing: React.Dispatch<React.SetStateAction<PricingSettings>>;
  ductwork: TakeoffItem[];
  piping: TakeoffItem[];
}> = ({ pricing, setPricing, ductwork, piping }) => {
    
    const { grandTotal, baseMaterialCost, materialWithMarkup, baseLaborCost, laborWithMarkup, subtotal, overheadAndProfitAmount, contingencyAmount } = useQuoteCalculator(ductwork, piping, pricing);

    const handlePricingChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setPricing(prev => ({ ...prev, [e.target.name]: parseFloat(e.target.value) || 0 }));
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="md:col-span-2">
                <Card>
                    <h2 className="text-2xl font-bold text-white mb-6">Review & Price</h2>
                    <div className="space-y-4">
                      {/* Pricing sliders */}
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
                          <input type="range" id={p.name} name={p.name} min="0" max={p.name.includes('Factor') ? "2" : "50"} step={p.step || 1} value={p.value} onChange={handlePricingChange} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"/>
                        </div>
                      ))}
                    </div>
                </Card>
            </div>
            <div>
              <Card className="sticky top-8">
                <h3 className="text-xl font-bold text-white mb-4">Quote Summary</h3>
                <div className="space-y-2 text-gray-300">
                    <div className="flex justify-between"><span>Base Materials:</span> <span>{baseMaterialCost.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
                    <div className="flex justify-between"><span>Material Markup:</span> <span>{(materialWithMarkup - baseMaterialCost).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
                    <hr className="border-gray-600"/>
                    <div className="flex justify-between font-semibold"><span>Total Materials:</span> <span>{materialWithMarkup.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
                    <div className="h-4"></div>
                    <div className="flex justify-between"><span>Base Labor:</span> <span>{baseLaborCost.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
                    <div className="flex justify-between"><span>Labor Markup:</span> <span>{(laborWithMarkup - baseLaborCost).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
                     <hr className="border-gray-600"/>
                    <div className="flex justify-between font-semibold"><span>Total Labor:</span> <span>{laborWithMarkup.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
                    <div className="h-4"></div>
                     <hr className="border-gray-600"/>
                    <div className="flex justify-between"><span>Subtotal:</span> <span>{subtotal.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
                    <div className="flex justify-between"><span>Overhead & Profit:</span> <span>{overheadAndProfitAmount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
                    <div className="flex justify-between"><span>Contingency:</span> <span>{contingencyAmount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
                     <hr className="border-t-2 border-gray-500 my-2"/>
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
}> = (props) => {
    const { lineItems, bom, grandTotal, materialWithMarkup, laborWithMarkup } = useQuoteCalculator(props.ductwork, props.piping, props.pricing);
    
    const [view, setView] = useState<'quote' | 'bom'>('quote');
    
    const handlePrint = () => {
        window.print();
    };

    const Quote = () => (
        <div className="bg-white text-black p-8 font-sans printable-area">
             {/* Header */}
            <div className="text-center mb-8">
                <h1 className="text-3xl font-bold">GUARANTEED INSULATION</h1>
                <p>Athens, GA | glmoss@guaranteedinsulation.com</p>
                <h2 className="text-2xl font-semibold mt-4 border-b-2 border-black pb-2">MECHANICAL INSULATION PROPOSAL</h2>
            </div>

            {/* Project Info Table */}
            <div className="grid grid-cols-2 gap-x-8 text-sm mb-8">
                <div>
                    <p><strong>Project:</strong> {props.projectInfo.projectName}</p>
                    <p><strong>Location:</strong> {props.projectInfo.location}</p>
                </div>
                <div>
                    <p><strong>Customer:</strong> {props.projectInfo.customer}</p>
                    <p><strong>Date:</strong> {props.projectInfo.date}</p>
                    <p><strong>Quote #:</strong> {props.projectInfo.quoteNumber}</p>
                </div>
            </div>

            {/* Scope of Work */}
            <div className="mb-8">
                <h3 className="font-bold text-lg border-b border-gray-400 mb-2">SCOPE OF WORK</h3>
                <p className="text-sm">Furnish and install mechanical insulation per project specifications. All work to be performed in a neat and workmanlike manner.</p>
                {props.specAnalysis && <p className="text-sm mt-2">Systems include: {props.specAnalysis.summary}</p>}
            </div>

            {/* Pricing Table */}
             <table className="w-full text-sm mb-8">
                <thead className="bg-gray-200">
                    <tr>
                        <th className="text-left p-2">ITEM DESCRIPTION</th>
                        <th className="text-right p-2">QTY</th>
                        <th className="text-right p-2">UNIT</th>
                        <th className="text-right p-2">UNIT PRICE</th>
                        <th className="text-right p-2">TOTAL</th>
                    </tr>
                </thead>
                <tbody>
                    {lineItems.map((item, index) => (
                        <tr key={index} className="border-b">
                            <td className="p-2">{item.description} <span className="text-gray-600">{item.details}</span></td>
                            <td className="text-right p-2">{item.quantity.toFixed(2)}</td>
                            <td className="text-right p-2">{item.unit}</td>
                            <td className="text-right p-2">{item.unitPrice.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</td>
                            <td className="text-right p-2">{item.total.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
            
            {/* Summary Totals */}
            <div className="flex justify-end">
                <div className="w-1/2 text-sm">
                    <div className="flex justify-between p-2"><span className="font-semibold">MATERIAL SUBTOTAL:</span> <span>{materialWithMarkup.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
                    <div className="flex justify-between p-2"><span className="font-semibold">LABOR SUBTOTAL:</span> <span>{laborWithMarkup.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
                    <div className="flex justify-between bg-gray-200 p-2 text-lg font-bold"><span >TOTAL:</span> <span >{grandTotal.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span></div>
                </div>
            </div>
            
             {/* Fine Print */}
            <div className="text-xs text-gray-600 mt-8 space-y-4">
                <div>
                    <h4 className="font-bold">EXCLUSIONS:</h4>
                    <p>Scaffolding, staging, lifts, or access equipment; Insulation removal or demolition; Permits and inspections; Work outside normal business hours; Sales tax.</p>
                </div>
                <div>
                    <h4 className="font-bold">TERMS & CONDITIONS:</h4>
                    <p>Quote valid for 30 days. Payment terms: Net 30 days. Required schedule notice: 2 weeks.</p>
                </div>
            </div>
        </div>
    );
    
    const BillOfMaterials = () => (
      <div className="bg-white text-black p-8 font-sans printable-area">
        <h1 className="text-2xl font-bold mb-2">GUARANTEED INSULATION - MATERIAL ORDER</h1>
        <p><strong>Project:</strong> {props.projectInfo.projectName}</p>
        <p><strong>Quote #:</strong> {props.projectInfo.quoteNumber}</p>
        <p><strong>Date:</strong> {props.projectInfo.date}</p>
        
        <div className="mt-8 space-y-6">
          {Array.from(new Set(bom.map(item => item.category))).map(category => (
            <div key={category}>
              <h3 className="font-bold text-lg border-b border-gray-400 mb-2 uppercase">{category}</h3>
              <ul className="list-disc list-inside">
                {bom.filter(item => item.category === category).map((item, index) => (
                  <li key={index}><strong>{item.quantity}</strong> - {item.item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    );


    return (
        <Card>
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">Generated Documents</h2>
                <div className="flex gap-2 print:hidden">
                    <Button variant={view === 'quote' ? 'primary' : 'secondary'} onClick={() => setView('quote')}>Quote</Button>
                    <Button variant={view === 'bom' ? 'primary' : 'secondary'} onClick={() => setView('bom')}>Bill of Materials</Button>
                    <Button onClick={handlePrint}>Print</Button>
                </div>
            </div>
            <div className="bg-gray-700 p-2 rounded-lg">
                {view === 'quote' ? <Quote/> : <BillOfMaterials />}
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
