export type RankingComponents = {
  temporal_precedence: number;
  anomaly_severity: number;
  dependency_centrality: number;
  trace_relationship: number;
  deployment_proximity: number;
  historical_similarity: number;
  runbook_relevance: number;
  agent_agreement: number;
  contradiction_penalty: number;
};

export type Hypothesis = {
  hypothesis_id: string;
  label: string;
  score: number;
  rank: number;
  components: RankingComponents;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  uncertainty: number;
};

export type Incident = {
  id: string;
  scenario_id: string;
  title: string;
  status: string;
  synthetic: boolean;
  hypotheses: Hypothesis[];
};

export type Simulation = {
  id: string;
  estimated_recovery_probability: number;
  uncertainty: number;
  expected_latency_improvement_pct: number;
  expected_error_rate_improvement_pct: number;
  blast_radius: string[];
  expected_downtime_seconds: number;
  rollback_feasibility: "low" | "medium" | "high";
  estimate_label: string;
};

export type Approval = { id: string; signature: string };
export type Execution = { id: string; state: string; detail: string };
export type Verification = { state: string; windows_observed: number; windows_required: number };
export type RetrievedChunk = { chunk_id: string; document_id: string; document_version: string; section: string; content: string; retrieval_score: number; trust_level: string; metadata: Record<string, unknown> };
export type EvaluationReport = { dataset_version: string; seed: number; generated_at: string; aggregate: Record<string, number>; per_scenario: Array<Record<string, unknown>> };
export type Postmortem = { incident_id: string; summary: string; impact: string; root_cause: string; resolution: string; citations: string[]; updated_at: string };

type ErrorEnvelope = { error?: { code?: string; message?: string; request_id?: string } };

const DEFAULT_API_BASE_URL = "https://opsassist-api-production.up.railway.app/api/v1";
const DEFAULT_WS_URL = "wss://opsassist-api-production.up.railway.app/api/v1/events";

export class OpsAssistApi {
  readonly baseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, "");
  readonly wsUrl = (process.env.NEXT_PUBLIC_WS_URL || DEFAULT_WS_URL).replace(/\/$/, "");
  readonly enabled = Boolean(this.baseUrl);
  constructor(private readonly tokenProvider: () => Promise<string | null> = async () => null) {}

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    if (!this.enabled) throw new Error("Python API URL is not configured");
    const token = await this.tokenProvider();
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: { "content-type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(init?.headers ?? {}) },
    });
    if (!response.ok) {
      const body = (await response.json().catch(() => ({}))) as ErrorEnvelope;
      throw new Error(body.error?.message ?? `OpsAssist API returned ${response.status}`);
    }
    return response.json() as Promise<T>;
  }

  health() { return this.request<{ status: string }>("/health"); }

  launchScenario() {
    return this.request<Incident>("/incidents/simulate", {
      method: "POST",
      body: JSON.stringify({ scenario_id: "checkout_pool_exhaustion", seed: 847 }),
    });
  }

  async investigate(incidentId: string) {
    const result = await this.request<{ incident: Incident }>(`/incidents/${incidentId}/investigate`, { method: "POST" });
    return result.incident;
  }

  simulate(incidentId: string) {
    return this.request<Simulation>(`/incidents/${incidentId}/simulate-action`, {
      method: "POST",
      body: JSON.stringify({
        action_type: "rollback_deployment",
        target_service: "checkout",
        parameters: { target_version: "v2.18.0", strategy: "rolling", min_healthy: 2 },
        seed: 847,
      }),
    });
  }

  approve(incidentId: string, simulationId: string) {
    return this.request<Approval>(`/incidents/${incidentId}/approve`, {
      method: "POST",
      body: JSON.stringify({ simulation_id: simulationId, actor_id: "demo-incident-commander", actor_role: "incident_commander", acknowledgement: true }),
    });
  }

  execute(incidentId: string, simulationId: string, approvalId: string) {
    return this.request<Execution>(`/incidents/${incidentId}/execute`, {
      method: "POST",
      headers: { "Idempotency-Key": `opsassist-${incidentId}-${simulationId}` },
      body: JSON.stringify({ simulation_id: simulationId, approval_id: approvalId, idempotency_key: `opsassist-${incidentId}-${simulationId}` }),
    });
  }

  verify(incidentId: string, executionId: string) {
    return this.request<Verification>(`/incidents/${incidentId}/verify?execution_id=${encodeURIComponent(executionId)}`, { method: "POST" });
  }

  searchKnowledge(query: string, serviceIds: string[] = []) {
    return this.request<RetrievedChunk[]>("/knowledge/search", {
      method: "POST",
      body: JSON.stringify({ query, service_ids: serviceIds, trust_levels: ["verified", "reviewed"], limit: 5 }),
    });
  }

  evaluations() { return this.request<EvaluationReport>("/evaluations"); }
  postmortem(incidentId: string) { return this.request<Postmortem>(`/incidents/${incidentId}/postmortem`); }

  connect(incidentId: string, onEvent: (event: { type: string; data: unknown }) => void) {
    if (!this.wsUrl || typeof WebSocket === "undefined") return () => undefined;
    let socket: WebSocket | null = null;
    let stopped = false;
    let retry = 0;
    let timer: number | undefined;
    const open = async () => {
      const token = await this.tokenProvider();
      socket = new WebSocket(`${this.wsUrl}?incident_id=${encodeURIComponent(incidentId)}`, token ? ["opsassist", `bearer.${token}`] : ["opsassist"]);
      socket.onopen = () => { retry = 0; socket?.send("ready"); };
      socket.onmessage = (message) => onEvent(JSON.parse(message.data));
      socket.onclose = () => {
        if (!stopped) timer = window.setTimeout(open, Math.min(10_000, 500 * 2 ** retry++));
      };
    };
    void open();
    return () => { stopped = true; if (timer) window.clearTimeout(timer); socket?.close(); };
  }
}
