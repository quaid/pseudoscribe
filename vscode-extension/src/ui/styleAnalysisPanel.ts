import * as vscode from 'vscode';

/**
 * Style Analysis Panel for displaying style analysis results
 * Part of VSC-004 Advanced Style Features implementation
 */
export class StyleAnalysisPanel {
    public static currentPanel: StyleAnalysisPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private _disposables: vscode.Disposable[] = [];

    public static createOrShow(extensionUri: vscode.Uri) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        // If we already have a panel, show it.
        if (StyleAnalysisPanel.currentPanel) {
            StyleAnalysisPanel.currentPanel._panel.reveal(column);
            return;
        }

        // Otherwise, create a new panel.
        const panel = vscode.window.createWebviewPanel(
            'styleAnalysis',
            'Style Analysis',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(extensionUri, 'media')
                ]
            }
        );

        StyleAnalysisPanel.currentPanel = new StyleAnalysisPanel(panel, extensionUri);
    }

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
        this._panel = panel;

        // Set the webview's initial html content
        this._update();

        // Listen for when the panel is disposed
        // This happens when the user closes the panel or when the panel is closed programmatically
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        // Update the content based on view changes
        this._panel.onDidChangeViewState(
            e => {
                if (this._panel.visible) {
                    this._update();
                }
            },
            null,
            this._disposables
        );

        // Handle messages from the webview
        this._panel.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                    case 'alert':
                        vscode.window.showErrorMessage(message.text);
                        return;
                }
            },
            null,
            this._disposables
        );
    }

    public updateAnalysis(analysisResult: any) {
        this._panel.webview.postMessage({
            command: 'updateAnalysis',
            data: analysisResult
        });
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

    private _update() {
        const webview = this._panel.webview;
        this._panel.title = 'Style Analysis';
        this._panel.webview.html = this._getHtmlForWebview(webview);
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Style Analysis</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 20px;
        }
        .analysis-result {
            margin: 10px 0;
            padding: 15px;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 5px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
        }
        .metric-name {
            font-weight: bold;
        }
        .metric-value {
            color: var(--vscode-textLink-foreground);
        }
        .loading {
            text-align: center;
            color: var(--vscode-descriptionForeground);
        }
    </style>
</head>
<body>
    <h1>Style Analysis Results</h1>
    <div id="content">
        <div class="loading">Waiting for analysis results...</div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        
        window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.command) {
                case 'updateAnalysis':
                    updateAnalysisDisplay(message.data);
                    break;
            }
        });

        function updateAnalysisDisplay(data) {
            const content = document.getElementById('content');
            if (!data) {
                content.innerHTML = '<div class="loading">No analysis data available</div>';
                return;
            }

            let html = '<div class="analysis-result">';
            html += '<h2>Style Characteristics</h2>';
            
            if (data.characteristics) {
                Object.entries(data.characteristics).forEach(([key, value]) => {
                    html += \`<div class="metric">
                        <span class="metric-name">\${key}:</span>
                        <span class="metric-value">\${value}</span>
                    </div>\`;
                });
            }
            
            if (data.suggestions && data.suggestions.length > 0) {
                html += '<h2>Suggestions</h2>';
                data.suggestions.forEach(suggestion => {
                    html += \`<div class="metric">
                        <span class="metric-name">\${suggestion.type}:</span>
                        <span class="metric-value">\${suggestion.text}</span>
                    </div>\`;
                });
            }
            
            html += '</div>';
            content.innerHTML = html;
        }
    </script>
</body>
</html>`;
    }
}
