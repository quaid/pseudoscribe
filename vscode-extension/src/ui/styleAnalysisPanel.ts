import * as vscode from 'vscode';

/**
 * StyleAnalysisPanel manages the webview panel for displaying style analysis results
 */
export class StyleAnalysisPanel {
    public static currentPanel: StyleAnalysisPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private _disposables: vscode.Disposable[] = [];

    public static createOrShow(extensionUri: vscode.Uri, analysisData: any) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        // If we already have a panel, show it
        if (StyleAnalysisPanel.currentPanel) {
            StyleAnalysisPanel.currentPanel._panel.reveal(column);
            StyleAnalysisPanel.currentPanel.updateContent(analysisData);
            return;
        }

        // Otherwise, create a new panel
        const panel = vscode.window.createWebviewPanel(
            'styleAnalysis',
            'Style Analysis',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(extensionUri, 'media'),
                    vscode.Uri.joinPath(extensionUri, 'out', 'compiled')
                ]
            }
        );

        StyleAnalysisPanel.currentPanel = new StyleAnalysisPanel(panel, extensionUri, analysisData);
    }

    public static kill() {
        StyleAnalysisPanel.currentPanel?.dispose();
        StyleAnalysisPanel.currentPanel = undefined;
    }

    public static revive(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
        StyleAnalysisPanel.currentPanel = new StyleAnalysisPanel(panel, extensionUri, {});
    }

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri, analysisData: any) {
        this._panel = panel;
        this.updateContent(analysisData);
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
    }

    public updateContent(analysisData: any) {
        const webview = this._panel.webview;
        this._panel.webview.html = this._getHtmlForWebview(webview, analysisData);
    }

    public updateAnalysis(analysis: any, text: string) {
        this.updateContent({ analysis, text });
    }

    public show() {
        this._panel.reveal();
    }

    public dispose() {
        StyleAnalysisPanel.currentPanel = undefined;

        // Clean up our resources
        this._panel.dispose();

        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }

    private _getHtmlForWebview(webview: vscode.Webview, analysisData: any) {
        // Use a nonce to only allow specific scripts to be run
        const nonce = getNonce();

        const styleData = analysisData || {};
        const metrics = styleData.metrics || {};
        const suggestions = styleData.suggestions || [];

        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${nonce}';">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Style Analysis Results</title>
                <style>
                    body {
                        font-family: var(--vscode-font-family);
                        font-size: var(--vscode-font-size);
                        color: var(--vscode-foreground);
                        background-color: var(--vscode-editor-background);
                        padding: 20px;
                        line-height: 1.6;
                    }
                    .metric-card {
                        background-color: var(--vscode-editor-inactiveSelectionBackground);
                        border: 1px solid var(--vscode-panel-border);
                        border-radius: 8px;
                        padding: 16px;
                        margin: 12px 0;
                    }
                    .metric-title {
                        font-weight: bold;
                        color: var(--vscode-textLink-foreground);
                        margin-bottom: 8px;
                    }
                    .metric-value {
                        font-size: 1.2em;
                        margin-bottom: 4px;
                    }
                    .suggestions {
                        margin-top: 20px;
                    }
                    .suggestion-item {
                        background-color: var(--vscode-textBlockQuote-background);
                        border-left: 4px solid var(--vscode-textLink-foreground);
                        padding: 12px;
                        margin: 8px 0;
                    }
                    .suggestion-type {
                        font-weight: bold;
                        color: var(--vscode-textLink-foreground);
                        text-transform: capitalize;
                    }
                    .progress-bar {
                        width: 100%;
                        height: 8px;
                        background-color: var(--vscode-progressBar-background);
                        border-radius: 4px;
                        overflow: hidden;
                        margin: 8px 0;
                    }
                    .progress-fill {
                        height: 100%;
                        background-color: var(--vscode-progressBar-foreground);
                        transition: width 0.3s ease;
                    }
                </style>
            </head>
            <body>
                <h1>Style Analysis Results</h1>
                
                <div class="metrics">
                    <h2>Style Metrics</h2>
                    
                    <div class="metric-card">
                        <div class="metric-title">Complexity</div>
                        <div class="metric-value">${(metrics.complexity || 0).toFixed(2)}</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${(metrics.complexity || 0) * 100}%"></div>
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">Formality</div>
                        <div class="metric-value">${(metrics.formality || 0).toFixed(2)}</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${(metrics.formality || 0) * 100}%"></div>
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">Tone</div>
                        <div class="metric-value">${(metrics.tone || 0).toFixed(2)}</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${(metrics.tone || 0) * 100}%"></div>
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">Readability</div>
                        <div class="metric-value">${(metrics.readability || 0).toFixed(2)}</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${(metrics.readability || 0) * 100}%"></div>
                        </div>
                    </div>
                </div>

                ${suggestions.length > 0 ? `
                <div class="suggestions">
                    <h2>Suggestions</h2>
                    ${suggestions.map((suggestion: any) => `
                        <div class="suggestion-item">
                            <div class="suggestion-type">${suggestion.type || 'General'}</div>
                            <div>${suggestion.text || suggestion.message || 'No description available'}</div>
                        </div>
                    `).join('')}
                </div>
                ` : ''}

                <script nonce="${nonce}">
                    // Add any interactive functionality here
                    console.log('Style Analysis Panel loaded');
                </script>
            </body>
            </html>`;
    }
}

function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}
