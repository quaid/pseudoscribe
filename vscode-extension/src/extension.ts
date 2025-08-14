import * as vscode from 'vscode';
import { CommandManager } from './commands/commandManager';

/**
 * Main extension entry point
 * Implements VSC-001: Command Integration
 */
export async function activate(context: vscode.ExtensionContext) {
    console.log('PseudoScribe Writer Assistant is now active!');

    // Initialize command manager
    const commandManager = new CommandManager();
    
    try {
        // Register all commands
        await commandManager.registerCommands(context);
        
        // Show activation notification
        vscode.window.showInformationMessage('PseudoScribe Writer Assistant activated successfully!');
        
    } catch (error) {
        console.error('Failed to activate PseudoScribe extension:', error);
        vscode.window.showErrorMessage('Failed to activate PseudoScribe Writer Assistant');
    }
}

export function deactivate() {
    console.log('PseudoScribe Writer Assistant is now deactivated');
}
