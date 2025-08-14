import * as vscode from 'vscode';
import { StyleProfileView } from './styleProfileView';
import { ContentAnalysisView } from './contentAnalysisView';

/**
 * Manages all custom views for the PseudoScribe extension
 * Handles view lifecycle, registration, and coordination
 */
export class ViewManager implements vscode.Disposable {
    private styleProfileView: StyleProfileView | undefined;
    private contentAnalysisView: ContentAnalysisView | undefined;
    private disposables: vscode.Disposable[] = [];

    constructor(private context: vscode.ExtensionContext) {}

    /**
     * Initialize all custom views
     */
    async initializeViews(): Promise<void> {
        try {
            // Create style profile view
            this.styleProfileView = new StyleProfileView(this.context);
            this.disposables.push(this.styleProfileView);

            // Create content analysis view
            this.contentAnalysisView = new ContentAnalysisView(this.context);
            this.disposables.push(this.contentAnalysisView);

            // Register view providers
            this.registerViewProviders();
        } catch (error) {
            console.error('Failed to initialize views:', error);
            // Don't throw - allow extension to continue functioning
        }
    }

    /**
     * Register view providers with VSCode
     */
    private registerViewProviders(): void {
        if (this.styleProfileView) {
            const styleProvider = vscode.window.registerWebviewViewProvider(
                this.styleProfileView.viewType,
                this.styleProfileView,
                {
                    webviewOptions: {
                        retainContextWhenHidden: true
                    }
                }
            );
            this.disposables.push(styleProvider);
        }

        if (this.contentAnalysisView) {
            const analysisProvider = vscode.window.registerWebviewViewProvider(
                this.contentAnalysisView.viewType,
                this.contentAnalysisView,
                {
                    webviewOptions: {
                        retainContextWhenHidden: true
                    }
                }
            );
            this.disposables.push(analysisProvider);
        }
    }

    /**
     * Get the style profile view instance
     */
    getStyleProfileView(): StyleProfileView | undefined {
        return this.styleProfileView;
    }

    /**
     * Get the content analysis view instance
     */
    getContentAnalysisView(): ContentAnalysisView | undefined {
        return this.contentAnalysisView;
    }

    /**
     * Refresh all views with latest data
     */
    async refreshAllViews(): Promise<void> {
        const refreshPromises: Promise<void>[] = [];

        if (this.styleProfileView) {
            refreshPromises.push(this.styleProfileView.refresh());
        }

        if (this.contentAnalysisView) {
            refreshPromises.push(this.contentAnalysisView.refresh());
        }

        await Promise.all(refreshPromises);
    }

    /**
     * Show a specific view
     */
    async showView(viewType: string): Promise<void> {
        try {
            await vscode.commands.executeCommand(`${viewType}.focus`);
        } catch (error) {
            console.error(`Failed to show view ${viewType}:`, error);
        }
    }

    /**
     * Dispose of all views and resources
     */
    dispose(): void {
        this.disposables.forEach(disposable => {
            try {
                disposable.dispose();
            } catch (error) {
                console.error('Error disposing view resource:', error);
            }
        });
        this.disposables = [];
        this.styleProfileView = undefined;
        this.contentAnalysisView = undefined;
    }
}
