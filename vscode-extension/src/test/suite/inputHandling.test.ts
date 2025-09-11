import * as assert from 'assert';
import * as vscode from 'vscode';
import { InputManager } from '../../input/inputManager';

suite('VSC-003: Input Handling Test Suite', () => {
    let inputManager: InputManager;

    suiteSetup(() => {
        inputManager = global.extensionApi.inputManager!;
    });

    suite('BDD Scenario: Keyboard Shortcuts', () => {
        test('Given shortcut registered, When user presses keys, Then action triggered', async () => {
            assert.ok(inputManager, 'InputManager should be available from global API');
            const shortcutHandler = inputManager.getShortcutHandler();
            assert.ok(shortcutHandler, 'Shortcut handler should be registered');

            const mockCommand = 'pseudoscribe.quickAnalyze';
            const commands = await vscode.commands.getCommands(true);
            const isRegistered = commands.includes(mockCommand);
            
            assert.ok(isRegistered, `Command ${mockCommand} should be registered`);
        });
    });

    suite('BDD Scenario: Context Menus', () => {
        test('Given right-click event, When menu opens, Then options shown', () => {
            assert.ok(inputManager, 'InputManager should be available from global API');
            const contextMenuProvider = inputManager.getContextMenuProvider();
            assert.ok(contextMenuProvider, 'Context menu provider should be registered');

            const menuItems = contextMenuProvider.getMenuItems();
            
            assert.ok(Array.isArray(menuItems), 'Menu items should be an array');
            assert.ok(menuItems.length > 0, 'Should have at least one menu item');
            
            const hasAnalyzeOption = menuItems.some(item => item.command === 'pseudoscribe.analyzeStyle');
            const hasAdaptOption = menuItems.some(item => item.command === 'pseudoscribe.adaptContent');
            
            assert.ok(hasAnalyzeOption, 'Should have analyze style option');
            assert.ok(hasAdaptOption, 'Should have adapt content option');
        });
    });

    suite('Input Handling Integration Tests', () => {
        test('InputManager should coordinate all input methods', () => {
            assert.ok(inputManager, 'InputManager should be available from global API');
            assert.ok(inputManager.getShortcutHandler(), 'Shortcut handler should be initialized');
            assert.ok(inputManager.getContextMenuProvider(), 'Context menu provider should be initialized');
        });
    });
});
