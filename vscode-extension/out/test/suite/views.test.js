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
suite('VSC-002: Custom Views Test Suite', () => {
    let viewManager;
    suiteSetup(() => {
        viewManager = global.extensionApi.viewManager;
    });
    suite('BDD Scenario: View Creation', () => {
        test('Given extension activates, When loading views, Then panels created', () => {
            assert.ok(viewManager, 'ViewManager should be available from global API');
            const styleView = viewManager.getStyleProfileView();
            const analysisView = viewManager.getContentAnalysisView();
            assert.ok(styleView, 'Style profile view should be created');
            assert.ok(analysisView, 'Content analysis view should be created');
        });
        test('Given extension activates, When loading views, Then properly styled', async () => {
            const styleView = viewManager.getStyleProfileView();
            assert.ok(styleView, 'Style profile view should be available');
            const webviewContent = await styleView.getWebviewContent();
            assert.ok(webviewContent, 'Webview content should not be null');
            assert.ok(webviewContent.includes('var(--vscode-editor-background)'), 'Should include VSCode theme variables');
        });
    });
    suite('BDD Scenario: View Updates', () => {
        test('Given view exists, When content changes, Then view refreshes', async () => {
            const styleView = viewManager.getStyleProfileView();
            assert.ok(styleView, 'Style view should exist');
            const testData = { style: 'Updated Style', confidence: 0.9 };
            await styleView.updateContent(testData);
            const content = await styleView.getWebviewContent();
            assert.ok(content, 'Webview content should not be null');
            assert.ok(content.includes('Updated Style'), 'View should contain updated style data');
            assert.ok(content.includes('90%'), 'View should contain updated confidence data');
        });
        test('Given view exists, When content changes, Then smoothly updates', async () => {
            const analysisView = viewManager.getContentAnalysisView();
            assert.ok(analysisView, 'Analysis view should exist');
            const updates = [
                { wordCount: 100, readability: 'easy' },
                { wordCount: 150, readability: 'medium' },
                { wordCount: 200, readability: 'hard' }
            ];
            const startTime = Date.now();
            for (const update of updates) {
                await analysisView.updateContent(update);
            }
            const endTime = Date.now();
            const updateDuration = endTime - startTime;
            assert.ok(updateDuration < 1000, 'Updates should complete smoothly within 1 second');
            const finalContent = await analysisView.getWebviewContent();
            assert.ok(finalContent, 'Final webview content should not be null');
            assert.ok(finalContent.includes('200'), 'Final content should reflect last update');
        });
    });
});
//# sourceMappingURL=views.test.js.map