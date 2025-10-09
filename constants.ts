
// All prices are in USD, lengths in LF, areas in SF
// Based on "October 2025 - Athens, GA Market"

// DUCTWORK INSULATION (per LF, includes FSK facing)
export const DUCT_PRICING = {
  '1.5_fiberglass_fsk': 5.00, // Average of $4.75-5.25
  '2.0_fiberglass_fsk': 6.13, // Average of $5.75-6.50
};

// PIPING INSULATION (per LF)
export const PIPE_PRICING = {
  '1.0_elastomeric': 4.50, // Average of $4.25-4.75
  '1.5_fiberglass': 4.88, // Average of $4.50-5.25
};

// JACKETING (per SF)
export const JACKETING_PRICING = {
  'aluminum_0.016': 9.00,
};

// ACCESSORIES
export const ACCESSORY_PRICING = {
  mastic_gallon: 50.00,
  adhesive_gallon: 40.00,
  stainless_bands_each: 2.50,
};

// LABOR PRODUCTION RATES
export const LABOR_RATES = {
  duct_rectangular_medium: 22.5, // LF/hour (20-25)
  duct_fitting: 1, // hours/fitting
  pipe_medium: 17.5, // LF/hour (15-20)
  pipe_fitting: 0.6, // hours/fitting (30-45 mins)
  jacketing_aluminum: 45, // SF/hour
  mastic: 70, // SF/hour
};

// TAKEOFF WASTE & FITTING FACTORS
export const TAKEOFF_FACTORS = {
  duct_straight_waste: 1.10, // 10%
  duct_elbow_waste_multiplier: 0.5,
  pipe_elbow_equivalent_lf: 1.5,
  pipe_tee_equivalent_lf: 2.0,
  surface_area_overlap: 1.10, // 10%
};

// ACCESSORY COVERAGE
export const ACCESSORY_COVERAGE = {
  adhesive_gallon_per_lf: 125, // 1 gallon per 100-150 LF
  mastic_gallon_per_sf: 175, // 1 gallon per 150-200 SF
  bands_per_lf_outdoor: 1, // 1 per 12"
};
