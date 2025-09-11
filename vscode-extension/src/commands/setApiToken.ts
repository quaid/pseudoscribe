import * as vscode from 'vscode';
import { TokenManager } from '../auth/tokenManager';

/**
 * Handles the 'pseudoscribe.setApiToken' command.
 * Prompts the user for an API token and stores it securely.
 * @param tokenManager An instance of TokenManager to use for storing the token.
 */
export async function setApiTokenCommand(tokenManager: TokenManager) {
    const token = await vscode.window.showInputBox({
        prompt: 'Enter your PseudoScribe API Token',
        password: true,
        ignoreFocusOut: true,
        placeHolder: 'pst_...'
    });

    if (token) {
        await tokenManager.setToken(token);
        vscode.window.showInformationMessage('PseudoScribe API token saved successfully.');
    } else {
        vscode.window.showWarningMessage('No API token was entered.');
    }
}
