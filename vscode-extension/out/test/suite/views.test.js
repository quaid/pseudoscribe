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
const assert = __importStar(require("assert"));
const vscode = __importStar(require("vscode"));
const viewManager_1 = require("../../views/viewManager");
const styleProfileView_1 = require("../../views/styleProfileView");
const contentAnalysisView_1 = require("../../views/contentAnalysisView");
suite('VSC-002: Custom Views Test Suite', () => {
    let viewManager;
    let mockContext;
    setup(() => {
        // Mock extension context
        mockContext = {
            subscriptions: [],
            workspaceState: {
                get: () => undefined,
                update: () => Promise.resolve(),
                keys: () => []
            },
            globalState: {
                get: () => undefined,
                update: () => Promise.resolve(),
                setKeysForSync: () => { },
                keys: () => []
            },
            extensionUri: vscode.Uri.file('/test'),
            extensionPath: '/test',
            asAbsolutePath: (relativePath) => `/test/${relativePath}`,
            storagePath: '/test/storage',
            storageUri: vscode.Uri.file('/test/storage'),
            globalStoragePath: '/test/global',
            globalStorageUri: vscode.Uri.file('/test/global'),
            logPath: '/test/logs',
            logUri: vscode.Uri.file('/test/logs'),
            extensionMode: vscode.ExtensionMode.Test,
            secrets: {},
            environmentVariableCollection: {},
            extension: {},
            languageModelAccessInformation: {}
        };
        viewManager = new viewManager_1.ViewManager(mockContext);
    });
    teardown(() => {
        viewManager?.dispose();
    });
    suite('BDD Scenario: View Creation', () => {
        test('Given extension activates, When loading views, Then panels created', async () => {
            // Given: Extension activates
            assert.ok(viewManager, 'ViewManager should be instantiated');
            // When: Loading views
            await viewManager.initializeViews();
            // Then: Panels created
            const styleView = viewManager.getStyleProfileView();
            const analysisView = viewManager.getContentAnalysisView();
            assert.ok(styleView, 'Style profile view should be created');
            assert.ok(analysisView, 'Content analysis view should be created');
        });
        test('Given extension activates, When loading views, Then properly styled', async () => {
            // Given: Extension activates
            await viewManager.initializeViews();
            // When: Loading views
            const styleView = viewManager.getStyleProfileView();
            // Then: Properly styled
            const webviewContent = await styleView?.getWebviewContent();
            assert.ok(webviewContent?.includes('vscode-dark'), 'Should include VSCode dark theme styles');
            assert.ok(webviewContent?.includes('font-family'), 'Should include proper font styling');
        });
    });
    suite('BDD Scenario: View Updates', () => {
        test('Given view exists, When content changes, Then view refreshes', async () => {
            // Given: View exists
            await viewManager.initializeViews();
            const styleView = viewManager.getStyleProfileView();
            assert.ok(styleView, 'Style view should exist');
            // When: Content changes
            const testData = { style: 'formal', confidence: 0.85 };
            await styleView?.updateContent(testData);
            // Then: View refreshes
            const content = await styleView?.getWebviewContent();
            assert.ok(content?.includes('formal'), 'View should contain updated style data');
            assert.ok(content?.includes('0.85'), 'View should contain updated confidence data');
        });
        test('Given view exists, When content changes, Then smoothly updates', async () => {
            // Given: View exists
            await viewManager.initializeViews();
            const analysisView = viewManager.getContentAnalysisView();
            // When: Content changes (multiple rapid updates)
            const updates = [
                { wordCount: 100, readability: 'easy' },
                { wordCount: 150, readability: 'medium' },
                { wordCount: 200, readability: 'hard' }
            ];
            const startTime = Date.now();
            for (const update of updates) {
                await analysisView?.updateContent(update);
            }
            const endTime = Date.now();
            // Then: Smoothly updates (should complete within reasonable time)
            const updateDuration = endTime - startTime;
            assert.ok(updateDuration < 1000, 'Updates should complete smoothly within 1 second');
            const finalContent = await analysisView?.getWebviewContent();
            assert.ok(finalContent?.includes('200'), 'Final content should reflect last update');
        });
    });
    suite('View Component Tests', () => {
        test('StyleProfileView should initialize with default state', () => {
            const styleView = new styleProfileView_1.StyleProfileView(mockContext);
            assert.ok(styleView, 'StyleProfileView should be created');
            assert.strictEqual(styleView.viewType, 'pseudoscribe.styleProfile', 'Should have correct view type');
        });
        test('ContentAnalysisView should initialize with default state', () => {
            const analysisView = new contentAnalysisView_1.ContentAnalysisView(mockContext);
            assert.ok(analysisView, 'ContentAnalysisView should be created');
            assert.strictEqual(analysisView.viewType, 'pseudoscribe.contentAnalysis', 'Should have correct view type');
        });
        test('Views should handle disposal properly', () => {
            const styleView = new styleProfileView_1.StyleProfileView(mockContext);
            const analysisView = new contentAnalysisView_1.ContentAnalysisView(mockContext);
            // Should not throw when disposing
            assert.doesNotThrow(() => {
                styleView.dispose();
                analysisView.dispose();
            }, 'Views should dispose cleanly');
        });
    });
    suite('View Styling Tests', () => {
        test('Views should apply VSCode theme integration', async () => {
            const styleView = new styleProfileView_1.StyleProfileView(mockContext);
            const content = await styleView.getWebviewContent();
            assert.ok(content.includes('var(--vscode-'), 'Should use VSCode CSS variables');
            assert.ok(content.includes('color-scheme'), 'Should respect color scheme');
        });
        test('Views should be responsive', async () => {
            const analysisView = new contentAnalysisView_1.ContentAnalysisView(mockContext);
            const content = await analysisView.getWebviewContent();
            assert.ok(content.includes('@media'), 'Should include responsive media queries');
            assert.ok(content.includes('flex'), 'Should use flexible layouts');
        });
    });
    suite('Error Handling Tests', () => {
        test('Views should handle update errors gracefully', async () => {
            const styleView = new styleProfileView_1.StyleProfileView(mockContext);
            // Should not throw on invalid data
            assert.doesNotThrow(async () => {
                await styleView.updateContent(null);
                await styleView.updateContent(undefined);
                await styleView.updateContent({});
            }, 'Should handle invalid update data gracefully');
        });
        test('ViewManager should handle view creation failures', async () => {
            // Mock a failure scenario
            const failingContext = { ...mockContext, extensionUri: null };
            const failingManager = new viewManager_1.ViewManager(failingContext);
            // Should not throw during initialization
            assert.doesNotThrow(async () => {
                await failingManager.initializeViews();
            }, 'Should handle view creation failures gracefully');
        });
    });
});
//# sourceMappingURL=views.test.js.map