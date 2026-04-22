// GMP Platform — TypeScript Type Definitions
// All types mirror backend Pydantic schemas (app/modules/*/schemas.py)

// ── Auth ──────────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  site_id?: string;
  must_change_password?: boolean;
  roles: Role[];
}

export interface Role {
  id: string;
  name: string;
  code: string;
  description: string;
  is_system_role: boolean;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// ── QMS ───────────────────────────────────────────────────────────────────────
export type RiskLevel = "low" | "minor" | "major" | "critical";
export type CAPAStatus =
  | "draft"
  | "under_review"
  | "approved"
  | "wip"
  | "effectiveness_check"
  | "closed"
  | "cancelled";

export interface CAPAAction {
  id: string;
  capa_id: string;
  sequence_number: number;
  description: string;
  assigned_to_id?: string;
  due_date?: string;
  completed_at?: string;
  is_frozen: boolean;
  freeze_reason?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CAPA {
  id: string;
  capa_number: string;
  title: string;
  description: string;
  source_type: string;
  source_record_id?: string;
  risk_level: RiskLevel;
  current_status: CAPAStatus;
  owner_id: string;
  site_id: string;
  due_date?: string;
  root_cause?: string;
  effectiveness_criteria?: string;
  effectiveness_check_date?: string;
  closed_at?: string;
  created_at: string;
  updated_at: string;
  actions: CAPAAction[];
}

export interface Deviation {
  id: string;
  deviation_number: string;
  title: string;
  description: string;
  severity: "minor" | "major" | "critical";
  status: string;
  detected_by_id: string;
  owner_id: string;
  site_id: string;
  detection_date: string;
  immediate_action?: string;
  root_cause?: string;
  linked_capa_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ChangeControl {
  id: string;
  change_number: string;
  title: string;
  description: string;
  change_type: string;
  change_category: "minor" | "major" | "critical";
  regulatory_impact: boolean;
  validation_required: boolean;
  status: string;
  current_status: string;
  owner_id: string;
  site_id: string;
  implementation_date?: string;
  created_at: string;
  updated_at: string;
}

// ── MES ───────────────────────────────────────────────────────────────────────
export interface Product {
  id: string;
  name: string;
  code: string;
  description?: string;
  product_type: string;
  dosage_form?: string;
  strength?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MBRStep {
  id: string;
  mbr_id: string;
  step_number: number;
  title: string;
  instructions: string;
  is_critical: boolean;
  requires_signature: boolean;
  expected_result?: string;
}

export interface MasterBatchRecord {
  id: string;
  mbr_number: string;
  product_id: string;
  version: string;
  status: string;
  batch_size: number;
  batch_size_unit: string;
  yield_min?: number;
  yield_max?: number;
  created_at: string;
  updated_at: string;
  steps: MBRStep[];
}

export interface BatchRecordStep {
  id: string;
  batch_record_id: string;
  mbr_step_id: string;
  step_number: number;
  title: string;
  instructions: string;
  is_critical: boolean;
  performed_at?: string;
  performed_by_id?: string;
  result_text?: string;
  result_numeric?: number;
  passed?: boolean;
}

export interface BatchRecord {
  id: string;
  batch_number: string;
  mbr_id: string;
  product_id?: string;
  product_name?: string;
  status: string;
  batch_size: number;
  batch_size_unit: string;
  started_at?: string;
  completed_at?: string;
  released_at?: string;
  release_decision?: string;
  reject_reason?: string;
  released_by_id?: string;
  created_at: string;
  updated_at: string;
  steps: BatchRecordStep[];
}

// ── Equipment ─────────────────────────────────────────────────────────────────
export interface Equipment {
  id: string;
  equipment_number: string;
  name: string;
  description?: string;
  equipment_type: string;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  location?: string;
  status: string;
  calibration_required: boolean;
  calibration_interval_months?: number;
  calibration_due_date?: string;
  qualification_status?: string;
  site_id?: string;
  created_at: string;
  updated_at: string;
}

export interface CalibrationRecord {
  id: string;
  equipment_id: string;
  calibration_number: string;
  calibration_date: string;
  next_due_date: string;
  performed_by: string;
  provider?: string;
  calibration_result: string;
  certificate_number?: string;
  passed: boolean;
  out_of_tolerance: boolean;
  created_at: string;
}

export interface QualificationRecord {
  id: string;
  equipment_id: string;
  qualification_number: string;
  qualification_type: "IQ" | "OQ" | "PQ" | "DQ" | "PV";
  status: string;
  protocol_ref?: string;
  started_at: string;
  completed_at?: string;
  approved_at?: string;
  approved_by_id?: string;
  created_at: string;
}

export interface MaintenanceRecord {
  id: string;
  equipment_id: string;
  maintenance_number: string;
  maintenance_type: string;
  performed_at: string;
  performed_by: string;
  description: string;
  parts_replaced?: string;
  next_due_date?: string;
  created_at: string;
}

// ── Training ──────────────────────────────────────────────────────────────────
export interface CurriculumItem {
  id: string;
  curriculum_id: string;
  sequence_number: number;
  document_number?: string;
  title: string;
  description?: string;
  requires_read_and_understood: boolean;
}

export interface TrainingCurriculum {
  id: string;
  name: string;
  code: string;
  description?: string;
  is_mandatory: boolean;
  retraining_interval_months?: number;
  target_roles: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  items: CurriculumItem[];
}

export interface TrainingCompletion {
  id: string;
  assignment_id: string;
  completion_method: string;
  completed_at: string;
  score?: number;
  passed: boolean;
  signature_id?: string;
}

export type AssignmentStatus = "assigned" | "in_progress" | "completed" | "overdue" | "expired";

export interface TrainingAssignment {
  id: string;
  curriculum_id: string;
  curriculum?: TrainingCurriculum;
  user_id: string;
  due_date?: string;
  status: AssignmentStatus;
  assigned_by_id?: string;
  created_at: string;
  updated_at: string;
  completion?: TrainingCompletion;
}

// ── Documents ─────────────────────────────────────────────────────────────────
export interface DocumentType {
  id: string;
  name: string;
  prefix: string;
  review_period_months?: number;
}

export interface DocumentVersion {
  id: string;
  document_id: string;
  version_number: string;
  status: string;
  file_path?: string;
  file_hash?: string;
  change_summary?: string;
  authored_by_id?: string;
  reviewed_by_id?: string;
  approved_by_id?: string;
  effective_date?: string;
  next_review_date?: string;
  created_at: string;
}

export interface Document {
  id: string;
  document_number: string;
  title: string;
  document_type_id: string;
  current_version_id?: string;
  current_version?: DocumentVersion;
  created_at: string;
  updated_at: string;
}

// ── Environmental Monitoring ──────────────────────────────────────────────────
export type GmpGrade = "A" | "B" | "C" | "D";
export type EMStatus = "within_limits" | "alert" | "action" | "oot" | "oos";

export interface AlertLimit {
  id: string;
  location_id: string;
  parameter: string;
  unit: string;
  alert_limit?: number;
  action_limit?: number;
  method?: string;
  is_active: boolean;
}

export interface MonitoringLocation {
  id: string;
  code: string;
  name: string;
  gmp_grade: GmpGrade;
  room?: string;
  building?: string;
  area_classification?: string;
  is_active: boolean;
  created_at: string;
  alert_limits: AlertLimit[];
}

export interface MonitoringResult {
  id: string;
  result_number: string;
  location_id: string;
  location?: MonitoringLocation;
  parameter: string;
  result_value: number;
  unit: string;
  status: EMStatus;
  result_entered_at: string;
  sampled_by_id: string;
  sampling_date?: string;
  comments?: string;
  created_at: string;
}

// ── LIMS ──────────────────────────────────────────────────────────────────────
export interface TestMethod {
  id: string;
  name: string;
  code: string;
  description?: string;
  method_type: string;
  is_compendial: boolean;
  is_active: boolean;
}

export interface SpecificationTest {
  id: string;
  specification_id: string;
  test_method_id?: string;
  test_name: string;
  lower_limit?: number;
  upper_limit?: number;
  acceptance_criteria: string;
  unit?: string;
  is_mandatory: boolean;
}

export interface Specification {
  id: string;
  name: string;
  code: string;
  product_id?: string;
  version: string;
  status: string;
  created_at: string;
  tests: SpecificationTest[];
}

export interface TestResult {
  id: string;
  sample_id: string;
  specification_test_id?: string;
  test_name: string;
  result_value?: number;
  result_text?: string;
  unit?: string;
  is_oos: boolean;
  is_oot: boolean;
  status: string;
  decision?: string;
  analyst_id: string;
  created_at: string;
}

export interface OOSInvestigation {
  id: string;
  test_result_id: string;
  phase: 1 | 2;
  status: string;
  phase1_conclusion?: string;
  phase2_conclusion?: string;
  root_cause?: string;
  opened_at: string;
  closed_at?: string;
  created_at: string;
}

export interface Sample {
  id: string;
  sample_number: string;
  sample_type: string;
  description?: string;
  batch_number?: string;
  product_id?: string;
  specification_id?: string;
  status: string;
  received_at?: string;
  required_by?: string;
  created_at: string;
  updated_at: string;
  results: TestResult[];
}

// ── Audit ─────────────────────────────────────────────────────────────────────
export interface AuditEvent {
  id: string;
  action: string;
  record_type: string;
  record_id: string;
  user_id: string;
  username: string;
  full_name: string;
  event_at: string;
  human_description: string;
  module: string;
  ip_address?: string;
  field_name?: string;
  old_value?: string;
  new_value?: string;
}

// ── Utility ───────────────────────────────────────────────────────────────────
export interface PaginationParams {
  skip?: number;
  limit?: number;
}

export interface SignaturePayload {
  password: string;
  meaning: string;
  comments?: string;
}
