import * as vscode from 'vscode';

export function registerOpenDashboardCommand(): vscode.Disposable {
  return vscode.commands.registerCommand('codeintel.openDashboard', async () => {
    const url = vscode.workspace
      .getConfiguration('codeintel')
      .get<string>('apiUrl')!
      .replace('api.', 'app.')
      .replace('/api', '');
    await vscode.env.openExternal(vscode.Uri.parse(url));
  });
}
