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
//# sourceMappingURL=extension.test.js.map