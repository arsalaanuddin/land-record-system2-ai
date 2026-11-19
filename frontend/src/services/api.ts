// Typed client for the land record API.
// Field values are null when nothing was read from the document — never a
// placeholder. UI code must render a dash for null instead of text.

// Empty means same-origin, which the Vite dev server proxies to the API.
// Set VITE_API_BASE_URL when the frontend and API are served from different hosts.
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '';

export type UserRole = 'operator' | 'verifier' | 'tehsildar' | 'admin';

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface RecordField {
  // Spec contract
  field: string;
  value: string | null;
  original_text: string | null;
  ocr_confidence: number | null;
  extraction_confidence: number | null;
  validation_status: 'valid' | 'invalid' | 'missing' | 'unreadable' | 'needs_review' | 'not_checked';
  verification_status: 'pending' | 'approved' | 'rejected' | 'flagged';
  extraction_method: 'rules' | 'layoutlm' | 'manual' | 'none';
  source: { page: number; bbox: BoundingBox | null };
  warnings: string[];
  // UI conveniences
  key: string;
  label: string;
  category: string;
  confidence: number | null;
  boundingBox: BoundingBox | null;
}

export interface ValidationSummary {
  passed: boolean;
  errors: string[];
  warnings: string[];
  crossDatabaseChecks: { dbName: string; status: string; message: string; lastChecked: string | null }[];
  duplicateCheck: { isDuplicate: boolean; duplicateWithId?: string | null; message: string };
  businessRules: { ruleId: string; ruleName: string; passed: boolean; details: string }[];
  validatedAt?: string;
}

export interface StageView {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'unavailable';
  message: string | null;
  durationMs: number | null;
}

export interface LandRecord {
  id: string;
  status: 'verified' | 'review' | 'processing' | 'rejected' | 'failed';
  rawStatus: string;
  confidenceScore: number | null;
  documentType: string;
  documentLanguage: string;
  state: string;
  district: string | null;
  sha256Hash: string;
  lastUpdated: string;
  createdAt: string;
  fileName: string;
  pageCount: number;
  extractionMethod: string;
  surveyNumber: string | null;
  khasraNumber: string | null;
  khataNumber: string | null;
  ownerName: string | null;
  coOwners: string[];
  ownershipType: string | null;
  ownershipShare: string | null;
  area: string | null;
  village: string | null;
  tehsil: string | null;
  landClassification: string | null;
  mutationNumber: string | null;
  mutationDate: string | null;
  mutationType: string | null;
  registrationDeedNo: string | null;
  sroOffice: string | null;
  registrationDate: string | null;
  stampDutyStatus: string | null;
  coordinates: [number, number][];
  fields: RecordField[];
  validation: ValidationSummary;
  stages: StageView[];
  warnings: string[];
}

export interface DocumentStatusResponse {
  documentId: string;
  status: string;
  totalPages: number;
  stages: {
    name: string;
    status: StageView['status'];
    message: string | null;
    startedAt: string | null;
    finishedAt: string | null;
    details: Record<string, unknown>;
  }[];
  warnings: string[];
  updatedAt: string;
}

export interface DashboardStats {
  totalDocuments: number;
  totalProcessed: number;
  verifiedRecords: number;
  requiresReview: number;
  failedDocuments: number;
  processingProgress: number;
  extractionAccuracy: number | null;
  accuracyNote: string;
  avgConfidenceScore: number | null;
  activeLearningRetrainedCount: number;
  byType: Record<string, number>;
  errorStats: { type: string; count: number; percentage: number; color: string }[];
  stateProgress: {
    state: string;
    totalDistricts: number;
    digitizedDistricts: number | null;
    totalParcels: number | null;
    verifiedCount: number;
    pendingReview: number;
    accuracy: number | null;
    progressPercent: number;
  }[];
  recentActivity: { id: number; text: string; time: string; type: string }[];
}

export interface AuditLogEntry {
  id: number;
  recordId: string;
  timestamp: string;
  user: string;
  role: string;
  action: string;
  fieldChanged: string | null;
  oldValue: string | null;
  newValue: string | null;
  details: string | null;
  ipAddress: string | null;
}

export interface ApiKeyItem {
  id: string;
  name: string;
  prefix: string;
  role: string;
  created: string;
  lastUsed: string;
}

export interface IntegrationStatus {
  name: string;
  status: string;
  endpoint: string;
  latency: string;
  lastSync: string;
}

export interface Session {
  username: string;
  role: UserRole;
  name: string;
  designation: string;
  department: string;
  authenticated: boolean;
  method: string;
  notice: string;
}

export interface UploadOptions {
  file: File;
  language: string;
  documentType: string;
  state: string;
  district: string;
  enableDenoise: boolean;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API ${response.status} on ${path}: ${body}`);
  }
  return (await response.json()) as T;
}

export const api = {
  uploadDocument: async (options: UploadOptions) => {
    const form = new FormData();
    form.append('file', options.file);
    form.append('language', options.language);
    form.append('declared_document_type', options.documentType);
    form.append('state', options.state);
    form.append('district', options.district);
    form.append('enable_denoise', String(options.enableDenoise));
    return request<{
      documentId: string;
      recordId: string;
      status: string;
      fileName: string;
      fileSize: string;
      sha256: string;
    }>('/api/documents/upload', { method: 'POST', body: form });
  },

  getRecords: () => request<LandRecord[]>('/api/documents'),

  getRecord: (documentId: string) =>
    request<LandRecord>(`/api/documents/${encodeURIComponent(documentId)}`),

  getDocumentStatus: (documentId: string) =>
    request<DocumentStatusResponse>(`/api/documents/${encodeURIComponent(documentId)}/status`),

  getPageImageUrl: (documentId: string, page = 1) =>
    `${API_BASE_URL}/api/documents/${encodeURIComponent(documentId)}/pages/${page}`,

  submitVerification: (
    documentId: string,
    payload: {
      action: 'approve' | 'review' | 'reject';
      officer_id: string;
      role: UserRole;
      updated_fields: Record<string, string>;
      remarks?: string;
    },
  ) =>
    request<{ success: boolean; recordId: string; status: string; fieldsCorrected: number; message: string }>(
      `/api/documents/${encodeURIComponent(documentId)}/verification`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      },
    ),

  getDashboardStats: () => request<DashboardStats>('/api/dashboard/stats'),

  getAuditLogs: () => request<AuditLogEntry[]>('/api/audit-logs'),

  getApiPortalData: () =>
    request<{ apiKeys: ApiKeyItem[]; integrations: IntegrationStatus[] }>('/api/api-portal'),

  getGisParcels: () =>
    request<{ type: string; features: unknown[] }>('/api/gis/parcels'),

  login: (username: string, role: UserRole) =>
    request<Session>('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, role }),
    }),
};

export default api;
