import * as vscode from 'vscode';
import { CommandManager } from './commands/commandManager';
import { ViewManager } from './views/viewManager';
import { InputManager } from './input/inputManager';
import { TokenManager } from './auth/tokenManager';
import { ServiceClient } from './services/serviceClient';
import { handleActivation } from './activation';

let viewManager: ViewManager | undefined;
let inputManager: InputManager | undefined;

/**
 * Main extension entry point
 * Implements VSC-001: Command Integration
 */

export async function activate(context: vscode.ExtensionContext) {
    try {
        const tokenManager = new TokenManager(context);
        const serviceClient = new ServiceClient(tokenManager);
        const commandManager = new CommandManager(serviceClient, tokenManager);
        viewManager = new ViewManager(context);
        inputManager = new InputManager(context);

        await handleActivation(
            context,
            tokenManager,
            serviceClient,
            commandManager,
            viewManager,
            inputManager
        );
    } catch (error) {
        console.error('Failed to activate PseudoScribe extension:', error);
        vscode.window.showErrorMessage('Failed to activate PseudoScribe extension');
    }
}

export function deactivate() {
    // Dispose view manager
    if (viewManager) {
        viewManager.dispose();
        viewManager = undefined;
    }

    // Dispose input manager
    if (inputManager) {
        inputManager.dispose();
        inputManager = undefined;
    }

    // Set context to indicate extension is deactivated
    vscode.commands.executeCommand('setContext', 'pseudoscribe:activated', false);
    
    console.log('PseudoScribe extension deactivated');
}
