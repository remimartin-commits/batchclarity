/**
 * mock-api.ts — Fake backend for parallel frontend development.
 *
 * PURPOSE: Allows frontend + GMP logic to be built and tested
 *          before the backend API is fully wired. When the real
 *          API is ready, swap imports: mock-api → api.ts. Zero rewrite.
 *
 * USAGE:   Set VITE_USE_MOCK=true in .env.development
 *          OR import directly from this file during local dev.
 *
 * RULE:    Mock data must be realistic (real GMP terminology, real
 *          field values). Fake data destroys the value of this file.
 */

// ── TYPES ───────────────────────────────────────────────────────────────────

export type CAPAStatus =
  | 'OPEN'
  | 'INVESTIGATION'
  | 'ACTION_PLAN_APPROVED'
  | 'IN_PROGRESS'
  | 'EFFECTIVENESS_CHECK'
  | 'CLOSED';

export type GMPClassification = 'Critical' | 'Major' | 'Minor' | 'Observation';
export type SourceType =
  | 'Deviation'
  | 'Audit Finding'
  | 'Customer Complaint'
  | 'OOS'
  | 'OOT'
  | 'Self-Inspection'
  | 'Risk Assessment'
  | 'Supplier Issue'
  | 'Other';

export type DeviationStatus = 'OPEN' | 'UNDER_INVESTIGATION' | 'PENDING_APPROVAL' | 'CLOSED';
export type DeviationType =
  | 'Process'
  | 'Equipment'
  | 'Environmental'
  | 'Material'
  | 'Documentation'
  | 'Personnel'
  | 'Laboratory'
  | 'Other';

export type BatchStatus =
  | 'SCHEDULED'
  | 'IN_PROGRESS'
  | 'PENDING_QA_REVIEW'
  | 'RELEASED'
  | 'ARCHIVED';

export type EquipmentStatus =
  | 'ACTIVE'
  | 'OUT_OF_CALIBRATION'
  | 'UNDER_MAINTENANCE'
  | 'DECOMMISSIONED'
  | 'QUARANTINE';

export interface User {
  id: string;
  username: string;
  full_name: string;
  email: string;
  role: string;
  site_id: string;
}

export interface CAPA {
  id: string;
  capa_number: string;
  title: string;
  description: string;
  status: CAPAStatus;
  source_type: SourceType;
  gmp_classification: GMPClassification;
  product_affected: string;
  batch_lot_number: string | null;
  root_cause_category: string | null;
  root_cause_description: string | null;
  regulatory_reporting_required: boolean;
  initiator_id: string;
  initiator_name: string;
  owner_id: string;
  owner_name: string;
  site_id: string;
  target_date: string;
  close_date: string | null;
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
}

export interface Deviation {
  id: string;
  deviation_number: string;
  title: string;
  description: string;
  status: DeviationStatus;
  deviation_type: DeviationType;
  gmp_impact_classification: GMPClassification;
  product_affected: string;
  batches_affected: string[];
  immediate_containment: string;
  potential_patient_impact: boolean;
  root_cause: string | null;
  linked_capa_id: string | null;
  regulatory_notification_required: boolean;
  initiator_name: string;
  site_id: string;
  target_close_date: string;
  is_overdue: boolean;
  created_at: string;
}

export interface BatchRecord {
  id: string;
  batch_number: string;
  product_name: string;
  product_code: string;
  mbr_id: string;
  mbr_version: string;
  status: BatchStatus;
  scheduled_start: string;
  actual_start: string | null;
  actual_end: string | null;
  theoretical_yield_kg: number;
  actual_yield_kg: number | null;
  yield_pct: number | null;
  steps_total: number;
  steps_completed: number;
  has_open_deviation: boolean;
  operator_name: string;
  site_id: string;
  created_at: string;
}

export interface Equipment {
  id: string;
  equipment_number: string;
  name: string;
  manufacturer: string;
  model: string;
  serial_number: string;
  location: string;
  status: EquipmentStatus;
  last_calibration_date: string | null;
  next_calibration_due: string | null;
  calibration_interval_days: number;
  is_calibration_overdue: boolean;
  qualification_status: 'QUALIFIED' | 'NOT_QUALIFIED' | 'QUALIFICATION_EXPIRED';
  site_id: string;
  created_at: string;
}

export interface Sample {
  id: string;
  sample_number: string;
  product_name: string;
  batch_number: string;
  sample_type: string;
  status: 'PENDING' | 'IN_TESTING' | 'PASSED' | 'FAILED' | 'OOS' | 'OOT';
  sampled_at: string;
  tested_at: string | null;
  analyst_name: string | null;
  is_oos: boolean;
  is_oot: boolean;
  site_id: string;
  created_at: string;
}

export interface DashboardSummary {
  open_capas: number;
  overdue_capas: number;
  open_deviations: number;
  overdue_deviations: number;
  pending_change_controls: number;
  calibrations_due_30_days: number;
  calibrations_overdue: number;
  open_oos_investigations: number;
  documents_expiring_60_days: number;
  training_overdue: number;
  pending_my_signatures: number;
  pending_my_actions: MyAction[];
}

export interface MyAction {
  id: string;
  type: 'e-signature' | 'review' | 'approve' | 'training';
  title: string;
  due_date: string;
  module: string;
  record_id: string;
}

// ── MOCK DATA ────────────────────────────────────────────────────────────────

export const mockCurrentUser: User = {
  id: 'usr-001',
  username: 'admin',
  full_name: 'Rémi Martin',
  email: 'remi.martin@batchclarity.ch',
  role: 'QA Manager',
  site_id: 'site-001',
};

export const mockCAPAs: CAPA[] = [
  {
    id: 'capa-001',
    capa_number: 'CAPA-2026-001',
    title: 'Recurring temperature excursion in ambient storage area B',
    description:
      'Three temperature excursions recorded in storage area B during Q1 2026. Root cause appears to be HVAC unit failure pattern. Immediate containment in place.',
    status: 'IN_PROGRESS',
    source_type: 'Deviation',
    gmp_classification: 'Major',
    product_affected: 'mRNA Vaccine DS (all batches stored in Area B)',
    batch_lot_number: 'DS-2026-004, DS-2026-005',
    root_cause_category: 'Equipment',
    root_cause_description:
      'HVAC Unit HVAC-B-02 bearing wear causing intermittent failure. Preventive maintenance interval insufficient for ambient conditions during winter months.',
    regulatory_reporting_required: false,
    initiator_id: 'usr-002',
    initiator_name: 'Sophie Lefebvre',
    owner_id: 'usr-001',
    owner_name: 'Rémi Martin',
    site_id: 'site-001',
    target_date: '2026-05-15',
    close_date: null,
    is_overdue: false,
    created_at: '2026-03-12T09:00:00Z',
    updated_at: '2026-04-10T14:30:00Z',
  },
  {
    id: 'capa-002',
    capa_number: 'CAPA-2026-002',
    title: 'OOS result for endotoxin testing — Batch LT-2026-011',
    description:
      'Endotoxin result 3.2 EU/mL against specification of ≤1.0 EU/mL. Phase 1 investigation confirmed no assignable lab error. Phase 2 manufacturing investigation in progress.',
    status: 'EFFECTIVENESS_CHECK',
    source_type: 'OOS',
    gmp_classification: 'Critical',
    product_affected: 'Lipid Nanoparticle Formulation LT-2026-011',
    batch_lot_number: 'LT-2026-011',
    root_cause_category: 'Material',
    root_cause_description:
      'Lipid component from Lot LIP-2026-003 found to have elevated endotoxin content at supplier. Supplier QC failure not detected at incoming inspection due to sampling limitation.',
    regulatory_reporting_required: true,
    initiator_id: 'usr-003',
    initiator_name: 'Dr. James Park',
    owner_id: 'usr-001',
    owner_name: 'Rémi Martin',
    site_id: 'site-001',
    target_date: '2026-04-01',
    close_date: null,
    is_overdue: true,
    created_at: '2026-02-20T11:15:00Z',
    updated_at: '2026-04-18T09:45:00Z',
  },
  {
    id: 'capa-003',
    capa_number: 'CAPA-2026-003',
    title: 'Operator training gap identified during internal audit — MES step execution',
    description:
      'Internal audit finding: 3 operators did not correctly follow step-by-step EBR execution procedure. Steps were signed retrospectively, violating ALCOA contemporaneous principle.',
    status: 'OPEN',
    source_type: 'Audit Finding',
    gmp_classification: 'Major',
    product_affected: 'All production batches',
    batch_lot_number: null,
    root_cause_category: null,
    root_cause_description: null,
    regulatory_reporting_required: false,
    initiator_id: 'usr-004',
    initiator_name: 'Maria Santos',
    owner_id: 'usr-002',
    owner_name: 'Sophie Lefebvre',
    site_id: 'site-001',
    target_date: '2026-06-30',
    close_date: null,
    is_overdue: false,
    created_at: '2026-04-15T08:00:00Z',
    updated_at: '2026-04-15T08:00:00Z',
  },
];

export const mockDeviations: Deviation[] = [
  {
    id: 'dev-001',
    deviation_number: 'DEV-2026-007',
    title: 'Temperature excursion: ambient storage Area B, 2026-03-10',
    description: 'Storage area temperature reached 28°C (limit 25°C) for 4 hours between 02:00 and 06:00.',
    status: 'PENDING_APPROVAL',
    deviation_type: 'Environmental',
    gmp_impact_classification: 'Major',
    product_affected: 'mRNA Vaccine DS',
    batches_affected: ['DS-2026-004', 'DS-2026-005'],
    immediate_containment: 'Batches quarantined pending investigation. HVAC engineer called. Backup monitoring confirmed other areas within limits.',
    potential_patient_impact: false,
    root_cause: 'HVAC bearing wear — see CAPA-2026-001',
    linked_capa_id: 'capa-001',
    regulatory_notification_required: false,
    initiator_name: 'Sophie Lefebvre',
    site_id: 'site-001',
    target_close_date: '2026-05-01',
    is_overdue: false,
    created_at: '2026-03-10T08:30:00Z',
  },
];

export const mockBatchRecords: BatchRecord[] = [
  {
    id: 'batch-001',
    batch_number: 'DS-2026-006',
    product_name: 'mRNA Vaccine Drug Substance',
    product_code: 'MRNA-DS-001',
    mbr_id: 'mbr-001',
    mbr_version: 'v3.2',
    status: 'IN_PROGRESS',
    scheduled_start: '2026-04-23T06:00:00Z',
    actual_start: '2026-04-23T06:15:00Z',
    actual_end: null,
    theoretical_yield_kg: 2.5,
    actual_yield_kg: null,
    yield_pct: null,
    steps_total: 24,
    steps_completed: 14,
    has_open_deviation: false,
    operator_name: 'Thomas Müller',
    site_id: 'site-001',
    created_at: '2026-04-22T16:00:00Z',
  },
  {
    id: 'batch-002',
    batch_number: 'LT-2026-012',
    product_name: 'Lipid Nanoparticle Formulation',
    product_code: 'LNP-001',
    mbr_id: 'mbr-002',
    mbr_version: 'v1.5',
    status: 'PENDING_QA_REVIEW',
    scheduled_start: '2026-04-20T07:00:00Z',
    actual_start: '2026-04-20T07:10:00Z',
    actual_end: '2026-04-21T18:45:00Z',
    theoretical_yield_kg: 1.8,
    actual_yield_kg: 1.74,
    yield_pct: 96.7,
    steps_total: 18,
    steps_completed: 18,
    has_open_deviation: false,
    operator_name: 'Anna Kowalski',
    site_id: 'site-001',
    created_at: '2026-04-19T14:00:00Z',
  },
];

export const mockEquipment: Equipment[] = [
  {
    id: 'eq-001',
    equipment_number: 'BIOR-001',
    name: 'Bioreactor A — 200L upstream',
    manufacturer: 'Sartorius',
    model: 'BIOSTAT STR 200L',
    serial_number: 'SAR-2024-0831',
    location: 'Suite 3A — Upstream Processing',
    status: 'ACTIVE',
    last_calibration_date: '2026-01-15',
    next_calibration_due: '2026-07-15',
    calibration_interval_days: 180,
    is_calibration_overdue: false,
    qualification_status: 'QUALIFIED',
    site_id: 'site-001',
    created_at: '2024-08-01T00:00:00Z',
  },
  {
    id: 'eq-002',
    equipment_number: 'HVAC-B-02',
    name: 'HVAC Unit — Ambient Storage Area B',
    manufacturer: 'Carrier',
    model: 'AHU-45',
    serial_number: 'CAR-2022-1104',
    location: 'Storage Building B',
    status: 'UNDER_MAINTENANCE',
    last_calibration_date: '2025-10-01',
    next_calibration_due: '2026-04-01',
    calibration_interval_days: 180,
    is_calibration_overdue: true,
    qualification_status: 'QUALIFIED',
    site_id: 'site-001',
    created_at: '2022-11-01T00:00:00Z',
  },
];

export const mockSamples: Sample[] = [
  {
    id: 'smp-001',
    sample_number: 'SMP-2026-0421',
    product_name: 'mRNA Vaccine DS',
    batch_number: 'DS-2026-006',
    sample_type: 'In-Process',
    status: 'IN_TESTING',
    sampled_at: '2026-04-23T10:00:00Z',
    tested_at: null,
    analyst_name: 'Dr. James Park',
    is_oos: false,
    is_oot: false,
    site_id: 'site-001',
    created_at: '2026-04-23T10:05:00Z',
  },
  {
    id: 'smp-002',
    sample_number: 'SMP-2026-0398',
    product_name: 'Lipid Nanoparticle Formulation',
    batch_number: 'LT-2026-011',
    sample_type: 'Release',
    status: 'OOS',
    sampled_at: '2026-02-18T14:00:00Z',
    tested_at: '2026-02-19T11:30:00Z',
    analyst_name: 'Dr. James Park',
    is_oos: true,
    is_oot: false,
    site_id: 'site-001',
    created_at: '2026-02-18T14:05:00Z',
  },
];

export const mockDashboardSummary: DashboardSummary = {
  open_capas: 3,
  overdue_capas: 1,
  open_deviations: 2,
  overdue_deviations: 0,
  pending_change_controls: 1,
  calibrations_due_30_days: 2,
  calibrations_overdue: 1,
  open_oos_investigations: 1,
  documents_expiring_60_days: 3,
  training_overdue: 5,
  pending_my_signatures: 2,
  pending_my_actions: [
    {
      id: 'action-001',
      type: 'e-signature',
      title: 'Approve CAPA-2026-001 Action Plan',
      due_date: '2026-04-25',
      module: 'QMS',
      record_id: 'capa-001',
    },
    {
      id: 'action-002',
      type: 'review',
      title: 'QA Review — Batch LT-2026-012 pending release',
      due_date: '2026-04-24',
      module: 'MES',
      record_id: 'batch-002',
    },
  ],
};

// ── API FUNCTIONS ────────────────────────────────────────────────────────────

const delay = (ms = 200) => new Promise(resolve => setTimeout(resolve, ms));

// -- Auth --
export async function mockLogin(username: string, _password: string): Promise<User> {
  await delay(300);
  if (username === 'admin') return mockCurrentUser;
  throw new Error('Invalid credentials');
}

export async function mockGetCurrentUser(): Promise<User> {
  await delay(100);
  return mockCurrentUser;
}

// -- Dashboard --
export async function mockGetDashboardSummary(): Promise<DashboardSummary> {
  await delay(200);
  return mockDashboardSummary;
}

// -- CAPAs --
export async function mockGetCAPAs(): Promise<{ items: CAPA[]; total: number }> {
  await delay(200);
  return { items: mockCAPAs, total: mockCAPAs.length };
}

export async function mockGetCAPAById(id: string): Promise<CAPA> {
  await delay(150);
  const capa = mockCAPAs.find(c => c.id === id);
  if (!capa) throw new Error(`CAPA ${id} not found`);
  return capa;
}

export async function mockCreateCAPA(data: Partial<CAPA>): Promise<CAPA> {
  await delay(400);
  const newCAPA: CAPA = {
    id: `capa-${Date.now()}`,
    capa_number: `CAPA-2026-00${mockCAPAs.length + 1}`,
    status: 'OPEN',
    is_overdue: false,
    close_date: null,
    root_cause_category: null,
    root_cause_description: null,
    batch_lot_number: null,
    regulatory_reporting_required: false,
    initiator_id: mockCurrentUser.id,
    initiator_name: mockCurrentUser.full_name,
    site_id: mockCurrentUser.site_id,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...data,
  } as CAPA;
  mockCAPAs.push(newCAPA);
  return newCAPA;
}

export async function mockCloseCAPA(
  id: string,
  _username: string,
  _password: string,
  _reason: string
): Promise<CAPA> {
  await delay(500);
  const capa = mockCAPAs.find(c => c.id === id);
  if (!capa) throw new Error(`CAPA ${id} not found`);
  capa.status = 'CLOSED';
  capa.close_date = new Date().toISOString();
  capa.updated_at = new Date().toISOString();
  return capa;
}

// -- Deviations --
export async function mockGetDeviations(): Promise<{ items: Deviation[]; total: number }> {
  await delay(200);
  return { items: mockDeviations, total: mockDeviations.length };
}

// -- Batch Records --
export async function mockGetBatchRecords(): Promise<{ items: BatchRecord[]; total: number }> {
  await delay(200);
  return { items: mockBatchRecords, total: mockBatchRecords.length };
}

// -- Equipment --
export async function mockGetEquipment(): Promise<{ items: Equipment[]; total: number }> {
  await delay(200);
  return { items: mockEquipment, total: mockEquipment.length };
}

// -- LIMS Samples --
export async function mockGetSamples(): Promise<{ items: Sample[]; total: number }> {
  await delay(200);
  return { items: mockSamples, total: mockSamples.length };
}

// ── SWITCH: real vs mock ─────────────────────────────────────────────────────
// Usage in components:
//
//   import { mockGetCAPAs } from '@/lib/mock-api'   // mock mode
//   import { getCAPAs } from '@/lib/api'             // real mode
//
// Or via env flag — see vite.config.ts VITE_USE_MOCK
