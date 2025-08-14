import * as vscode from 'vscode';

/**
 * StatusBarManager handles status bar updates for user feedback
 * Supports VSC-001 user feedback requirements
 */
export class StatusBarManager {
    private statusBarItem: vscode.StatusBarItem;

    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left,
            100
        );
        this.statusBarItem.show();
    }

    /**
     * Show progress indicator in status bar
     */
    showProgress(message: string): void {
        this.statusBarItem.text = `$(sync~spin) ${message}`;
        this.statusBarItem.tooltip = 'PseudoScribe operation in progress';
    }

    /**
     * Hide progress indicator
     */
    hideProgress(): void {
        this.statusBarItem.text = '$(check) PseudoScribe';
        this.statusBarItem.tooltip = 'PseudoScribe Writer Assistant';
    }

    /**
     * Show error state in status bar
     */
    showError(message: string): void {
        this.statusBarItem.text = `$(error) ${message}`;
        this.statusBarItem.tooltip = 'PseudoScribe error - click for details';
    }

    /**
     * Dispose of status bar item
     */
    dispose(): void {
        this.statusBarItem.dispose();
    }
}
