import * as vscode from 'vscode';
import { ServiceClient } from '../services/serviceClient';
import { StyleAnalysisPanel } from '../ui/styleAnalysisPanel';
import { CacheManager } from '../services/cacheManager';

/**
 * Advanced style analysis commands for VSC-004
 * Implements BDD scenarios for real-time style analysis
 */
export class StyleAnalysisCommands {
    private serviceClient: ServiceClient;
    private cacheManager: CacheManager;
    private analysisPanel: StyleAnalysisPanel | undefined;

    constructor(serviceClient: ServiceClient, context: vscode.ExtensionContext) {
        this.serviceClient = serviceClient;
        this.cacheManager = new CacheManager(context);
        this.analysisPanel = undefined;
    }

    /**
     * Register all style analysis commands
     * BDD: Given the extension is activated, commands should be available
     */
    registerCommands(context: vscode.ExtensionContext): void {
        // Real-time style analysis command
        const analyzeStyleCommand = vscode.commands.registerCommand(
            'pseudoscribe.analyzeStyleAdvanced',
            this.handleAdvancedStyleAnalysis.bind(this)
        );

        // Batch consistency checking command
        const checkConsistencyCommand = vscode.commands.registerCommand(
            'pseudoscribe.checkStyleConsistency',
            this.handleStyleConsistencyCheck.bind(this)
        );

        // Document comparison command
        const compareDocumentsCommand = vscode.commands.registerCommand(
            'pseudoscribe.compareDocumentStyles',
            this.handleDocumentStyleComparison.bind(this)
        );

        context.subscriptions.push(
            analyzeStyleCommand,
            checkConsistencyCommand,
            compareDocumentsCommand
        );
    }

    /**
     * Handle advanced style analysis with detailed panel
     * BDD: When I trigger "Analyze Style", I should see analysis panel within 2 seconds
     */
    private async handleAdvancedStyleAnalysis(): Promise<void> {
        const startTime = Date.now();
        
        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active text editor found');
                return;
            }

            const selection = editor.selection;
            const text = editor.document.getText(selection.isEmpty ? undefined : selection);

            if (!text.trim()) {
                vscode.window.showWarningMessage('No text selected for analysis');
                return;
            }

            // Show progress indicator
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "Analyzing style...",
                cancellable: false
            }, async (progress) => {
                progress.report({ increment: 0 });

                // Check cache first for performance
                const cacheKey = this.generateCacheKey(text);
                let analysis = await this.cacheManager.get(cacheKey);

                if (!analysis) {
                    progress.report({ increment: 30, message: "Contacting analysis service..." });
                    
                    // Call backend API
                    analysis = await this.serviceClient.analyzeStyleDetailed(text);
                    
                    // Cache the result
                    await this.cacheManager.set(cacheKey, analysis, 300000); // 5 minutes TTL
                }

                progress.report({ increment: 70, message: "Preparing results..." });

                // Create or show analysis panel
                const extensionUri = vscode.extensions.getExtension('pseudoscribe.pseudoscribe-writer-assistant')?.extensionUri;
                if (extensionUri) {
                    StyleAnalysisPanel.createOrShow(extensionUri);
                    
                    // Update panel with results
                    if (StyleAnalysisPanel.currentPanel) {
                        StyleAnalysisPanel.currentPanel.updateAnalysis(analysis);
                    }
                }

                progress.report({ increment: 100 });
            });

            // Verify performance requirement: < 2 seconds
            const elapsedTime = Date.now() - startTime;
            if (elapsedTime > 2000) {
                console.warn(`Style analysis took ${elapsedTime}ms, exceeding 2s target`);
            }

        } catch (error) {
            console.error('Style analysis failed:', error);
            vscode.window.showErrorMessage(`Style analysis failed: ${error}`);
        }
    }

    /**
     * Handle batch style consistency checking
     * BDD: When I run "Check Style Consistency", I should see inconsistency report
     */
    private async handleStyleConsistencyCheck(): Promise<void> {
        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active text editor found');
                return;
            }

            const document = editor.document;
            const fullText = document.getText();

            if (!fullText.trim()) {
                vscode.window.showWarningMessage('Document is empty');
                return;
            }

            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "Checking style consistency...",
                cancellable: true
            }, async (progress, token) => {
                // Split document into paragraphs for analysis
                const paragraphs = this.splitIntoParagraphs(fullText);
                const inconsistencies: any[] = [];

                for (let i = 0; i < paragraphs.length; i++) {
                    if (token.isCancellationRequested) {
                        return;
                    }

                    progress.report({ 
                        increment: (i / paragraphs.length) * 100,
                        message: `Analyzing paragraph ${i + 1} of ${paragraphs.length}...`
                    });

                    const paragraph = paragraphs[i];
                    if (paragraph.text.trim().length < 50) continue; // Skip short paragraphs

                    try {
                        const analysis = await this.serviceClient.analyzeStyleDetailed(paragraph.text);
                        
                        // Compare with document baseline (first substantial paragraph)
                        if (i === 0) {
                            // Store baseline for comparison
                            continue;
                        }

                        // Check for inconsistencies (simplified logic)
                        const inconsistency = this.detectInconsistencies(analysis, paragraph);
                        if (inconsistency) {
                            inconsistencies.push({
                                ...inconsistency,
                                line: paragraph.startLine,
                                text: paragraph.text.substring(0, 100) + '...'
                            });
                        }
                    } catch (error) {
                        console.warn(`Failed to analyze paragraph ${i}:`, error);
                    }
                }

                // Display results
                if (inconsistencies.length > 0) {
                    this.showConsistencyReport(inconsistencies);
                } else {
                    vscode.window.showInformationMessage('No style inconsistencies detected!');
                }
            });

        } catch (error) {
            console.error('Consistency check failed:', error);
            vscode.window.showErrorMessage(`Consistency check failed: ${error}`);
        }
    }

    /**
     * Handle document style comparison
     * BDD: When I select "Compare Document Styles", I should see side-by-side comparison
     */
    private async handleDocumentStyleComparison(): Promise<void> {
        try {
            const openEditors = vscode.window.visibleTextEditors;
            
            if (openEditors.length < 2) {
                vscode.window.showErrorMessage('Please open at least two documents to compare');
                return;
            }

            // Let user select which documents to compare
            const documentOptions = openEditors.map((editor, index) => ({
                label: editor.document.fileName.split('/').pop() || `Document ${index + 1}`,
                description: editor.document.fileName,
                editor: editor
            }));

            const firstDoc = await vscode.window.showQuickPick(documentOptions, {
                placeHolder: 'Select first document to compare'
            });

            if (!firstDoc) return;

            const secondDocOptions = documentOptions.filter(doc => doc.editor !== firstDoc.editor);
            const secondDoc = await vscode.window.showQuickPick(secondDocOptions, {
                placeHolder: 'Select second document to compare'
            });

            if (!secondDoc) return;

            // Perform comparison
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "Comparing document styles...",
                cancellable: false
            }, async (progress) => {
                progress.report({ increment: 0 });

                const text1 = firstDoc.editor.document.getText();
                const text2 = secondDoc.editor.document.getText();

                progress.report({ increment: 30, message: "Analyzing first document..." });
                const analysis1 = await this.serviceClient.analyzeStyleDetailed(text1);

                progress.report({ increment: 60, message: "Analyzing second document..." });
                const analysis2 = await this.serviceClient.analyzeStyleDetailed(text2);

                progress.report({ increment: 90, message: "Comparing styles..." });
                const comparison = await this.serviceClient.compareStyles(text1, text2);

                progress.report({ increment: 100 });

                // Show comparison results
                this.showStyleComparison(firstDoc.label, secondDoc.label, analysis1, analysis2, comparison);
            });

        } catch (error) {
            console.error('Document comparison failed:', error);
            vscode.window.showErrorMessage(`Document comparison failed: ${error}`);
        }
    }

    /**
     * Generate cache key for text analysis
     */
    private generateCacheKey(text: string): string {
        // Simple hash function for cache key
        let hash = 0;
        for (let i = 0; i < text.length; i++) {
            const char = text.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return `style_analysis_${hash}`;
    }

    /**
     * Split document into paragraphs with line information
     */
    private splitIntoParagraphs(text: string): Array<{text: string, startLine: number}> {
        const lines = text.split('\n');
        const paragraphs: Array<{text: string, startLine: number}> = [];
        let currentParagraph = '';
        let startLine = 0;

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            if (line === '') {
                if (currentParagraph.trim()) {
                    paragraphs.push({
                        text: currentParagraph.trim(),
                        startLine: startLine
                    });
                    currentParagraph = '';
                }
                startLine = i + 1;
            } else {
                currentParagraph += line + ' ';
            }
        }

        // Add final paragraph if exists
        if (currentParagraph.trim()) {
            paragraphs.push({
                text: currentParagraph.trim(),
                startLine: startLine
            });
        }

        return paragraphs;
    }

    /**
     * Detect style inconsistencies (simplified implementation)
     */
    private detectInconsistencies(analysis: any, paragraph: any): any | null {
        // This would contain more sophisticated logic in a real implementation
        // For now, return null (no inconsistencies detected)
        return null;
    }

    /**
     * Show consistency report in a new panel
     */
    private showConsistencyReport(inconsistencies: any[]): void {
        const panel = vscode.window.createWebviewPanel(
            'consistencyReport',
            'Style Consistency Report',
            vscode.ViewColumn.Beside,
            { enableScripts: true }
        );

        // Generate HTML content for the report
        const html = this.generateConsistencyReportHtml(inconsistencies);
        panel.webview.html = html;
    }

    /**
     * Show style comparison in a new panel
     */
    private showStyleComparison(doc1Name: string, doc2Name: string, analysis1: any, analysis2: any, comparison: any): void {
        const panel = vscode.window.createWebviewPanel(
            'styleComparison',
            'Document Style Comparison',
            vscode.ViewColumn.Beside,
            { enableScripts: true }
        );

        // Generate HTML content for the comparison
        const html = this.generateComparisonHtml(doc1Name, doc2Name, analysis1, analysis2, comparison);
        panel.webview.html = html;
    }

    /**
     * Generate HTML for consistency report
     */
    private generateConsistencyReportHtml(inconsistencies: any[]): string {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Style Consistency Report</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    .inconsistency { margin: 10px 0; padding: 10px; border-left: 3px solid #ff6b6b; }
                    .line-number { font-weight: bold; color: #666; }
                </style>
            </head>
            <body>
                <h1>Style Consistency Report</h1>
                <p>Found ${inconsistencies.length} potential inconsistencies:</p>
                ${inconsistencies.map(inc => `
                    <div class="inconsistency">
                        <div class="line-number">Line ${inc.line}</div>
                        <div>${inc.text}</div>
                        <div><strong>Issue:</strong> ${inc.description}</div>
                    </div>
                `).join('')}
            </body>
            </html>
        `;
    }

    /**
     * Generate HTML for style comparison
     */
    private generateComparisonHtml(doc1Name: string, doc2Name: string, analysis1: any, analysis2: any, comparison: any): string {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Document Style Comparison</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    .comparison-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
                    .document { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
                    .similarity-score { font-size: 24px; font-weight: bold; text-align: center; margin: 20px 0; }
                </style>
            </head>
            <body>
                <h1>Document Style Comparison</h1>
                <div class="similarity-score">
                    Overall Similarity: ${(comparison.overall_similarity * 100).toFixed(1)}%
                </div>
                <div class="comparison-grid">
                    <div class="document">
                        <h2>${doc1Name}</h2>
                        <p><strong>Complexity:</strong> ${analysis1.complexity?.toFixed(2) || 'N/A'}</p>
                        <p><strong>Formality:</strong> ${analysis1.formality?.toFixed(2) || 'N/A'}</p>
                        <p><strong>Tone:</strong> ${analysis1.tone?.toFixed(2) || 'N/A'}</p>
                        <p><strong>Readability:</strong> ${analysis1.readability?.toFixed(2) || 'N/A'}</p>
                    </div>
                    <div class="document">
                        <h2>${doc2Name}</h2>
                        <p><strong>Complexity:</strong> ${analysis2.complexity?.toFixed(2) || 'N/A'}</p>
                        <p><strong>Formality:</strong> ${analysis2.formality?.toFixed(2) || 'N/A'}</p>
                        <p><strong>Tone:</strong> ${analysis2.tone?.toFixed(2) || 'N/A'}</p>
                        <p><strong>Readability:</strong> ${analysis2.readability?.toFixed(2) || 'N/A'}</p>
                    </div>
                </div>
            </body>
            </html>
        `;
    }

    /**
     * Dispose of resources
     */
    dispose(): void {
        if (this.analysisPanel) {
            this.analysisPanel.dispose();
        }
    }
}
