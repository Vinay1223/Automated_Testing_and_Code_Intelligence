# CodeIntel for VS Code / Cursor

Right-click any function -> **CodeIntel: Generate Tests for Function**.
The extension calls the CodeIntel API, streams the generation, validates
the result in a sandbox, and shows you the proposed test file in a
side-by-side diff. One more click opens a GitHub PR.

## Install

* **VS Code Marketplace** — search "CodeIntel"
* **Open VSX** (Cursor) — search "CodeIntel"
* **From source** — `pnpm install && pnpm package` then `code --install-extension codeintel-vscode-*.vsix`

## Sign in

1. Run `CodeIntel: Sign In`.
2. The extension opens the activation URL in your browser and starts an
   OAuth **device flow**. There is no token to paste.
3. Tokens are stored in the VS Code SecretStorage API (Keychain on macOS,
   DPAPI on Windows, libsecret on Linux). The extension never logs them.

## Configure

| Setting | Default | Notes |
|---|---|---|
| `codeintel.apiUrl` | `https://api.codeintel.dev` | Point at your self-hosted instance if needed |
| `codeintel.provider` | `groq` | `mock` / `groq` / `openai` / `anthropic` / `bedrock` |
| `codeintel.maxRetries` | `3` | Self-healing retries before giving up |
| `codeintel.openDiffOnSuccess` | `true` | Show the generated test in a diff |
