// All prices are in USD, lengths in LF, areas in SF
// Based on "General Insulation Price Book - August 2024"

// DUCTWORK INSULATION (per LF, includes FSK facing)
// Derived from Manson FSK Duct Wrap ($0.42/sf) assuming avg 24x12 duct (6' perimeter)
// 6 SF/LF * $0.42/SF = $2.52/LF
export const DUCT_PRICING = {
  '1.5_fiberglass_fsk': 2.52, 
};

// PIPING INSULATION (per LF)
// Averaged from K-Flex Insul-Lock 1" wall for 2", 3", 4" pipe
// ($4.409 + $7.303 + $9.832) / 3 = $7.18
// Averaged from Alley-Kat ASJ 1.5" wall for 1", 2", 4", 6" pipe
// ($2.603 + $3.266 + $4.148 + $4.927) / 4 = $3.74
export const PIPE_PRICING = {
  '1.0_elastomeric': 7.18, 
  '1.5_fiberglass': 3.74, 
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
  fsk_tape_roll: 15.00,
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
  fsk_tape_roll_per_lf: 200, // 1 roll per 200 LF
};
