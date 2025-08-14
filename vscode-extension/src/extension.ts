import * as vscode from 'vscode';
import { CommandManager } from './commands/commandManager';
import { ViewManager } from './views/viewManager';

let viewManager: ViewManager | undefined;

/**
 * Main extension entry point
 * Implements VSC-001: Command Integration
 */
export async function activate(context: vscode.ExtensionContext) {
    try {
        // Initialize command manager
        const commandManager = new CommandManager();
        await commandManager.registerCommands(context);

        // Initialize view manager
        viewManager = new ViewManager(context);
        await viewManager.initializeViews();

        // Set context to indicate extension is activated
        vscode.commands.executeCommand('setContext', 'pseudoscribe:activated', true);

        // Show activation notification
        vscode.window.showInformationMessage('PseudoScribe Writer Assistant activated!');

        console.log('PseudoScribe extension activated successfully');
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

    // Set context to indicate extension is deactivated
    vscode.commands.executeCommand('setContext', 'pseudoscribe:activated', false);
    
    console.log('PseudoScribe extension deactivated');
}
