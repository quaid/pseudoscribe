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

export interface ExtensionApi {
    viewManager: ViewManager | undefined;
    inputManager: InputManager | undefined;
}

export async function activate(context: vscode.ExtensionContext): Promise<ExtensionApi> {
    try {
        const tokenManager = new TokenManager(context);
        const serviceClient = new ServiceClient();
        const commandManager = new CommandManager();
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

        return {
            viewManager,
            inputManager
        };
    } catch (error) {
        console.error('Failed to activate PseudoScribe extension:', error);
        vscode.window.showErrorMessage('Failed to activate PseudoScribe extension');
        // Return a dummy API on failure to satisfy the type contract
        return {
            viewManager: undefined,
            inputManager: undefined
        };
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
