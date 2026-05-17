/**
 * @codeintel/sdk — typed client for the CodeIntel API.
 *
 * Used by the dashboard (server components) and the VS Code extension.
 * Browser-safe and node-safe.
 */
export interface FunctionTarget {
  language: 'python' | 'typescript' | 'javascript';
  file: string;
  name: string;
  qualified_name: string;
  source_code: string;
  start_line: number;
  end_line: number;
  raises: string[];
}

export type RunState =
  | 'pending'
  | 'generating'
  | 'validating'
  | 'healing'
  | 'passed'
  | 'failed'
  | 'cancelled';

export interface TestRun {
  id: string;
  org_id: string | null;
  repo: string | null;
  target: FunctionTarget;
  framework: 'pytest' | 'jest' | 'vitest';
  state: RunState;
  attempts: GenerationAttempt[];
  final_test_code: string | null;
  final_explanation: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface GenerationAttempt {
  attempt: number;
  provider: string;
  model: string;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  test_code: string;
  explanation: string;
  sandbox_passed: boolean | null;
  elapsed_ms: number | null;
}

export interface ScanResponse {
  repo_path: string;
  total: number;
  coverage_pct: number;
  uncovered: string[];
  targets: FunctionTarget[];
}

export interface RunSummary {
  id: string;
  state: RunState;
  function: string;
  file: string;
  framework: string;
  attempts: number;
  passed: boolean;
  created_at: string;
  updated_at: string;
}

export class CodeIntelClient {
  constructor(
    public readonly baseUrl: string,
    private readonly tokenProvider: () => Promise<string | undefined> | string | undefined,
  ) {}

  async scan(repoPath: string, languages?: string[]): Promise<ScanResponse> {
    return this.request<ScanResponse>('POST', '/v1/scans', { repo_path: repoPath, languages });
  }

  async createRun(input: {
    repoPath: string;
    functionName: string;
    language: string;
    framework: string;
    maxRetries?: number;
    model?: string;
  }): Promise<TestRun> {
    return this.request<TestRun>('POST', '/v1/runs', {
      repo_path: input.repoPath,
      function_name: input.functionName,
      language: input.language,
      framework: input.framework,
      max_retries: input.maxRetries ?? 3,
      model: input.model,
    });
  }

  async getRun(id: string): Promise<TestRun> {
    return this.request<TestRun>('GET', `/v1/runs/${id}`);
  }

  async listRuns(): Promise<RunSummary[]> {
    return this.request<RunSummary[]>('GET', '/v1/runs');
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const headers: Record<string, string> = { 'content-type': 'application/json' };
    const token = await this.tokenProvider();
    if (token) {
      headers['authorization'] = `Bearer ${token}`;
    }
    const r = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!r.ok) {
      throw new CodeIntelApiError(r.status, await r.text(), path);
    }
    return (await r.json()) as T;
  }
}

export class CodeIntelApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly bodyText: string,
    public readonly path: string,
  ) {
    super(`CodeIntel ${status} ${path}: ${bodyText}`);
    this.name = 'CodeIntelApiError';
  }
}
