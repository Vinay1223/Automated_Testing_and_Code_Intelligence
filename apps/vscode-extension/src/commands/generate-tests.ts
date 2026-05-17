/**
 * `CodeIntel: Generate Tests for Function`.
 *
 * Heuristic for picking the target function in the active editor:
 * 1. If the user has a non-empty selection, take its first line and parse
 *    out a function name from common Python / TS / JS declarations.
 * 2. Otherwise, walk up from the cursor line looking for the nearest
 *    declaration. (A full AST traversal lives on the server.)
 *
 * The actual heavy lifting (profiling, generation, sandboxing) happens
 * on the API. The client just submits one `function_name` and renders
 * a diff with the result.
 */
import * as vscode from 'vscode';
import { AuthService } from '../auth';
import { clientFromConfig } from '../api-client';

export function registerGenerateTestsCommand(
  auth: AuthService,
  output: vscode.OutputChannel,
): vscode.Disposable {
  return vscode.commands.registerCommand('codeintel.generateTestsForFunction', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showWarningMessage('Open a source file first.');
      return;
    }
    const workspace = vscode.workspace.getWorkspaceFolder(editor.document.uri);
    if (!workspace) {
      vscode.window.showWarningMessage('Function must live inside a workspace folder.');
      return;
    }
    const functionName = detectFunctionName(editor);
    if (!functionName) {
      vscode.window.showWarningMessage('Place the cursor inside a function definition first.');
      return;
    }

    const token = await auth.getToken();
    if (!token) {
      const choice = await vscode.window.showInformationMessage(
        'Sign in to CodeIntel?',
        'Sign in',
      );
      if (choice === 'Sign in') {
        await auth.signIn();
      }
      return;
    }

    const cfg = vscode.workspace.getConfiguration('codeintel');
    const client = clientFromConfig(token);
    const language = detectLanguage(editor.document.languageId);
    const framework = defaultFrameworkFor(language);

    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: `CodeIntel: generating tests for ${functionName}`,
        cancellable: false,
      },
      async () => {
        try {
          const run = await client.createRun({
            repoPath: workspace.uri.fsPath,
            functionName,
            language,
            framework,
            maxRetries: cfg.get<number>('maxRetries') ?? 3,
          });
          if (run.state !== 'passed' || !run.final_test_code) {
            vscode.window.showErrorMessage(
              `CodeIntel could not generate a passing test: ${run.error ?? run.state}`,
            );
            return;
          }
          await openProposedTestDiff(run.final_test_code, run.target, workspace.uri);
          vscode.window.showInformationMessage('Tests generated and validated.');
        } catch (e) {
          output.appendLine(`generateTests: ${(e as Error).message}`);
          vscode.window.showErrorMessage(`CodeIntel failed: ${(e as Error).message}`);
        }
      },
    );
  });
}

const PYTHON_DEF = /^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(/;
const TS_FUNC =
  /^\s*(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(/;
const TS_CONST_ARROW = /^\s*(?:export\s+)?const\s+([A-Za-z_$][\w$]*)\s*[:=].*?=>/;

function detectFunctionName(editor: vscode.TextEditor): string | undefined {
  const doc = editor.document;
  for (let line = editor.selection.active.line; line >= 0; line--) {
    const text = doc.lineAt(line).text;
    const m = text.match(PYTHON_DEF) ?? text.match(TS_FUNC) ?? text.match(TS_CONST_ARROW);
    if (m) {
      return m[1];
    }
  }
  return undefined;
}

function detectLanguage(id: string): 'python' | 'typescript' | 'javascript' {
  if (id === 'python') return 'python';
  if (id === 'javascript' || id === 'javascriptreact') return 'javascript';
  return 'typescript';
}

function defaultFrameworkFor(lang: string): string {
  return lang === 'python' ? 'pytest' : 'jest';
}

async function openProposedTestDiff(
  testCode: string,
  target: { file: string; name: string; language: string },
  workspaceUri: vscode.Uri,
): Promise<void> {
  const isPython = target.language === 'python';
  const filename = isPython ? `test_${target.name}.py` : `${target.name}.test.ts`;
  const proposed = vscode.Uri.joinPath(workspaceUri, 'tests', filename);

  let original = '';
  try {
    const buf = await vscode.workspace.fs.readFile(proposed);
    original = new TextDecoder('utf-8').decode(buf);
  } catch {
    /* file does not exist yet */
  }
  const left = vscode.Uri.parse(`untitled:${proposed.fsPath}.previous`);
  const right = vscode.Uri.parse(`untitled:${proposed.fsPath}`);
  const editLeft = new vscode.WorkspaceEdit();
  editLeft.insert(left, new vscode.Position(0, 0), original);
  const editRight = new vscode.WorkspaceEdit();
  editRight.insert(right, new vscode.Position(0, 0), testCode);
  await vscode.workspace.applyEdit(editLeft);
  await vscode.workspace.applyEdit(editRight);

  await vscode.commands.executeCommand('vscode.diff', left, right, `CodeIntel: ${filename}`);
}
