export enum Step {
  Documents,
  ProjectInfo,
  Takeoff,
  Review,
  Quote,
}

export interface ProjectInfo {
  projectName: string;
  location: string;
  customer: string;
  date: string;
  quoteNumber: string;
}

export interface TakeoffItem {
  id: string;
  size: string;
  length: number;
  fittings: number; // General purpose for elbows, tees, etc.
}

export interface QuoteData {
  projectInfo: ProjectInfo;
  ductwork: TakeoffItem[];
  piping: TakeoffItem[];
  pricing: PricingSettings;
  specAnalysis: string;
}

export interface PricingSettings {
  materialMarkup: number;
  laborMarkup: number;
  overheadProfit: number;
  contingency: number;
  laborAdjustment: number;
  laborRate: number;
}

export interface CalculatedLineItem {
  description: string;
  details: string;
  quantity: number;
  unit: string;
  unitPrice: number;
  total: number;
  type: 'material' | 'labor' | 'summary';
  category: string;
}

export interface BillOfMaterialsItem {
  category: string;
  item: string;
  quantity: string;
}

export interface GeminiSpecAnalysis {
  projectInfo?: {
    projectName?: string;
    location?: string;
    customer?: string;
    date?: string;
  };
  ductwork: { material: string; thickness: string; facing: string; };
  piping: { material: string; thickness: string; jacketing: string; };
  outdoor: { jacketing: string; requirements: string; };
  summary: string;
}

export interface GeminiDrawingAnalysis {
  ductwork: { size: string; length: number; fittings: number }[];
  piping: { size: string; length: number; fittings: number }[];
  scale: string;
  notes: string;
}
