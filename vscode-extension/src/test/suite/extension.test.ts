import * as assert from 'assert';
import * as vscode from 'vscode';

suite('VSC-001: Extension Activation and Command Integration', () => {

    test('should register commands on activation', async function () {
        this.timeout(5000);
        // The extension is activated globally in test/suite/index.ts.
        // This test verifies that the commands are available after activation.
        const commands = await vscode.commands.getCommands(true);
        
        assert.ok(commands.includes('pseudoscribe.analyzeStyle'), 'analyzeStyle command should be registered');
        assert.ok(commands.includes('pseudoscribe.adaptContent'), 'adaptContent command should be registered');
        assert.ok(commands.includes('pseudoscribe.connectService'), 'connectService command should be registered');
    });

    test('should make managers available via the extension API', () => {
        // The global setup in test/suite/index.ts should capture the extension's API.
        assert.ok(global.extensionApi, 'Extension API should be available globally');
        assert.ok(global.extensionApi.viewManager, 'ViewManager should be available via the API');
        assert.ok(global.extensionApi.inputManager, 'InputManager should be available via the API');
    });
});
