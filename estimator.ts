import { DUCT_PRICING, PIPE_PRICING } from './constants';
import type { ProjectInfo, TakeoffItem, GeminiSpecAnalysis } from './types';

export type InsulationSpec = {
    system_type: 'duct' | 'pipe' | 'equipment';
    size_range: string;
    thickness: number;
    material: string;
    facing?: string | null;
    special_requirements?: string[];
    location?: string;
};

export type MeasurementItem = {
    item_id: string;
    system_type: 'duct' | 'pipe' | 'unknown';
    size: string;
    length: number;
    location?: string;
    elevation_changes?: number;
    fittings?: { [k: string]: number };
    notes?: string[];
};

export type MaterialItem = {
    description: string;
    unit: string;
    quantity: number;
    unit_price: number;
    total_price: number;
    category: string;
};

// Very small, self-contained pricing engine ported from the Python example.
export class PricingEngine {
    prices: Record<string, number>;
    labor_rates: Record<string, number>;

    constructor(priceBook?: Record<string, number>) {
        this.prices = priceBook || {
            'fiberglass_1.5': DUCT_PRICING['1.5_fiberglass_fsk'],
            'elastomeric_1.0': PIPE_PRICING['1.0_elastomeric'],
            'mastic': 0.75,
            'aluminum_jacket': 8.5,
            'stainless_bands': 2.5,
            'fsk_facing': 1.25,
        } as Record<string, number>;

        this.labor_rates = {
            duct_insulation: 0.45,
            pipe_insulation: 0.35,
            jacketing: 0.25,
            mastic: 0.15,
        };
    }

    calculate_materials(measurements: MeasurementItem[], specs: InsulationSpec[]): MaterialItem[] {
        const materials: MaterialItem[] = [];

        for (const m of measurements) {
            const spec = specs.find(s => s.system_type === m.system_type) as InsulationSpec | undefined;
            if (!spec) continue;

            const quantity = m.length * (1 + (m.fittings ? ((m.fittings['elbow'] || 0) * 0.5 + (m.fittings['tee'] || 0) * 1.0) : 0));
            const price_key = `${spec.material}_${spec.thickness}`;
            const unit_price = (this.prices as any)[price_key] ?? (spec.system_type === 'duct' ? 5.0 : 4.0);

            materials.push({
                description: `${spec.material} ${spec.thickness}" - ${m.size}`,
                unit: 'LF',
                quantity,
                unit_price,
                total_price: quantity * unit_price,
                category: 'insulation',
            });

            if (spec.facing || (spec.special_requirements || []).includes('aluminum_jacket')) {
                const circumference = (parseFloat(m.size) || 12) / 12 * Math.PI; // crude
                const sf = m.length * circumference;
                const up = (spec.special_requirements || []).includes('aluminum_jacket') ? this.prices.aluminum_jacket : this.prices.fsk_facing;
                materials.push({ description: `${spec.facing ?? 'Facing'} - ${m.size}`, unit: 'SF', quantity: sf, unit_price: up, total_price: sf * up, category: 'jacket' });
            }

            if ((spec.special_requirements || []).includes('mastic_coating')) {
                const circumference = (parseFloat(m.size) || 12) / 12 * Math.PI;
                const sf = m.length * circumference;
                materials.push({ description: `Mastic Vapor Seal`, unit: 'SF', quantity: sf, unit_price: this.prices.mastic, total_price: sf * this.prices.mastic, category: 'mastic' });
            }
        }

        return materials;
    }

    calculate_labor(materials: MaterialItem[]): { hours: number; cost: number } {
        let total_hours = 0;
        for (const mat of materials) {
            if (mat.category === 'insulation') {
                total_hours += mat.quantity * this.labor_rates.duct_insulation; // crude assumption
            } else if (mat.category === 'jacket') {
                total_hours += mat.quantity * this.labor_rates.jacketing;
            } else if (mat.category === 'mastic') {
                total_hours += mat.quantity * this.labor_rates.mastic;
            }
        }
        total_hours *= 1.2; // overhead
        const labor_rate = 65;
        return { hours: total_hours, cost: total_hours * labor_rate };
    }
}

export class QuoteGenerator {
    generate_quote(projectName: string, measurements: MeasurementItem[], materials: MaterialItem[], laborHours: number, laborCost: number) {
        const material_total = materials.reduce((s, m) => s + m.total_price, 0);
        const subtotal = material_total + laborCost;
        const contingencyPercent = 10;
        const contingency = subtotal * (contingencyPercent / 100);
        const total = subtotal + contingency;

        const now = new Date();
        const quoteNumber = `Q${now.getFullYear()}${(now.getMonth() + 1).toString().padStart(2, '0')}${now.getDate().toString().padStart(2, '0')}-${now.getHours().toString().padStart(2, '0')}${now.getMinutes().toString().padStart(2, '0')}`;

        const quoteTextLines: string[] = [];
        quoteTextLines.push('='.repeat(60));
        quoteTextLines.push('HVAC INSULATION QUOTE');
        quoteTextLines.push('='.repeat(60));
        quoteTextLines.push(`Project: ${projectName}`);
        quoteTextLines.push(`Quote Number: ${quoteNumber}`);
        quoteTextLines.push(`Date: ${now.toISOString().split('T')[0]}`);
        quoteTextLines.push('');
        quoteTextLines.push('MATERIALS');
        quoteTextLines.push('-'.repeat(60));
        quoteTextLines.push(`Description | Qty | Unit | Price`);
        for (const m of materials) {
            quoteTextLines.push(`${m.description} | ${m.quantity.toFixed(2)} | ${m.unit} | $${m.total_price.toFixed(2)}`);
        }
        quoteTextLines.push('');
        quoteTextLines.push(`Material Subtotal: $${material_total.toFixed(2)}`);
        quoteTextLines.push(`Labor (${Math.round(laborHours)} hrs @ $65/hr): $${laborCost.toFixed(2)}`);
        quoteTextLines.push(`Subtotal: $${subtotal.toFixed(2)}`);
        quoteTextLines.push(`Contingency (${contingencyPercent}%): $${contingency.toFixed(2)}`);
        quoteTextLines.push('='.repeat(60));
        quoteTextLines.push(`TOTAL: $${total.toFixed(2)}`);

        const materialList = materials.reduce<Record<string, { unit: string; quantity: number }>>((acc, m) => {
            const key = `${m.description}|${m.unit}`;
            if (!acc[key]) acc[key] = { unit: m.unit, quantity: 0 };
            acc[key].quantity += m.quantity;
            return acc;
        }, {});

        const materialListLines: string[] = ['MATERIAL LIST', '-'.repeat(60)];
        for (const [k, v] of Object.entries(materialList)) {
            const desc = k.split('|')[0];
            materialListLines.push(`${desc} | ${v.quantity.toFixed(2)} ${v.unit}`);
        }

        return { quoteNumber, quoteText: quoteTextLines.join('\n'), materialListText: materialListLines.join('\n'), total };
    }
}

// Small helper to generate the demo used in the Python main()
export function generateDemoQuote() {
    const specs: InsulationSpec[] = [
        { system_type: 'duct', size_range: 'all', thickness: 1.5, material: 'fiberglass', facing: 'FSK', location: 'indoor' },
        { system_type: 'pipe', size_range: '1-2 inch', thickness: 1.0, material: 'elastomeric', location: 'outdoor', special_requirements: ['aluminum_jacket', 'stainless_bands'] },
    ];

    const manual_measurements: MeasurementItem[] = [
        { item_id: 'DUCT-001', system_type: 'duct', size: '18x12', length: 125.5, location: 'Main corridor', fittings: { elbow: 3, tee: 1 } },
        { item_id: 'PIPE-001', system_type: 'pipe', size: '2"', length: 85.0, location: 'Exterior wall', elevation_changes: 2, fittings: { elbow: 4 } },
    ];

    const engine = new PricingEngine();
    const materials = engine.calculate_materials(manual_measurements, specs);
    const lab = engine.calculate_labor(materials);
    const generator = new QuoteGenerator();
    return generator.generate_quote('Example Commercial Building', manual_measurements, materials, lab.hours, lab.cost);
}

export type GeneratedQuote = {
    quoteNumber: string;
    quoteText: string;
    materialListText: string;
    total: number;
    materials: MaterialItem[];
    laborHours: number;
    laborCost: number;
};

export function generateQuoteFromUI(
    projectInfo: ProjectInfo,
    ductwork: TakeoffItem[],
    piping: TakeoffItem[],
    specAnalysis?: GeminiSpecAnalysis | null
): GeneratedQuote {
    // Build specs from specAnalysis (fallback to defaults)
    const specs: InsulationSpec[] = [];

    if (specAnalysis) {
        specAnalysis.ductworkSystems.forEach(d => {
            specs.push({
                system_type: 'duct',
                size_range: d.sizeRange || 'all',
                thickness: parseFloat(d.thickness as unknown as string) || 1.5,
                material: (d.material || 'fiberglass').toLowerCase(),
                facing: d.facing || null,
                special_requirements: [],
                location: d.location || 'indoor',
            });
        });
        specAnalysis.pipingSystems.forEach(p => {
            specs.push({
                system_type: 'pipe',
                size_range: p.sizeRange || 'all',
                thickness: parseFloat(p.thickness as unknown as string) || 1.0,
                material: (p.material || 'elastomeric').toLowerCase(),
                facing: p.jacket || null,
                special_requirements: [],
                location: p.location || 'indoor',
            });
        });
    }

    // If no specs found, add defaults
    if (specs.length === 0) {
        specs.push({ system_type: 'duct', size_range: 'all', thickness: 1.5, material: 'fiberglass', facing: 'FSK', location: 'indoor' });
        specs.push({ system_type: 'pipe', size_range: 'all', thickness: 1.0, material: 'elastomeric', location: 'indoor' });
    }

    // Convert takeoff items to measurement items
    const measurements: MeasurementItem[] = [];
    ductwork.forEach(d => {
        measurements.push({
            item_id: d.id,
            system_type: 'duct',
            size: d.size,
            length: d.length,
            location: projectInfo.location,
            fittings: { elbow: d.fittings },
        });
    });
    piping.forEach(p => {
        measurements.push({
            item_id: p.id,
            system_type: 'pipe',
            size: p.size,
            length: p.length,
            location: projectInfo.location,
            fittings: { elbow: p.fittings },
        });
    });

    const engine = new PricingEngine();
    const materials = engine.calculate_materials(measurements, specs);
    const lab = engine.calculate_labor(materials);

    const generator = new QuoteGenerator();
    const generated = generator.generate_quote(projectInfo.projectName, measurements, materials, lab.hours, lab.cost);

    return {
        quoteNumber: generated.quoteNumber,
        quoteText: generated.quoteText,
        materialListText: generated.materialListText,
        total: generated.total,
        materials,
        laborHours: lab.hours,
        laborCost: lab.cost,
    };
}
