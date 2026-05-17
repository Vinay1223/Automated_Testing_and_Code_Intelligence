/**
 * Tiny REST client. We don't pull a dep — `fetch` is built into Node 18+
 * and is available inside VS Code's extension host on every supported
 * platform.
 */
import * as vscode from 'vscode';

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

export interface TestRun {
  id: string;
  state: 'pending' | 'generating' | 'validating' | 'healing' | 'passed' | 'failed' | 'cancelled';
  framework: string;
  attempts: unknown[];
  final_test_code: string | null;
  final_explanation: string | null;
  target: FunctionTarget;
  error: string | null;
}

export interface ScanResult {
  total: number;
  coverage_pct: number;
  uncovered: string[];
  targets: FunctionTarget[];
}

export class ApiClient {
  constructor(
    private readonly baseUrl: string,
    private readonly token: string | undefined,
  ) {}

  async scan(repoPath: string, languages?: string[]): Promise<ScanResult> {
    return this.post<ScanResult>('/v1/scans', { repo_path: repoPath, languages });
  }

  async createRun(input: {
    repoPath: string;
    functionName: string;
    language: string;
    framework: string;
    maxRetries: number;
    model?: string;
  }): Promise<TestRun> {
    return this.post<TestRun>('/v1/runs', {
      repo_path: input.repoPath,
      function_name: input.functionName,
      language: input.language,
      framework: input.framework,
      max_retries: input.maxRetries,
      model: input.model,
    });
  }

  async getRun(id: string): Promise<TestRun> {
    return this.get<TestRun>(`/v1/runs/${id}`);
  }

  private async get<T>(path: string): Promise<T> {
    return this.request<T>('GET', path);
  }

  private async post<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>('POST', path, body);
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const headers: Record<string, string> = { 'content-type': 'application/json' };
    if (this.token) {
      headers['authorization'] = `Bearer ${this.token}`;
    }
    const r = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!r.ok) {
      const text = await r.text();
      throw new Error(`CodeIntel API ${r.status} ${path}: ${text}`);
    }
    return (await r.json()) as T;
  }
}

export function clientFromConfig(token: string | undefined): ApiClient {
  const cfg = vscode.workspace.getConfiguration('codeintel');
  return new ApiClient(cfg.get<string>('apiUrl')!, token);
}
