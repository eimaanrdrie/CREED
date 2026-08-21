export type ServiceState = "CONNECTED" | "UNAVAILABLE" | "NOT_CONFIGURED";

export type HealthResponse = {
  service: string;
  status: "ok" | "degraded";
  version: string;
  environment: string;
  timestamp: string;
  dependencies: {
    api: ServiceState;
    database: ServiceState;
    qwen: ServiceState;
    knowledge_source: ServiceState;
  };
};

export type RuntimeState = {
  status: "READY" | "UNAVAILABLE";
  ollama: "CONNECTED" | "UNAVAILABLE";
  model: "AVAILABLE" | "UNAVAILABLE" | "NOT_INSTALLED";
  inference: "PASSED" | "UNAVAILABLE";
  configured_model: string;
  actual_model: string | null;
  checked_at: string;
  last_error: string | null;
  last_inference_duration_ms: number | null;
  ollama_base_url: string;
  last_execution: QwenExecutionRecord | null;
  recent_executions: QwenExecutionRecord[];
  execution_count: number;
};

export type QwenExecutionRecord = {
  run_id: string;
  node: string;
  configured_model: string;
  actual_model: string | null;
  started_at: string;
  completed_at: string;
  duration_ms: number;
  prompt_eval_count: number | null;
  eval_count: number | null;
  total_duration_ns: number | null;
  load_duration_ns: number | null;
  success: boolean;
  structured_output_valid: boolean;
  error: string | null;
};

export type QwenTestResult = {
  run_id: string;
  configured_model: string;
  actual_model: string | null;
  duration_ms: number;
  prompt_eval_count: number | null;
  eval_count: number | null;
  structured_output_valid: boolean;
  output: {
    classification: string;
    system: string;
    valid: boolean;
  };
  completed_at: string;
};

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function getHealth(): Promise<HealthResponse | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(3500),
    });
    if (!response.ok) return null;
    return (await response.json()) as HealthResponse;
  } catch {
    return null;
  }
}

export async function getAiRuntime(refresh = false): Promise<RuntimeState | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/ai/runtime?refresh=${refresh}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(refresh ? 60000 : 5000),
    });
    if (!response.ok) return null;
    return (await response.json()) as RuntimeState;
  } catch {
    return null;
  }
}


export type EvidenceDocument = {
  id: string;
  source: string;
  title: string;
  document_type: string;
  version: string | null;
  content_hash: string;
  original_filename: string | null;
  mime_type: string | null;
  file_size: number | null;
  parse_status: string;
  char_count: number;
  uploaded_at: string;
  metadata: Record<string, unknown>;
  index_status: string;
  chunk_count: number;
  embedding_model: string | null;
  embedding_degraded: boolean;
};

export type EvidenceDocumentDetail = EvidenceDocument & {
  extracted_text: string;
};

export async function getDocuments(): Promise<EvidenceDocument[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/documents`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`DOCUMENT_LIST_FAILED_${response.status}`);
  return (await response.json()) as EvidenceDocument[];
}

export async function uploadDocument(form: FormData): Promise<EvidenceDocumentDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/documents`, {
    method: "POST",
    body: form,
    signal: AbortSignal.timeout(45000),
  });
  if (!response.ok) {
    let detail = `UPLOAD_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : body.detail?.code ?? detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as EvidenceDocumentDetail;
}


export async function getDocument(id: string): Promise<EvidenceDocumentDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/documents/${id}`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`DOCUMENT_DETAIL_FAILED_${response.status}`);
  return (await response.json()) as EvidenceDocumentDetail;
}

export function getDocumentOriginalUrl(id: string): string {
  return `${API_BASE_URL}/api/v1/documents/${encodeURIComponent(id)}/original`;
}


export type RetrievalResult = {
  chunk_id: string;
  document_id: string;
  document_title: string;
  document_type: string;
  source: string;
  version: string | null;
  chunk_index: number;
  start_char: number;
  end_char: number;
  excerpt: string;
  score: number;
  semantic_score: number;
  keyword_score: number;
  metadata_score: number;
  embedding_model: string;
  embedding_degraded: boolean;
  citation: string;
};

export type RetrievalSearchResponse = {
  query: string;
  results: RetrievalResult[];
  searched_chunks: number;
  embedding: { provider: string; model: string; dimensions: number; degraded: boolean } | null;
  weights?: { semantic: number; keyword: number; metadata: number };
};

export async function searchKnowledge(query: string, topK = 8, filters?: { source?: string; document_type?: string; version?: string }): Promise<RetrievalSearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/retrieval/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: topK, ...filters }),
    signal: AbortSignal.timeout(60000),
  });
  if (!response.ok) {
    let detail = `SEARCH_FAILED_${response.status}`;
    try { const body = await response.json(); detail = body.detail ?? detail; } catch {}
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return (await response.json()) as RetrievalSearchResponse;
}

export type ClientRecord = {
  id: string;
  name: string;
  client_type: string;
};

export type ClientCreatePayload = {
  name: string;
  client_type: "BANK" | "FINANCIAL_INSTITUTION";
};

export type ProductRecord = {
  id: string;
  name: string;
  description: string | null;
  active: boolean;
};

export type ProductCreatePayload = {
  name: string;
  description?: string | null;
  active: boolean;
};

export type ProductUpdatePayload = {
  description?: string | null;
  active?: boolean;
};

export type ModuleRecord = {
  id: string;
  product_id: string;
  name: string;
  description: string | null;
  active: boolean;
};

export type ModuleCreatePayload = {
  product_id: string;
  name: string;
  description?: string | null;
  active: boolean;
};

export type ModuleUpdatePayload = {
  description?: string | null;
  active?: boolean;
};

export type DeliveryMethodRecord = {
  id: string;
  product_id: string;
  product_name: string;
  module_id: string;
  module_name: string;
  name: string;
  description: string | null;
};

export type DeliveryMethodCreatePayload = {
  module_id: string;
  name: string;
  description?: string | null;
};

export type RegisteredMethodVersionRecord = {
  id: string;
  method_id: string;
  method_name: string;
  product_id: string;
  product_name: string;
  module_id: string;
  module_name: string;
  version: string;
  status: string;
  summary: string | null;
  revoked_at: string | null;
  adoption_policy?: {
    enforced: boolean;
    learning_id: string;
    learning_status: string;
    receipt_id: string | null;
    receipt_integrity: "VALID" | "INVALID" | null;
    scope_mode: "METHOD_CATALOG" | "CURRENT_REGISTERED_IMPLEMENTATIONS" | "SELECTED_IMPLEMENTATIONS" | null;
    implementation_ids: string[];
    reason: string;
  } | null;
};

export type MethodVersionDraftCreatePayload = {
  method_id: string;
  version: string;
  summary?: string | null;
};

export type MethodVersionBaselineApprovalPayload = {
  reviewer: string;
  reason: string;
};

export type ImplementationRecord = {
  id: string;
  client_id: string;
  client_name: string;
  product_id: string;
  product_name: string;
  module_id: string;
  module_name: string;
  name: string;
  release_version: string;
  status: string;
};

export type ImplementationCreatePayload = {
  client_id: string;
  product_id: string;
  module_id: string;
  name: string;
  release_version: string;
};

export type DeploymentRecord = {
  id: string;
  implementation_id: string;
  implementation_name: string;
  implementation_status: string;
  client_id: string;
  client_name: string;
  product_id: string;
  product_name: string;
  module_id: string;
  module_name: string;
  release_version: string;
  environment: "DEVELOPMENT" | "SIT" | "UAT" | "PRODUCTION" | "DR" | string;
  status: string;
  deployed_at: string;
  deployment_reference: string | null;
  evidence_document_id: string | null;
  evidence_title: string | null;
  evidence_document_type: string | null;
  evidence_content_hash: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type DeploymentCreatePayload = {
  implementation_id: string;
  environment: "DEVELOPMENT" | "SIT" | "UAT" | "PRODUCTION" | "DR";
  deployed_at: string;
  deployment_reference?: string | null;
  evidence_document_id: string;
  notes?: string | null;
};

export type ImplementationMethodDependencyRecord = {
  id: string;
  relationship: string;
  implementation_id: string;
  implementation_name: string;
  implementation_release_version: string;
  implementation_status: string;
  client_id: string;
  client_name: string;
  product_id: string;
  product_name: string;
  module_id: string;
  module_name: string;
  method_id: string;
  method_name: string;
  method_version_id: string;
  method_version: string;
  method_version_status: string;
  evidence_document_id: string | null;
  evidence_title: string | null;
  evidence_document_type: string | null;
  evidence_version: string | null;
  evidence_content_hash: string | null;
  created_at: string;
};

export type ImplementationMethodDependencyCreatePayload = {
  implementation_id: string;
  method_version_id: string;
  evidence_document_id: string;
};

export type ResponsibilityScope = "PRODUCT" | "MODULE" | "IMPLEMENTATION" | "METHOD";
export type ResponsibilityType = "PRODUCT_OWNER" | "MODULE_OWNER" | "TECHNICAL_OWNER" | "QA_OWNER" | "IMPLEMENTATION_LEAD";

export type ResponsibilityAssignmentRecord = {
  id: string;
  scope_type: ResponsibilityScope;
  scope_id: string;
  scope_name: string;
  scope_context: string;
  responsibility_type: ResponsibilityType;
  authority_id: string;
  principal: string;
  display_name: string;
  authority_role_title: string;
  authority_active: boolean;
  team_name: string | null;
  created_at: string;
  updated_at: string;
};

export type ResponsibilityAssignmentCreatePayload = {
  scope_type: ResponsibilityScope;
  scope_id: string;
  responsibility_type: ResponsibilityType;
  authority_id: string;
  team_name?: string | null;
};

export type ResponsibilityAssignmentUpdatePayload = {
  authority_id: string;
  team_name?: string | null;
  reason: string;
};

export type HumanAuthorityRecord = {
  id: string;
  principal: string;
  display_name: string;
  role_title: string;
  active: boolean;
  can_submit_human_decision: boolean;
  can_approve_learning: boolean;
  can_authorize_recall: boolean;
  created_at: string;
  updated_at: string;
};

export type HumanAuthorityCreatePayload = {
  principal: string;
  display_name: string;
  role_title: string;
  active: boolean;
  can_submit_human_decision: boolean;
  can_approve_learning: boolean;
  can_authorize_recall: boolean;
};

export type HumanAuthorityUpdatePayload = Partial<Omit<HumanAuthorityCreatePayload, "principal">>;

export type IssueAttachment = {
  id: string;
  document_id: string;
  title: string;
  original_filename: string | null;
  document_type: string;
  parse_status: string;
  index_status: string;
  created_at: string;
};

export type SupportIssue = {
  id: string;
  external_ticket_id: string | null;
  client_id: string | null;
  client_name: string | null;
  title: string;
  description: string;
  issue_type: string;
  severity: string;
  status: string;
  attachment_count: number;
  created_at: string;
  updated_at: string;
};

export type SupportIssueDetail = SupportIssue & {
  attachments: IssueAttachment[];
  metadata: Record<string, unknown>;
};

export type IssueCreatePayload = {
  external_ticket_id?: string | null;
  client_id?: string | null;
  title: string;
  description: string;
  issue_type?: "BUG" | "CHANGE_REQUEST" | "ENHANCEMENT" | "INCIDENT" | "UNKNOWN";
  severity?: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | "UNKNOWN";
};

export async function getClients(): Promise<ClientRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/clients`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`CLIENT_LIST_FAILED_${response.status}`);
  return (await response.json()) as ClientRecord[];
}

export async function createClient(payload: ClientCreatePayload): Promise<ClientRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/clients`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `CLIENT_CREATE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as ClientRecord;
}

export async function getProducts(): Promise<ProductRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/products`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`PRODUCT_LIST_FAILED_${response.status}`);
  return (await response.json()) as ProductRecord[];
}

export async function createProduct(payload: ProductCreatePayload): Promise<ProductRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/products`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `PRODUCT_CREATE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as ProductRecord;
}

export async function updateProduct(productId: string, payload: ProductUpdatePayload): Promise<ProductRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/products/${encodeURIComponent(productId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `PRODUCT_UPDATE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as ProductRecord;
}

export async function getModules(productId?: string): Promise<ModuleRecord[]> {
  const query = productId ? `?product_id=${encodeURIComponent(productId)}` : "";
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/modules${query}`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`MODULE_LIST_FAILED_${response.status}`);
  return (await response.json()) as ModuleRecord[];
}

export async function createModule(payload: ModuleCreatePayload): Promise<ModuleRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/modules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `MODULE_CREATE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as ModuleRecord;
}

export async function updateModule(moduleId: string, payload: ModuleUpdatePayload): Promise<ModuleRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/modules/${encodeURIComponent(moduleId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `MODULE_UPDATE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as ModuleRecord;
}

export async function getDeliveryMethods(): Promise<DeliveryMethodRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/methods`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`METHOD_LIST_FAILED_${response.status}`);
  return (await response.json()) as DeliveryMethodRecord[];
}

export async function createDeliveryMethod(payload: DeliveryMethodCreatePayload): Promise<DeliveryMethodRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/methods`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `METHOD_CREATE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as DeliveryMethodRecord;
}

export async function getRegisteredMethodVersions(): Promise<RegisteredMethodVersionRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/method-versions`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`METHOD_VERSION_LIST_FAILED_${response.status}`);
  return (await response.json()) as RegisteredMethodVersionRecord[];
}

export async function createDraftMethodVersion(payload: MethodVersionDraftCreatePayload): Promise<RegisteredMethodVersionRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/method-versions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `METHOD_VERSION_CREATE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as RegisteredMethodVersionRecord;
}


export async function approveBaselineMethodVersion(
  versionId: string,
  payload: MethodVersionBaselineApprovalPayload,
  principal: string,
): Promise<RegisteredMethodVersionRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/method-versions/${encodeURIComponent(versionId)}/baseline-approval`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CREED-Principal": principal,
    },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `METHOD_BASELINE_APPROVAL_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as RegisteredMethodVersionRecord;
}

export async function getImplementations(): Promise<ImplementationRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/implementations`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`IMPLEMENTATION_LIST_FAILED_${response.status}`);
  return (await response.json()) as ImplementationRecord[];
}

export async function createImplementation(payload: ImplementationCreatePayload): Promise<ImplementationRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/implementations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `IMPLEMENTATION_CREATE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as ImplementationRecord;
}

export async function getDeployments(): Promise<DeploymentRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/deployments`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`DEPLOYMENT_LIST_FAILED_${response.status}`);
  return (await response.json()) as DeploymentRecord[];
}

export async function createDeployment(payload: DeploymentCreatePayload): Promise<DeploymentRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/deployments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `DEPLOYMENT_CREATE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as DeploymentRecord;
}

export async function getImplementationMethodDependencies(): Promise<ImplementationMethodDependencyRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/dependencies`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`DEPENDENCY_LIST_FAILED_${response.status}`);
  return (await response.json()) as ImplementationMethodDependencyRecord[];
}

export async function createImplementationMethodDependency(
  payload: ImplementationMethodDependencyCreatePayload,
): Promise<ImplementationMethodDependencyRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/dependencies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `DEPENDENCY_CREATE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as ImplementationMethodDependencyRecord;
}

export async function removeImplementationMethodDependency(
  dependencyId: string,
  reason: string,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/dependencies/${encodeURIComponent(dependencyId)}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `DEPENDENCY_REMOVE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
}

export async function getOwnershipAssignments(): Promise<ResponsibilityAssignmentRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/ownership`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`OWNERSHIP_LIST_FAILED_${response.status}`);
  return (await response.json()) as ResponsibilityAssignmentRecord[];
}

export async function createOwnershipAssignment(
  payload: ResponsibilityAssignmentCreatePayload,
): Promise<ResponsibilityAssignmentRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/ownership`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `OWNERSHIP_CREATE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as ResponsibilityAssignmentRecord;
}

export async function updateOwnershipAssignment(
  assignmentId: string,
  payload: ResponsibilityAssignmentUpdatePayload,
): Promise<ResponsibilityAssignmentRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/ownership/${encodeURIComponent(assignmentId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `OWNERSHIP_UPDATE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as ResponsibilityAssignmentRecord;
}

export async function removeOwnershipAssignment(assignmentId: string, reason: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/ownership/${encodeURIComponent(assignmentId)}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `OWNERSHIP_REMOVE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
}

export async function getHumanAuthorities(): Promise<HumanAuthorityRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/authorities`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`AUTHORITY_LIST_FAILED_${response.status}`);
  return (await response.json()) as HumanAuthorityRecord[];
}

export async function createHumanAuthority(payload: HumanAuthorityCreatePayload): Promise<HumanAuthorityRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/authorities`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `AUTHORITY_CREATE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as HumanAuthorityRecord;
}

export async function updateHumanAuthority(
  authorityId: string,
  payload: HumanAuthorityUpdatePayload,
): Promise<HumanAuthorityRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domain/authorities/${encodeURIComponent(authorityId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `AUTHORITY_UPDATE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as HumanAuthorityRecord;
}

export async function getIssues(): Promise<SupportIssue[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/issues`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`ISSUE_LIST_FAILED_${response.status}`);
  return (await response.json()) as SupportIssue[];
}

export async function getIssue(id: string): Promise<SupportIssueDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/issues/${id}`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`ISSUE_DETAIL_FAILED_${response.status}`);
  return (await response.json()) as SupportIssueDetail;
}

export async function createIssue(payload: IssueCreatePayload): Promise<SupportIssueDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/issues`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `ISSUE_CREATE_FAILED_${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as SupportIssueDetail;
}

export type IssueUnderstanding = {
  id: string;
  issue_id: string;
  qwen_run_id: string;
  input_hash: string;
  configured_model: string;
  actual_model: string | null;
  duration_ms: number | null;
  prompt_eval_count: number | null;
  eval_count: number | null;
  client_name: string | null;
  product: string | null;
  module: string | null;
  issue_type: "BUG" | "CHANGE_REQUEST" | "ENHANCEMENT" | "INCIDENT" | "UNKNOWN";
  summary: string;
  suspected_function: string | null;
  keywords: string[];
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | "UNKNOWN";
  confidence: number;
  status: "AI_GENERATED" | "HUMAN_VERIFIED" | string;
  human_verified_by: string | null;
  human_verified_at: string | null;
  created_at: string;
  updated_at: string;
  warnings: string[];
};

export type IssueUnderstandingEdit = Pick<IssueUnderstanding,
  "client_name" | "product" | "module" | "issue_type" | "summary" | "suspected_function" | "keywords" | "severity"
>;

export async function getIssueUnderstanding(issueId: string): Promise<IssueUnderstanding | null> {
  const response = await fetch(`${API_BASE_URL}/api/v1/issues/${issueId}/understanding`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`ISSUE_UNDERSTANDING_FAILED_${response.status}`);
  const body = await response.json();
  return body as IssueUnderstanding | null;
}

export async function runIssueUnderstanding(issueId: string): Promise<IssueUnderstanding> {
  const response = await fetch(`${API_BASE_URL}/api/v1/issues/${issueId}/understand`, {
    method: "POST",
    signal: AbortSignal.timeout(90000),
  });
  if (!response.ok) {
    let detail = `ISSUE_UNDERSTANDING_FAILED_${response.status}`;
    try { const body = await response.json(); detail = typeof body.detail === "string" ? body.detail : detail; } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as IssueUnderstanding;
}

export async function updateIssueUnderstanding(issueId: string, understandingId: string, payload: IssueUnderstandingEdit): Promise<IssueUnderstanding> {
  const response = await fetch(`${API_BASE_URL}/api/v1/issues/${issueId}/understanding/${understandingId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let detail = `ISSUE_UNDERSTANDING_UPDATE_FAILED_${response.status}`;
    try { const body = await response.json(); detail = typeof body.detail === "string" ? body.detail : detail; } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as IssueUnderstanding;
}

export type AgentLifecycleStatus = "QUEUED" | "RUNNING" | "COMPLETED" | "WAITING_HUMAN" | "FAILED" | "SKIPPED" | "CANCELLED";

export type AnalysisStep = {
  id: string;
  agent_name: string;
  display_name: string;
  task: string | null;
  module: string | null;
  status: AgentLifecycleStatus;
  sequence: number;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  output_summary: string | null;
  error: string | null;
  metadata: Record<string, unknown>;
};

export type AnalysisRun = {
  id: string;
  graph_run_id: string;
  issue_id: string | null;
  status: AgentLifecycleStatus;
  started_at: string | null;
  completed_at: string | null;
  input_summary: string | null;
  output_summary: string | null;
  error: string | null;
  created_at: string;
  checkpoint_backend: string;
  latest_event_seq: number;
  recovery_eligible?: boolean;
  recovery_reason?: string | null;
  steps: AnalysisStep[];
};

export async function startAnalysisRun(issueId: string): Promise<AnalysisRun> {
  const response = await fetch(`${API_BASE_URL}/api/v1/issues/${issueId}/analysis-runs`, {
    method: "POST",
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) {
    let detail = `ANALYSIS_RUN_START_FAILED_${response.status}`;
    try { const body = await response.json(); detail = typeof body.detail === "string" ? body.detail : detail; } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as AnalysisRun;
}

export async function recoverStuckAnalysisRun(issueId: string, reason: string): Promise<AnalysisRun> {
  const response = await fetch(`${API_BASE_URL}/api/v1/issues/${issueId}/analysis-runs/recover`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) {
    let detail = `ANALYSIS_RUN_RECOVERY_FAILED_${response.status}`;
    try { const body = await response.json(); detail = typeof body.detail === "string" ? body.detail : detail; } catch {}
    throw new Error(detail);
  }
  return (await response.json()) as AnalysisRun;
}

export async function getLatestAnalysisRun(issueId: string): Promise<AnalysisRun | null> {
  const response = await fetch(`${API_BASE_URL}/api/v1/issues/${issueId}/analysis-runs/latest`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) {
    if (response.status === 404) return null;
    throw new Error(`ANALYSIS_RUN_FETCH_FAILED_${response.status}`);
  }
  return (await response.json()) as AnalysisRun | null;
}

export function analysisRunEventsUrl(graphRunId: string, after = 0): string {
  return `${API_BASE_URL}/api/v1/analysis-runs/${encodeURIComponent(graphRunId)}/events?after=${Math.max(0, after)}`;
}

// M09-M20 integrated CREED intelligence APIs
async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api/v1${path}`, { cache: "no-store", ...init });
  if (!response.ok) {
    let detail = `${path}_FAILED_${response.status}`;
    try { const body = await response.json(); detail = typeof body.detail === "string" ? body.detail : detail; } catch {}
    throw new Error(detail);
  }
  return await response.json() as T;
}
export type DashboardCoverageMetric = { numerator: number; denominator: number; percent: number | null };
export type DashboardDecision = { decision: string; reviewer: string; reason: string; decided_at: string };
export type DashboardData = {
  metrics: Record<string, number>;
  coverage: Record<string, DashboardCoverageMetric>;
  recent_decisions: DashboardDecision[];
};
export const getDashboard = () => jsonFetch<DashboardData>("/dashboard");
export type ImpactData = {graph_run_id:string;issue_id:string;weights:Record<string,number>;results:Array<{id:string;implementation_id:string;implementation_name:string;client_name:string;impact_score:number;impact_band:string;reported_source:boolean;signals:Record<string,number>;explanation:Array<{signal:string;value:number;weight:number;contribution:number}>;evidence_refs:string[]}>;graph:{nodes:Array<Record<string,unknown>>;edges:Array<Record<string,unknown>>}};
export const getImpact = (run:string) => jsonFetch<ImpactData>(`/analysis-runs/${encodeURIComponent(run)}/impact`);
export const getRecall = (id:string) => jsonFetch<any>(`/recalls/${encodeURIComponent(id)}`);
export const getRecalls = () => jsonFetch<any[]>("/recalls");
export type AuditTimelineCategory = "ISSUE" | "AGENT" | "AI" | "EVIDENCE" | "IMPACT" | "HUMAN" | "GOVERNANCE" | "AUDIT";
export type AuditTimelineItem = {
  category: AuditTimelineCategory | string;
  at: string;
  title: string;
  detail?: string | null;
  id?: string;
  actor?: string;
  reviewer?: string;
  status?: string;
  duration_ms?: number | null;
  model?: string | null;
  run_id?: string;
  error?: string | null;
  content_hash?: string;
  document_id?: string;
  score?: number;
  impact_score?: number;
  evidence_refs?: string[];
  href?: string;
  metadata?: Record<string, unknown>;
};
export type AuditData = {
  graph_run_id: string | null;
  run_id: string | null;
  scope: {
    mode: "RUN" | "GLOBAL";
    run: null | { id:string; graph_run_id:string; status:string; started_at:string|null; completed_at:string|null; duration_ms:number|null; input_summary:string|null; output_summary:string|null; error:string|null };
    issue: null | { id:string; ticket:string|null; title:string; status:string; client_id:string|null };
  };
  summary: {
    timeline_records:number; agent_steps:number; qwen_calls:number; evidence_accesses:number; impact_assessments:number;
    human_decisions:number; governance_artefacts:number; failures:number; category_counts:Record<string,number>;
  };
  agents: Array<{id:string;agent_name:string;display_name:string;status:string;sequence:number;started_at:string|null;completed_at:string|null;duration_ms:number|null;input_summary:string|null;output_summary:string|null;error:string|null;metadata:Record<string,unknown>}>;
  qwen_calls: Array<{run_id:string;node:string;purpose:string;configured_model:string|null;actual_model:string|null;duration_ms:number|null;prompt_tokens:number|null;output_tokens:number|null;structured_output_valid:boolean;success:boolean;status:string;evidence_refs:string[];at:string|null;error:string|null}>;
  evidence: Array<{id:string;rank:number;document_id:string;document_title:string;document_type:string|null;version:string|null;source:string|null;content_hash:string|null;citation:string;excerpt:string;final_score:number;semantic_score:number;keyword_score:number;metadata_score:number;embedding_model:string|null;embedding_degraded:boolean;at:string}>;
  impacts: Array<{id:string;implementation_id:string;implementation_name:string|null;client_name:string|null;method_version_id:string|null;impact_score:number;impact_band:string;reported_source:boolean;signals:Record<string,number>;weights:Record<string,number>;explanation:Array<Record<string,unknown>>;evidence_refs:string[];at:string}>;
  human_decisions: Array<{id:string;investigation_id:string;implementation_name:string|null;client_name:string|null;decision:string;reviewer:string;reason:string|null;decided_at:string;metadata:Record<string,unknown>}>;
  governance: Array<{type:"ADOPTION"|"RECALL"|string;id:string;status:string;actor:string;at:string;content_hash:string;hash_algorithm:string;integrity:string;detail:string|null;href:string}>;
  timeline: AuditTimelineItem[];
};
export const getAudit = (run?:string) => jsonFetch<AuditData>(`/audit${run?`?graph_run_id=${encodeURIComponent(run)}`:""}`);
export const getResilience = () => jsonFetch<any>("/resilience");
export const getRunEvidence = (run:string) => jsonFetch<any>(`/analysis-runs/${encodeURIComponent(run)}/evidence`);
export const getRunInvestigations = (run:string) => jsonFetch<any>(`/analysis-runs/${encodeURIComponent(run)}/investigations`);
export const getHumanReview = (run:string) => jsonFetch<any>(`/analysis-runs/${encodeURIComponent(run)}/human-review`);
export const resumeHumanReview = (run:string,payload:any,principal:string) => jsonFetch<any>(`/analysis-runs/${encodeURIComponent(run)}/human-review/resume`,{method:"POST",headers:{"Content-Type":"application/json","X-CREED-Principal":principal},body:JSON.stringify(payload)});

export type AdoptionScopeMode = "METHOD_CATALOG" | "CURRENT_REGISTERED_IMPLEMENTATIONS" | "SELECTED_IMPLEMENTATIONS";
export type AdoptionScopeSummary = {
  scope_version?: string;
  mode?: AdoptionScopeMode;
  product?: { id:string; name:string };
  module?: { id:string; name:string };
  method?: { id:string; name:string };
  source_method_version?: { id:string; version:string };
  adopted_method_version?: { id:string; version:string };
  implementation_ids?: string[];
  implementations?: Array<{ id:string; name:string | null; release_version:string | null; client_id:string | null; client_name:string | null }>;
  registered_adopter_count?: number;
  automatic_deployment_change?: boolean;
};

export type AdoptionReceiptSummary = {
  id: string;
  learning_id: string;
  approved_by: string;
  approved_at: string;
  content_hash: string;
  adoption_scope: AdoptionScopeSummary;
  source_issue_id: string;
  source_method_version_id: string;
  adopted_method_version_id: string;
  approval_reason: string;
  evidence: Array<{ id:string; title:string; document_type:string | null; version:string | null; source:string | null; content_hash:string | null }>;
  payload: Record<string, unknown>;
  attestation: string;
  receipt_version: string;
  hash_algorithm: string;
  integrity: "VALID" | "INVALID" | string;
};

export type AdoptionReceiptVerification = {
  valid: boolean;
  status: string;
  hash_algorithm: string;
  content_hash: string;
};

export type LearningProposalSummary = {
  id: string;
  status: string;
  source_issue_id: string;
  source_method_version: { id: string; version: string; status: string } | null;
  proposed_method_version: { id: string; version: string; status: string; summary: string | null } | null;
  title: string | null;
  summary: string;
  correction_input: string;
  applicability: string | null;
  guardrails: string[];
  validation_steps: string[];
  supporting_evidence_refs: string[];
  qwen: { run_id: string; configured_model: string; actual_model: string | null; duration_ms: number | null } | null;
  human_edited_by: string | null;
  decision_by: string | null;
  decision_at: string | null;
  decision_reason: string | null;
  adoption_receipt: AdoptionReceiptSummary | null;
};
export const getLearningProposal = (run:string) => jsonFetch<LearningProposalSummary | null>(`/analysis-runs/${encodeURIComponent(run)}/learning-proposal`);

export type LearningReadiness = {
  eligible: boolean;
  reason: string;
  source_method_version: { id:string; version:string; status:string; method_name:string | null } | null;
  suggested_new_version: string;
  affected_decision_count: number;
  affected_reviewers: string[];
  supporting_evidence_count: number;
};
export const getLearningReadiness = (run:string) => jsonFetch<LearningReadiness>(`/analysis-runs/${encodeURIComponent(run)}/learning-readiness`);
export const createLearningProposal = (
  run:string,
  payload:{ new_version:string; corrected_method:string; author:string },
  principal:string,
) => jsonFetch<LearningProposalSummary>(`/analysis-runs/${encodeURIComponent(run)}/learning-proposal`, {
  method:"POST",
  headers:{"Content-Type":"application/json","X-CREED-Principal":principal},
  body:JSON.stringify(payload),
});

export type LearningDecisionResult = {
  learning: LearningProposalSummary;
  receipt: AdoptionReceiptSummary | null;
};

export type AdoptionScopeInput = { mode:AdoptionScopeMode; implementation_ids:string[] };

export const decideLearningProposal = (
  proposalId:string,
  payload:{ reviewer:string; decision:"APPROVE_LEARNING"|"REJECT_LEARNING"; reason:string; adoption_scope?:AdoptionScopeInput },
  principal:string,
) => jsonFetch<LearningDecisionResult>(`/learning-proposals/${encodeURIComponent(proposalId)}/decision`, {
  method:"POST",
  headers:{"Content-Type":"application/json","X-CREED-Principal":principal},
  body:JSON.stringify(payload),
});

export const getAdoptionReceipt = (receiptId:string) =>
  jsonFetch<AdoptionReceiptSummary>(`/adoption-receipts/${encodeURIComponent(receiptId)}`);

export const verifyAdoptionReceipt = (receiptId:string) =>
  jsonFetch<AdoptionReceiptVerification>(`/adoption-receipts/${encodeURIComponent(receiptId)}/verify`);

export type MethodAbom = {
  method_version:{ id:string; version:string; status:string; method_id:string; method_name:string | null; module:string | null; product:string | null };
  clients:number;
  implementations:Array<{ id:string; name:string; release_version:string; client_id:string; client_name:string; edge_id:string; confidence:number; evidence_document_id:string | null }>;
  documents:Array<{ id:string; title:string; document_type:string | null; version:string | null; content_hash:string | null }>;
  persistent_edges:number;
  edges:Array<Record<string,unknown>>;
};
export const getMethodAbom = (versionId:string) => jsonFetch<MethodAbom>(`/knowledge-graph/method-versions/${encodeURIComponent(versionId)}/abom`);

export type MethodVersionRecord = {
  id: string;
  version: string;
  status: string;
  method_id: string;
  method_name: string | null;
  adoption_policy?: {
    enforced: boolean;
    learning_id: string;
    learning_status: string;
    receipt_id: string | null;
    receipt_integrity: "VALID" | "INVALID" | null;
    scope_mode: "METHOD_CATALOG" | "CURRENT_REGISTERED_IMPLEMENTATIONS" | "SELECTED_IMPLEMENTATIONS" | null;
    implementation_ids: string[];
    reason: string;
  } | null;
};

export type RecallCaseRecord = {
  id: string;
  implementation_id: string;
  implementation_name: string | null;
  client_name: string | null;
  investigation_id: string;
  status: string;
  dependency_edge_id: string;
};

export type RecallEvidenceRecord = {
  id: string;
  title: string;
  content_hash: string;
  version: string | null;
};

export type RecallRecord = {
  id: string;
  revoked_version_id: string;
  reason: string;
  approved_by: string;
  created_at: string;
  content_hash: string;
  status: string;
  source_issue_id: string;
  recall_run_id: string;
  evidence: RecallEvidenceRecord[];
  affected_implementation_ids: string[];
  attestation: string;
  notice_version: string;
  hash_algorithm: string;
  routing_scope: {
    enforced: boolean;
    mode: "METHOD_CATALOG" | "CURRENT_REGISTERED_IMPLEMENTATIONS" | "SELECTED_IMPLEMENTATIONS" | null;
    adoption_receipt_id: string | null;
    receipt_integrity: "VALID" | "INVALID" | null;
    scope_implementation_ids: string[];
    explicit_dependency_count: number;
    routed_count: number;
    routed_implementation_ids: string[];
    blocked_count: number;
    blocked_implementations: Array<{ implementation_id: string; dependency_edge_id: string; reason: string }>;
    basis: string;
  };
  integrity: string;
  cases: RecallCaseRecord[];
  graph: { nodes: Array<Record<string, unknown>>; edges: Array<Record<string, unknown>> };
};

export type RecallVerification = {
  valid: boolean;
  status: string;
  hash_algorithm: string;
  content_hash: string;
};

export const getMethodVersions = () => jsonFetch<MethodVersionRecord[]>("/knowledge-graph/method-versions");
export const revokeMethodVersion = (
  versionId: string,
  payload: { source_issue_id: string; evidence_document_ids?: string[]; reviewer: string; reason: string },
  principal: string,
) => jsonFetch<RecallRecord>(`/method-versions/${encodeURIComponent(versionId)}/revoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CREED-Principal": principal },
    body: JSON.stringify(payload),
  });
export const verifyRecall = (id: string) => jsonFetch<RecallVerification>(`/recalls/${encodeURIComponent(id)}/verify`);

export type DemoReadinessCheck = {
  key: string;
  label: string;
  status: "PASS" | "BLOCKED" | "WARN";
  detail: string;
};

export type DemoReadiness = {
  ready: boolean;
  blocking_checks: string[];
  checks: DemoReadinessCheck[];
  dataset: {
    dataset: string;
    synthetic: boolean;
    ready: boolean;
    clients: number;
    implementations: number;
    documents: number;
    indexed_documents: number;
    dependency_edges: number;
    baseline_version: string | null;
    baseline_status: string | null;
    active_authorities: number;
    decision_authorities: number;
    learning_authorities: number;
    recall_authorities: number;
    production_deployments: number;
    ownership_assignments: number;
    main_live_issue_count: number;
    active_analysis_runs: number;
    human_decisions: number;
    active_learnings: number;
    recalls: number;
  };
  runtime: {
    qwen_status: string | null;
    configured_model: string | null;
    actual_model: string | null;
    langgraph: string;
  };
  live_issue: {
    ticket: string;
    client: string;
    title: string;
    issue_type: string;
    severity: string;
  };
};

export const getDemoReadiness = (refreshRuntime = false) =>
  jsonFetch<DemoReadiness>(`/demo/readiness?refresh_runtime=${refreshRuntime ? "true" : "false"}`);

export const resetDemoBaseline = () =>
  jsonFetch<DemoReadiness["dataset"]>("/demo/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: "RESET CREED DEMO" }),
  });
