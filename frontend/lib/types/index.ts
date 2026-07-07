export type UserRole = "admin" | "user";

export interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export type DocumentStatus = "uploaded" | "processing" | "analyzed" | "partial" | "failed";
export type FileType = "pdf" | "docx" | "txt";

export interface DocumentOut {
  id: number;
  owner_id: number;
  original_filename: string;
  file_type: FileType;
  file_size_bytes: number;
  status: DocumentStatus;
  status_detail: string | null;
  used_ocr: boolean;
  page_count: number | null;
  created_at: string;
  processed_at: string | null;
}

export interface DocumentListItem extends DocumentOut {
  contract_type: string | null;
  compliance_score: number | null;
  compliance_grade: string | null;
  high_risk_count: number;
}

export interface PartyItem {
  name: string;
  role: string | null;
}

export interface ResponsibilityItem {
  party: string;
  obligation: string;
}

export interface ImportantDate {
  label: string;
  date: string;
}

export interface AnalysisOut {
  id: number;
  document_id: number;
  contract_type: string | null;
  parties: PartyItem[];
  effective_date: string | null;
  expiry_date: string | null;
  payment_terms: string | null;
  renewal_clause: string | null;
  confidentiality_clause: string | null;
  termination_clause: string | null;
  responsibilities: ResponsibilityItem[];
  executive_summary: string | null;
  key_obligations: string[];
  important_dates: ImportantDate[];
  important_clauses: string[];
  recommended_actions: string[];
  compliance_score: number | null;
  compliance_grade: string | null;
  model_used: string | null;
  created_at: string;
}

export type RiskCategory =
  | "missing_clause"
  | "high_risk_condition"
  | "ambiguous_statement"
  | "unusual_payment_term"
  | "legal_red_flag";

export type RiskSeverity = "low" | "medium" | "high" | "critical";

export interface RiskFindingOut {
  id: number;
  analysis_id: number;
  category: RiskCategory;
  severity: RiskSeverity;
  confidence: number;
  title: string;
  explanation: string;
  supporting_clause_text: string | null;
  suggested_action: string | null;
  created_at: string;
}

export interface SearchResultItem {
  chunk_id: string;
  text: string;
  similarity: number;
}

export interface SearchResponse {
  mode: "retrieve" | "answer";
  results: SearchResultItem[];
  answer: string | null;
}

export type ReportFormat = "pdf" | "docx";

export interface ReportOut {
  id: number;
  document_id: number;
  analysis_id: number;
  format: ReportFormat;
  created_at: string;
}

export interface RiskTypeFrequency {
  category: RiskCategory;
  count: number;
}

export interface DashboardStats {
  total_documents: number;
  average_risk_score: number | null;
  high_risk_documents: number;
  frequent_risk_types: RiskTypeFrequency[];
  processing_history: DocumentListItem[];
}

export interface AdminUserOut {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
  document_count: number;
}

export type AuditLevel = "info" | "warning" | "error";

export interface AuditLogOut {
  id: number;
  user_id: number | null;
  action: string;
  resource_type: string | null;
  resource_id: number | null;
  detail: Record<string, unknown> | null;
  level: AuditLevel;
  created_at: string;
}

export interface SystemStatsOut {
  total_users: number;
  total_documents: number;
  total_analyses: number;
  total_groq_calls: number;
  average_processing_time_seconds: number | null;
  documents_by_status: Record<DocumentStatus, number>;
}

export interface ApiErrorBody {
  error_code: string;
  message: string;
  detail: string | null;
}
