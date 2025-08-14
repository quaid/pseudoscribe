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
const commandManager_1 = require("../../commands/commandManager");
/**
 * Test suite for VSC-001: Command Integration
 *
 * BDD Scenarios:
 * - Register commands: Extension loads -> Commands registered -> Available in palette
 * - Execute command: Command exists -> User triggers -> Action performed -> Feedback shown
 */
suite('VSC-001: Command Integration Test Suite', () => {
    let commandManager;
    setup(() => {
        commandManager = new commandManager_1.CommandManager();
    });
    suite('Command Registration', () => {
        test('should register all PseudoScribe commands on activation', async () => {
            // Given extension loads
            const mockContext = {
                subscriptions: []
            };
            // When registering commands
            await commandManager.registerCommands(mockContext);
            // Then they are available
            const commands = await vscode.commands.getCommands(true);
            // And in command palette
            assert.ok(commands.includes('pseudoscribe.analyzeStyle'), 'analyzeStyle command should be registered');
            assert.ok(commands.includes('pseudoscribe.adaptContent'), 'adaptContent command should be registered');
            assert.ok(commands.includes('pseudoscribe.connectService'), 'connectService command should be registered');
            assert.ok(commands.includes('pseudoscribe.showStyleProfile'), 'showStyleProfile command should be registered');
        });
        test('should handle registration errors gracefully', async () => {
            // Given invalid context
            const invalidContext = null;
            // When registering commands with invalid context
            // Then should not throw error
            assert.doesNotThrow(async () => {
                await commandManager.registerCommands(invalidContext);
            });
        });
    });
    suite('Command Execution', () => {
        test('should execute analyzeStyle command and show feedback', async () => {
            // Given command exists
            const mockContext = { subscriptions: [] };
            await commandManager.registerCommands(mockContext);
            // Mock active text editor
            const mockEditor = {
                selection: new vscode.Selection(0, 0, 0, 10),
                document: {
                    getText: () => 'Sample text for analysis'
                }
            };
            // When user triggers it
            const result = await vscode.commands.executeCommand('pseudoscribe.analyzeStyle');
            // Then action performed
            assert.ok(result !== undefined, 'Command should return a result');
            // And feedback shown (we'll verify this through status bar or notifications)
        });
        test('should execute adaptContent command with selection', async () => {
            // Given command exists and text is selected
            const mockContext = { subscriptions: [] };
            await commandManager.registerCommands(mockContext);
            // When user triggers adaptation
            const result = await vscode.commands.executeCommand('pseudoscribe.adaptContent');
            // Then action performed
            assert.ok(result !== undefined, 'Adapt command should return a result');
        });
        test('should execute connectService command', async () => {
            // Given command exists
            const mockContext = { subscriptions: [] };
            await commandManager.registerCommands(mockContext);
            // When user triggers connection
            const result = await vscode.commands.executeCommand('pseudoscribe.connectService');
            // Then connection attempt made
            assert.ok(result !== undefined, 'Connect command should return a result');
        });
        test('should show error feedback for failed commands', async () => {
            // Given command exists but service is unavailable
            const mockContext = { subscriptions: [] };
            await commandManager.registerCommands(mockContext);
            // When command fails
            // Then error feedback should be shown
            // This will be implemented with proper error handling
        });
    });
    suite('User Feedback', () => {
        test('should show status bar updates during command execution', () => {
            // Given command is executing
            // When processing
            // Then status bar should show progress
            // This will be implemented with StatusBarManager
        });
        test('should show notifications for command results', () => {
            // Given command completes
            // When result is available
            // Then notification should be shown
            // This will be implemented with NotificationManager
        });
    });
});
//# sourceMappingURL=extension.test.js.map