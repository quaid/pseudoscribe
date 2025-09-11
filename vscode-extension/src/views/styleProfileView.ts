import * as vscode from 'vscode';

/**
 * Style Profile View - displays writing style analysis and profiles
 */
export class StyleProfileView implements vscode.WebviewViewProvider, vscode.Disposable {
    public static readonly viewType = 'pseudoscribe.styleProfile';
    public readonly viewType = StyleProfileView.viewType;

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
                        break;
                    case 'analyze':
                        vscode.commands.executeCommand('pseudoscribe.analyzeStyle');
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

    /**
     * Generate HTML content for the webview
     */
    private _renderContent(): string {
        if (!this._currentData || Object.keys(this._currentData).length === 0) {
            return `
                <div class="empty-state">
                    <p>No style analysis available</p>
                    <button class="analyze-btn" onclick="analyze()">Analyze Current Document</button>
                </div>
            `;
        }

        const style = this._currentData.style || 'Unknown';
        const confidence = this._currentData.confidence || 0;
        const confidencePercent = Math.round(confidence * 100);

        return `
            <div class="profile-section">
                <div class="profile-item">
                    <span class="profile-label">Style:</span>
                    <span class="profile-value">${style}</span>
                </div>
                <div class="profile-item">
                    <span class="profile-label">Confidence:</span>
                    <span class="profile-value">${confidencePercent}%</span>
                </div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${confidencePercent}%"></div>
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
    <title>Style Profile</title>
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
        
        .profile-section {
            background: var(--vscode-editor-inactiveSelectionBackground);
            padding: 12px;
            border-radius: 4px;
            border: 1px solid var(--vscode-panel-border);
        }
        
        .profile-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        
        .profile-item:last-child {
            margin-bottom: 0;
        }
        
        .profile-label {
            font-weight: 500;
        }
        
        .profile-value {
            color: var(--vscode-textLink-foreground);
        }
        
        .confidence-bar {
            width: 100%;
            height: 4px;
            background: var(--vscode-progressBar-background);
            border-radius: 2px;
            overflow: hidden;
            margin-top: 4px;
        }
        
        .confidence-fill {
            height: 100%;
            background: var(--vscode-progressBar-background);
            transition: width 0.3s ease;
        }
        
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
            
            .profile-item {
                flex-direction: column;
                gap: 4px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">Style Profile</div>
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

    /**
     * Dispose of resources
     */
    dispose(): void {
        this._view = undefined;
        this._currentData = null;
    }
}
