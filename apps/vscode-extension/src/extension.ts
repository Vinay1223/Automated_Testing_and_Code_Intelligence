/**
 * CodeIntel for VS Code / Cursor — entry point.
 *
 * Registers commands, wires them to the API client, and owns the OAuth
 * device-flow auth state via VS Code's SecretStorage.
 */
import * as vscode from 'vscode';
import { registerGenerateTestsCommand } from './commands/generate-tests';
import { registerScanFileCommand } from './commands/scan-file';
import { registerOpenDashboardCommand } from './commands/open-dashboard';
import { AuthService } from './auth';

export function activate(context: vscode.ExtensionContext): void {
  const output = vscode.window.createOutputChannel('CodeIntel');
  const auth = new AuthService(context.secrets, output);

  context.subscriptions.push(
    output,
    registerGenerateTestsCommand(auth, output),
    registerScanFileCommand(auth, output),
    registerOpenDashboardCommand(),
    vscode.commands.registerCommand('codeintel.signIn', () => auth.signIn()),
    vscode.commands.registerCommand('codeintel.signOut', () => auth.signOut()),
  );

  output.appendLine('CodeIntel extension activated.');
}

export function deactivate(): void {
  /* no-op */
}
