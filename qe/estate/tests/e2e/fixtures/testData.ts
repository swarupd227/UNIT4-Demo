/**
 * Seeded test data. The test environment loads the same data on every reset,
 * so these values are fixed. Period: October 2026.
 */
export const PERIOD_END = '2026-10-31';

export const projects = {
  haldenRollout: 'P-1001 Halden ERP rollout',
  haldenData: 'P-1002 Halden data platform',
  haldenSupport: 'P-1003 Halden support retainer',
  brightwaterSurvey: 'P-1010 Brightwater asset survey',
  brightwaterStudy: 'P-1011 Brightwater network study',
  vestfold: 'P-1030 Vestfold fleet optimisation',
  meridian: 'P-1040 Meridian clinical scheduling',
  atlas: 'P-1050 Atlas store analytics',
  lumo: 'P-1060 Lumo brand system',
  pacificTracking: 'P-1080 Pacific freight tracking',
  pacificCustoms: 'P-1081 Pacific customs integration',
  ostra: 'P-1120 Ostra warehouse WMS',
};

export const customers = {
  halden: 'C100',
};

export const invoices = {
  /** Lumo, September 2026: 2 lines, 2,986.90 EUR, line 2 already credited by CN-000013. */
  lumoSeptember: 'INV-000291',
  /** Any final invoice will do for the lock check. */
  final: 'INV-000280',
};
