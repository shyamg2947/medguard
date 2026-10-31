export interface Medication {
  id: string;
  brand_name?: string;
  generic_name: string;
  strength?: string;
  form?: string;
  frequency?: string;
  start_date?: string;
  status: string;
  user_confirmed: boolean;
}

export interface Alert {
  id: string;
  rule_id: string;
  severity: 'critical' | 'high' | 'moderate' | 'low';
  title: string;
  message: string;
  doctor_question: string;
  clinical_rationale: string;
  sources: string[];
  status: string;
  approved_for_patient: boolean;
  requires_clinician_review: boolean;
}

export interface RiskScores {
  acb: {
    total_score: number;
    band: string;
    flagged: boolean;
    breakdown: Array<{ drug: string; score: number }>;
  };
  fall_risk: {
    score: number;
    band: 'low' | 'moderate' | 'high';
    flagged_drugs: Array<{ drug: string; class: string; weight: number }>;
  };
  renal: {
    crcl_ml_min?: number;
    crcl_missing_inputs?: string[];
    is_impaired: boolean;
    stage?: string;
  };
}

export interface Patient {
  id: string;
  display_token: string;
  primary_language: string;
  age?: number;
  gender?: string;
  is_synthetic: boolean;
  medications?: Medication[];
}

export interface ReviewCase {
  id: string;
  patient_id: string;
  display_token: string;
  age?: number;
  gender?: string;
  medications: Array<{ generic: string; brand?: string; strength?: string; form?: string }>;
  alerts: Alert[];
  panel_summary?: string;
  draft_patient_message: string;
  severity: string;
}

export interface RuleProposal {
  id: string;
  rule_id: string;
  rejection_count: number;
  total_reviews: number;
  primary_reason_tag: string;
  proposed_change: string;
  evidence_summary: Record<string, any>;
  status: string;
  created_at: string;
}

export interface LLMUsage {
  daily_calls: number;
  daily_budget: number;
  session_calls: number;
  session_budget: number;
  cached_queries: number;
  circuit_breaker: string;
  free_tier_mode: boolean;
}

export interface SimulatorMessage {
  id: string;
  direction: 'inbound' | 'outbound';
  type: 'text' | 'voice' | 'image' | 'buttons' | 'emergency';
  body: string;
  media_url?: string;
  timestamp: string;
  quick_replies?: string[];
}

const API_BASE = '';

export async function fetchPatients(): Promise<Patient[]> {
  const res = await fetch(`${API_BASE}/caregivers/patients`, {
    headers: { Authorization: 'Bearer demo-admin-token' }
  });
  if (!res.ok) {
    // Fallback to synthetic scenarios
    return [
      { id: 'scen-a', display_token: 'PT-SCEN-A (Bleeding Risk)', primary_language: 'en', age: 74, gender: 'female', is_synthetic: true },
      { id: 'scen-b', display_token: 'PT-SCEN-B (Kidney Risk)', primary_language: 'hi', age: 69, gender: 'male', is_synthetic: true },
      { id: 'scen-c', display_token: 'PT-SCEN-C (Cascade & Falls)', primary_language: 'en', age: 80, gender: 'female', is_synthetic: true },
    ];
  }
  return res.json();
}

export async function fetchPatient(id: string): Promise<Patient> {
  const res = await fetch(`${API_BASE}/patients/${id}`);
  if (!res.ok) throw new Error('Patient not found');
  return res.json();
}

export async function fetchAlerts(patientId: string): Promise<Alert[]> {
  const res = await fetch(`${API_BASE}/patients/${patientId}/alerts`);
  if (!res.ok) return [];
  return res.json();
}

export async function fetchScores(patientId: string): Promise<RiskScores | null> {
  const res = await fetch(`${API_BASE}/patients/${patientId}/scores`);
  if (!res.ok) return null;
  return res.json();
}

export async function runAnalysis(patientId: string) {
  const res = await fetch(`${API_BASE}/patients/${patientId}/analyze`, { method: 'POST' });
  return res.json();
}

export async function fetchReviewQueue(): Promise<ReviewCase[]> {
  const res = await fetch(`${API_BASE}/review/queue`, {
    headers: { Authorization: 'Bearer demo-clinician-token' }
  });
  if (!res.ok) return [];
  return res.json();
}

export async function submitReview(
  caseId: string,
  decision: 'agree' | 'reject' | 'needs_info',
  reasonTag?: string,
  note?: string,
  patientMessageEdit?: string
) {
  const res = await fetch(`${API_BASE}/review/${caseId}/decision`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: 'Bearer demo-clinician-token'
    },
    body: JSON.stringify({
      decision,
      reason_tag: reasonTag,
      note,
      patient_message_edit: patientMessageEdit
    })
  });
  return res.json();
}

export async function undoReview(decisionId: string) {
  const res = await fetch(`${API_BASE}/review/${decisionId}/undo`, {
    method: 'POST',
    headers: { Authorization: 'Bearer demo-clinician-token' }
  });
  return res.json();
}

export async function revealPatientIdentity(patientId: string, reason: string) {
  const res = await fetch(`${API_BASE}/review/${patientId}/reveal?reason=${encodeURIComponent(reason)}`, {
    method: 'POST',
    headers: { Authorization: 'Bearer demo-clinician-token' }
  });
  return res.json();
}

export async function fetchRuleProposals(): Promise<RuleProposal[]> {
  const res = await fetch(`${API_BASE}/admin/rule-proposals`, {
    headers: { Authorization: 'Bearer demo-admin-token' }
  });
  if (!res.ok) return [];
  return res.json();
}

export async function decideRuleProposal(proposalId: string, action: 'accept' | 'reject') {
  const res = await fetch(`${API_BASE}/admin/rule-proposals/${proposalId}/decide?action=${action}`, {
    method: 'POST',
    headers: { Authorization: 'Bearer demo-admin-token' }
  });
  return res.json();
}

export async function fetchLLMUsage(): Promise<LLMUsage> {
  const res = await fetch(`${API_BASE}/admin/usage`, {
    headers: { Authorization: 'Bearer demo-admin-token' }
  });
  if (!res.ok) {
    return {
      daily_calls: 14,
      daily_budget: 1500,
      session_calls: 3,
      session_budget: 20,
      cached_queries: 42,
      circuit_breaker: 'closed',
      free_tier_mode: true
    };
  }
  return res.json();
}

export async function sendSimulatorMessage(phone: string, text: string): Promise<SimulatorMessage> {
  const res = await fetch(`${API_BASE}/simulator/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sender_phone: phone,
      message_type: 'text',
      text
    })
  });
  return res.json();
}

