import * as vscode from 'vscode';

/**
 * NotificationManager handles user notifications and feedback
 * Supports VSC-001 user feedback requirements
 */
export class NotificationManager {
    
    /**
     * Show information notification
     */
    showInfo(message: string): void {
        vscode.window.showInformationMessage(`PseudoScribe: ${message}`);
    }

    /**
     * Show warning notification
     */
    showWarning(message: string): void {
        vscode.window.showWarningMessage(`PseudoScribe: ${message}`);
    }

    /**
     * Show error notification
     */
    showError(message: string): void {
        vscode.window.showErrorMessage(`PseudoScribe: ${message}`);
    }

    /**
     * Show progress notification with cancellation support
     */
    async showProgress<T>(
        title: string,
        task: (progress: vscode.Progress<{ message?: string; increment?: number }>) => Promise<T>
    ): Promise<T> {
        return vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: `PseudoScribe: ${title}`,
                cancellable: true
            },
            task
        );
    }

    /**
     * Show quick pick selection
     */
    async showQuickPick(items: string[], placeholder: string): Promise<string | undefined> {
        return vscode.window.showQuickPick(items, {
            placeHolder: placeholder
        });
    }

    /**
     * Show input box for user input
     */
    async showInputBox(prompt: string, placeholder?: string): Promise<string | undefined> {
        return vscode.window.showInputBox({
            prompt,
            placeHolder: placeholder
        });
    }
}
