import * as vscode from 'vscode';
import { CommandManager } from './commands/commandManager';
import { ViewManager } from './views/viewManager';
import { InputManager } from './input/inputManager';
import { TokenManager } from './auth/tokenManager';
import { ServiceClient } from './services/serviceClient';

/**
 * Handles the core activation logic of the extension.
 * This function is designed to be testable by allowing dependency injection.
 */
export async function handleActivation(
    context: vscode.ExtensionContext,
    tokenManager: TokenManager,
    serviceClient: ServiceClient,
    commandManager: CommandManager,
    viewManager: ViewManager,
    inputManager: InputManager
) {
    await commandManager.registerCommands(context);

    const token = await tokenManager.getToken();
    if (!token) {
        vscode.commands.executeCommand('pseudoscribe.setApiToken');
    }

    await viewManager.initializeViews();
    await inputManager.initialize();
    await inputManager.registerShortcuts();
    await inputManager.registerContextMenus();

    vscode.commands.executeCommand('setContext', 'pseudoscribe:activated', true);
    vscode.commands.executeCommand('pseudoscribe.activate');

    console.log('PseudoScribe extension activated successfully');
}
