import * as vscode from 'vscode';

/**
 * Content Analysis View - displays document analysis metrics and insights
 */
export class ContentAnalysisView implements vscode.WebviewViewProvider, vscode.Disposable {
    public static readonly viewType = 'pseudoscribe.contentAnalysis';
    public readonly viewType = ContentAnalysisView.viewType;

    private _view?: vscode.WebviewView;
    private _currentData: any = null;

    constructor(private readonly _context: vscode.ExtensionContext) {}

    /**
     * Resolve the webview view
     */
    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        token: vscode.CancellationToken,
    ): void {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._context.extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(
            message => {
                switch (message.type) {
                    case 'refresh':
                        this.refresh();
                    case 'analyze':
                        vscode.commands.executeCommand('pseudoscribe.adaptContent');
                        break;
                }
            },
            undefined,
            this._context.subscriptions
        );
    }

    /**
     * Update view content with new data
     */
    async updateContent(data: any): Promise<void> {
        if (!data) {
            return;
        }
        this._currentData = data;
        if (this._view) {
            this._view.webview.html = this._getHtmlForWebview(this._view.webview);
        }
    }

    /**
     * Refresh the view
     */
    async refresh(): Promise<void> {
        if (this._view) {
            this._view.webview.html = this._getHtmlForWebview(this._view.webview);
        }
    }

    /**
     * Get webview content
     */
    async getWebviewContent(): Promise<string> {
        return this._getHtmlForWebview(this._view?.webview as vscode.Webview);
    }

    private _renderContent(): string {
        if (!this._currentData || Object.keys(this._currentData).length === 0) {
            return `
                <div class="empty-state">
                    <p>No content analysis available</p>
                    <button class="analyze-btn" onclick="analyze()">Analyze Current Document</button>
                </div>
            `;
        }

        const wordCount = this._currentData.wordCount || 0;
        const readability = this._currentData.readability || 'unknown';
        const sentences = this._currentData.sentences || 0;
        const paragraphs = this._currentData.paragraphs || 0;
        
        const readabilityClass = `readability-${readability.toLowerCase()}`;
        const readabilityText = readability.charAt(0).toUpperCase() + readability.slice(1);

        return `
            <div class="metrics-grid">
                <div class="metric-card">
                    <span class="metric-value">${wordCount}</span>
                    <div class="metric-label">Words</div>
                </div>
                <div class="metric-card">
                    <span class="metric-value">${sentences}</span>
                    <div class="metric-label">Sentences</div>
                </div>
                <div class="metric-card">
                    <span class="metric-value">${paragraphs}</span>
                    <div class="metric-label">Paragraphs</div>
                </div>
            </div>
            
            <div class="readability-section">
                <div class="readability-header">Readability</div>
                <div class="readability-indicator">
                    <div class="readability-dot ${readabilityClass}"></div>
                    <span>${readabilityText}</span>
                </div>
            </div>
            
            <button class="analyze-btn" onclick="analyze()">Re-analyze Document</button>
        `;
    }

    private _getHtmlForWebview(webview: vscode.Webview): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Content Analysis</title>
    <style>
        :root {
            --vscode-font-family: var(--vscode-font-family);
            --vscode-font-size: var(--vscode-font-size);
        }
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            margin: 0;
            padding: 16px;
            color-scheme: var(--vscode-color-scheme);
        }
        .container {
            display: flex;
            flex-direction: column;
            gap: 16px;
            max-width: 100%;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--vscode-panel-border);
        }
        .title {
            font-weight: bold;
            font-size: 1.1em;
        }
        .refresh-btn {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 4px 8px;
            border-radius: 2px;
            cursor: pointer;
            font-size: 0.9em;
        }
        .refresh-btn:hover {
            background: var(--vscode-button-hoverBackground);
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
        }
        .metric-card {
            background: var(--vscode-editor-inactiveSelectionBackground);
            padding: 12px;
            border-radius: 4px;
            border: 1px solid var(--vscode-panel-border);
            text-align: center;
        }
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: var(--vscode-textLink-foreground);
            display: block;
        }
        .metric-label {
            font-size: 0.85em;
            color: var(--vscode-descriptionForeground);
            margin-top: 4px;
        }
        .readability-section {
            background: var(--vscode-editor-inactiveSelectionBackground);
            padding: 12px;
            border-radius: 4px;
            border: 1px solid var(--vscode-panel-border);
        }
        .readability-header {
            font-weight: 500;
            margin-bottom: 8px;
        }
        .readability-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .readability-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        .readability-easy { background-color: #4CAF50; }
        .readability-medium { background-color: #FF9800; }
        .readability-hard { background-color: #F44336; }
        .analyze-btn {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 8px 16px;
            border-radius: 2px;
            cursor: pointer;
            width: 100%;
            margin-top: 8px;
        }
        .analyze-btn:hover {
            background: var(--vscode-button-hoverBackground);
        }
        .empty-state {
            text-align: center;
            color: var(--vscode-descriptionForeground);
            padding: 24px;
        }
        @media (max-width: 300px) {
            .container {
                padding: 8px;
            }
            .metrics-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">Content Analysis</div>
            <button class="refresh-btn" onclick="refresh()">↻</button>
        </div>
        <div id="content">
            ${this._renderContent()}
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        
        function refresh() {
            vscode.postMessage({ type: 'refresh' });
        }
        
        function analyze() {
            vscode.postMessage({ type: 'analyze' });
        }
    </script>
</body>
</html>`;
    }

    dispose(): void {
        this._view = undefined;
        this._currentData = null;
    }
}
