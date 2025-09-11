import * as vscode from 'vscode';
import { ServiceClient } from '../services/serviceClient';

/**
 * Handles the logic for the 'pseudoscribe.activate' command.
 * Checks the connection to the backend service.
 */
export async function activateCommand(serviceClient: ServiceClient) {
    try {
        const connected = await serviceClient.testConnection();
        if (connected) {
            vscode.window.showInformationMessage('Successfully connected to PseudoScribe service.');
        } else {
            vscode.window.showErrorMessage('Failed to connect to PseudoScribe service. Please check the URL and ensure the service is running.');
        }
    } catch (error) {
        console.error('Failed to connect to PseudoScribe service:', error);
        vscode.window.showErrorMessage('An error occurred while connecting to the PseudoScribe service.');
    }
}
