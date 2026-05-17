/**
 * OAuth device-flow authentication.
 *
 * 1. POST /oauth/device -> { device_code, user_code, verification_uri, interval }
 * 2. Open verification_uri in the browser.
 * 3. Poll /oauth/token until the user approves, then stash the JWT in
 *    SecretStorage.
 */
import * as vscode from 'vscode';

const TOKEN_KEY = 'codeintel.jwt';

export class AuthService {
  constructor(
    private readonly secrets: vscode.SecretStorage,
    private readonly output: vscode.OutputChannel,
  ) {}

  async getToken(): Promise<string | undefined> {
    return this.secrets.get(TOKEN_KEY);
  }

  async signIn(): Promise<void> {
    const apiUrl = vscode.workspace.getConfiguration('codeintel').get<string>('apiUrl')!;
    let device: DeviceResponse;
    try {
      device = await postJson(`${apiUrl}/oauth/device`, {});
    } catch (e) {
      vscode.window.showErrorMessage(`CodeIntel sign-in failed: ${(e as Error).message}`);
      return;
    }
    await vscode.env.openExternal(vscode.Uri.parse(device.verification_uri));
    vscode.window.showInformationMessage(
      `Enter code ${device.user_code} in your browser to finish signing in.`,
    );
    const token = await pollForToken(apiUrl, device, this.output);
    if (token) {
      await this.secrets.store(TOKEN_KEY, token);
      vscode.window.showInformationMessage('CodeIntel signed in.');
    }
  }

  async signOut(): Promise<void> {
    await this.secrets.delete(TOKEN_KEY);
    vscode.window.showInformationMessage('CodeIntel signed out.');
  }
}

interface DeviceResponse {
  device_code: string;
  user_code: string;
  verification_uri: string;
  interval: number;
  expires_in: number;
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    throw new Error(`${r.status} ${await r.text()}`);
  }
  return (await r.json()) as T;
}

async function pollForToken(
  apiUrl: string,
  device: DeviceResponse,
  output: vscode.OutputChannel,
): Promise<string | undefined> {
  const start = Date.now();
  while (Date.now() - start < device.expires_in * 1000) {
    await sleep(device.interval * 1000);
    try {
      const r = await fetch(`${apiUrl}/oauth/token`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ device_code: device.device_code }),
      });
      if (r.status === 200) {
        const data = (await r.json()) as { access_token: string };
        return data.access_token;
      }
      if (r.status !== 425 && r.status !== 428) {
        output.appendLine(`token poll: ${r.status} ${await r.text()}`);
      }
    } catch (e) {
      output.appendLine(`token poll error: ${(e as Error).message}`);
    }
  }
  return undefined;
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}
