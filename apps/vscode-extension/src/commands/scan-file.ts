/**
 * `CodeIntel: Scan File for Uncovered Functions`.
 *
 * Posts to /v1/scans and shows the uncovered functions in a QuickPick.
 * Picking one immediately runs `codeintel.generateTestsForFunction`.
 */
import * as vscode from 'vscode';
import { AuthService } from '../auth';
import { clientFromConfig } from '../api-client';

export function registerScanFileCommand(
  auth: AuthService,
  output: vscode.OutputChannel,
): vscode.Disposable {
  return vscode.commands.registerCommand('codeintel.scanFile', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showWarningMessage('Open a source file first.');
      return;
    }
    const folder = vscode.workspace.getWorkspaceFolder(editor.document.uri);
    if (!folder) {
      return;
    }
    const token = await auth.getToken();
    if (!token) {
      vscode.window.showWarningMessage('Run "CodeIntel: Sign In" first.');
      return;
    }

    const client = clientFromConfig(token);
    try {
      const result = await client.scan(folder.uri.fsPath);
      const items = result.targets
        .filter((t) => t.file.endsWith(editor.document.fileName.split(/[\\/]/).pop()!))
        .map((t) => ({ label: t.name, description: t.qualified_name, target: t }));
      if (items.length === 0) {
        vscode.window.showInformationMessage('No testable functions in this file.');
        return;
      }
      const pick = await vscode.window.showQuickPick(items, {
        title: `CodeIntel — ${result.total} functions scanned (${result.coverage_pct}% covered)`,
      });
      if (pick) {
        await vscode.commands.executeCommand('codeintel.generateTestsForFunction');
      }
    } catch (e) {
      output.appendLine(`scanFile: ${(e as Error).message}`);
      vscode.window.showErrorMessage(`CodeIntel scan failed: ${(e as Error).message}`);
    }
  });
}
