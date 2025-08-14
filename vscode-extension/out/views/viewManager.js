"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ViewManager = void 0;
const vscode = __importStar(require("vscode"));
const styleProfileView_1 = require("./styleProfileView");
const contentAnalysisView_1 = require("./contentAnalysisView");
/**
 * Manages all custom views for the PseudoScribe extension
 * Handles view lifecycle, registration, and coordination
 */
class ViewManager {
    constructor(context) {
        this.context = context;
        this.disposables = [];
    }
    /**
     * Initialize all custom views
     */
    async initializeViews() {
        try {
            // Create style profile view
            this.styleProfileView = new styleProfileView_1.StyleProfileView(this.context);
            this.disposables.push(this.styleProfileView);
            // Create content analysis view
            this.contentAnalysisView = new contentAnalysisView_1.ContentAnalysisView(this.context);
            this.disposables.push(this.contentAnalysisView);
            // Register view providers
            this.registerViewProviders();
        }
        catch (error) {
            console.error('Failed to initialize views:', error);
            // Don't throw - allow extension to continue functioning
        }
    }
    /**
     * Register view providers with VSCode
     */
    registerViewProviders() {
        if (this.styleProfileView) {
            const styleProvider = vscode.window.registerWebviewViewProvider(this.styleProfileView.viewType, this.styleProfileView, {
                webviewOptions: {
                    retainContextWhenHidden: true
                }
            });
            this.disposables.push(styleProvider);
        }
        if (this.contentAnalysisView) {
            const analysisProvider = vscode.window.registerWebviewViewProvider(this.contentAnalysisView.viewType, this.contentAnalysisView, {
                webviewOptions: {
                    retainContextWhenHidden: true
                }
            });
            this.disposables.push(analysisProvider);
        }
    }
    /**
     * Get the style profile view instance
     */
    getStyleProfileView() {
        return this.styleProfileView;
    }
    /**
     * Get the content analysis view instance
     */
    getContentAnalysisView() {
        return this.contentAnalysisView;
    }
    /**
     * Refresh all views with latest data
     */
    async refreshAllViews() {
        const refreshPromises = [];
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
    async showView(viewType) {
        try {
            await vscode.commands.executeCommand(`${viewType}.focus`);
        }
        catch (error) {
            console.error(`Failed to show view ${viewType}:`, error);
        }
    }
    /**
     * Dispose of all views and resources
     */
    dispose() {
        this.disposables.forEach(disposable => {
            try {
                disposable.dispose();
            }
            catch (error) {
                console.error('Error disposing view resource:', error);
            }
        });
        this.disposables = [];
        this.styleProfileView = undefined;
        this.contentAnalysisView = undefined;
    }
}
exports.ViewManager = ViewManager;
//# sourceMappingURL=viewManager.js.map