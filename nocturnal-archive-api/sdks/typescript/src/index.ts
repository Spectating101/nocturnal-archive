/**
 * Nocturnal Archive TypeScript SDK
 */

export interface SearchRequest {
  query: string;
  limit?: number;
  sources?: string[];
}

export interface SearchResponse {
  papers: any[];
  count: number;
  query_id: string;
  trace_id: string;
}

export interface FinanceContext {
  series: TimeSeries[];
}

export interface TimeSeries {
  series_id: string;
  freq: "D" | "W" | "M" | "Q" | "A";
  points: [string, number][];
}

export interface NumericClaim {
  id: string;
  metric: string;
  operator: "=" | "<" | "<=" | ">" | ">=" | "change" | "yoy" | "qoq";
  value: number;
  at?: string;
  window?: number;
}

export interface FinanceSynthesisRequest {
  context: FinanceContext;
  claims: NumericClaim[];
  grounded?: boolean;
  max_words?: number;
  style?: string;
}

export interface FinanceSynthesisResponse {
  summary: string;
  evidence: any[];
  grounded: boolean;
  claims_verified: number;
  total_claims: number;
}

export interface JobResponse {
  job_id: string;
  status: string;
  message?: string;
}

export interface JobStatus {
  status: "queued" | "started" | "finished" | "failed" | "not_found" | "error";
  result?: any;
  error?: string;
  created_at?: string;
  started_at?: string;
  ended_at?: string;
}

export class NocturnalClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(baseUrl: string = process.env.NOCTURNAL_BASE || "https://api.nocturnal.dev", apiKey: string = process.env.NOCTURNAL_KEY || "") {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  private getHeaders(): Record<string, string> {
    return {
      "X-API-Key": this.apiKey,
      "Content-Type": "application/json"
    };
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Search academic papers
   */
  async papersSearch(request: SearchRequest): Promise<SearchResponse> {
    return this.request<SearchResponse>("/v1/api/papers/search", {
      method: "POST",
      body: JSON.stringify(request)
    });
  }

  /**
   * Synthesize finance data with numeric grounding
   */
  async financeSynthesize(request: FinanceSynthesisRequest): Promise<FinanceSynthesisResponse> {
    return this.request<FinanceSynthesisResponse>("/v1/api/finance/synthesize", {
      method: "POST",
      body: JSON.stringify(request)
    });
  }

  /**
   * Create an async synthesis job
   */
  async createSynthesisJob(request: Omit<FinanceSynthesisRequest, "grounded">): Promise<JobResponse> {
    return this.request<JobResponse>("/v1/api/jobs/synthesis", {
      method: "POST",
      body: JSON.stringify(request)
    });
  }

  /**
   * Get job status and result
   */
  async getJobStatus(jobId: string): Promise<JobStatus> {
    return this.request<JobStatus>(`/v1/api/jobs/${jobId}`);
  }

  /**
   * Verify claims without synthesis
   */
  async verifyClaims(context: FinanceContext, claims: NumericClaim[]): Promise<any> {
    return this.request("/v1/api/finance/verify-claims", {
      method: "POST",
      body: JSON.stringify({ context, claims, grounded: true })
    });
  }

  /**
   * Convenience method for simple paper search
   */
  async searchPapers(query: string, limit: number = 10): Promise<SearchResponse> {
    return this.papersSearch({ query, limit });
  }

  /**
   * Convenience method for finance synthesis
   */
  async synthesizeFinance(context: FinanceContext, claims: NumericClaim[]): Promise<FinanceSynthesisResponse> {
    return this.financeSynthesize({ context, claims, grounded: true });
  }
}

// Default client instance
export const nocturnal = new NocturnalClient();

// Convenience functions
export async function searchPapers(query: string, limit: number = 10): Promise<SearchResponse> {
  return nocturnal.searchPapers(query, limit);
}

export async function synthesizeFinance(context: FinanceContext, claims: NumericClaim[]): Promise<FinanceSynthesisResponse> {
  return nocturnal.synthesizeFinance(context, claims);
}

export async function createSynthesisJob(context: FinanceContext, claims: NumericClaim[]): Promise<JobResponse> {
  return nocturnal.createSynthesisJob({ context, claims });
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  return nocturnal.getJobStatus(jobId);
}
