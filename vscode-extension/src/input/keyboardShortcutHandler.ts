import * as vscode from 'vscode';

/**
 * Interface for keyboard shortcut configuration
 */
interface ShortcutConfig {
    command: string;
    key: string;
    when?: string;
    title: string;
}

/**
 * Handles keyboard shortcuts for PseudoScribe extension
 * Implements VSC-003: Input Handling - Keyboard shortcuts
 */
export class KeyboardShortcutHandler implements vscode.Disposable {
    private disposables: vscode.Disposable[] = [];
    private shortcuts: ShortcutConfig[] = [];

    constructor(private context: vscode.ExtensionContext) {
        this.initializeShortcuts();
    }

    /**
     * Initialize default keyboard shortcuts
     */
    private initializeShortcuts(): void {
        this.shortcuts = [
            {
                command: 'pseudoscribe.quickAnalyze',
                key: 'ctrl+shift+a',
                when: 'editorTextFocus',
                title: 'Quick Style Analysis'
            },
            {
                command: 'pseudoscribe.quickAdapt',
                key: 'ctrl+shift+t',
                when: 'editorHasSelection',
                title: 'Quick Content Adaptation'
            },
            {
                command: 'pseudoscribe.showProfile',
                key: 'ctrl+shift+p',
                when: 'editorTextFocus',
                title: 'Show Style Profile'
            },
            {
                command: 'pseudoscribe.toggleViews',
                key: 'ctrl+shift+v',
                title: 'Toggle PseudoScribe Views'
            }
        ];
    }

    /**
     * Register all keyboard shortcuts
     */
    async registerShortcuts(): Promise<void> {
        try {
            // Register quick analyze command
            const quickAnalyzeDisposable = vscode.commands.registerCommand(
                'pseudoscribe.quickAnalyze',
                this.handleQuickAnalyze.bind(this)
            );
            this.disposables.push(quickAnalyzeDisposable);

            // Register quick adapt command
            const quickAdaptDisposable = vscode.commands.registerCommand(
                'pseudoscribe.quickAdapt',
                this.handleQuickAdapt.bind(this)
            );
            this.disposables.push(quickAdaptDisposable);

            // Register show profile command
            const showProfileDisposable = vscode.commands.registerCommand(
                'pseudoscribe.showProfile',
                this.handleShowProfile.bind(this)
            );
            this.disposables.push(showProfileDisposable);

            // Register toggle views command
            const toggleViewsDisposable = vscode.commands.registerCommand(
                'pseudoscribe.toggleViews',
                this.handleToggleViews.bind(this)
            );
            this.disposables.push(toggleViewsDisposable);

            console.log('PseudoScribe keyboard shortcuts registered successfully');
        } catch (error) {
            console.error('Failed to register keyboard shortcuts:', error);
        }
    }

    /**
     * Handle quick style analysis shortcut
     */
    private async handleQuickAnalyze(): Promise<void> {
        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No active editor found');
                return;
            }

            // Show progress indicator
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Analyzing style...',
                cancellable: false
            }, async (progress) => {
                progress.report({ increment: 0 });
                
                // Simulate analysis (in real implementation, this would call the service)
                await new Promise(resolve => setTimeout(resolve, 1000));
                progress.report({ increment: 50 });
                
                // Execute the main analyze command
                await vscode.commands.executeCommand('pseudoscribe.analyzeStyle');
                progress.report({ increment: 100 });
            });

        } catch (error) {
            console.error('Quick analyze failed:', error);
            vscode.window.showErrorMessage('Failed to analyze style');
        }
    }

    /**
     * Handle quick content adaptation shortcut
     */
    private async handleQuickAdapt(): Promise<void> {
        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No active editor found');
                return;
            }

            const selection = editor.selection;
            if (selection.isEmpty) {
                vscode.window.showWarningMessage('Please select text to adapt');
                return;
            }

            // Show progress indicator
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Adapting content...',
                cancellable: false
            }, async (progress) => {
                progress.report({ increment: 0 });
                
                // Simulate adaptation
                await new Promise(resolve => setTimeout(resolve, 1500));
                progress.report({ increment: 50 });
                
                // Execute the main adapt command
                await vscode.commands.executeCommand('pseudoscribe.adaptContent');
                progress.report({ increment: 100 });
            });

        } catch (error) {
            console.error('Quick adapt failed:', error);
            vscode.window.showErrorMessage('Failed to adapt content');
        }
    }

    /**
     * Handle show style profile shortcut
     */
    private async handleShowProfile(): Promise<void> {
        try {
            // Focus on the style profile view
            await vscode.commands.executeCommand('pseudoscribe.styleProfile.focus');
            
            // If that fails, try the main command
            if (!await this.isViewVisible('pseudoscribe.styleProfile')) {
                await vscode.commands.executeCommand('pseudoscribe.showStyleProfile');
            }
            
            vscode.window.showInformationMessage('Style profile view opened');
        } catch (error) {
            console.error('Show profile failed:', error);
            vscode.window.showErrorMessage('Failed to show style profile');
        }
    }

    /**
     * Handle toggle views shortcut
     */
    private async handleToggleViews(): Promise<void> {
        try {
            // Toggle the PseudoScribe activity bar
            await vscode.commands.executeCommand('workbench.view.extension.pseudoscribe');
            
            vscode.window.showInformationMessage('PseudoScribe views toggled');
        } catch (error) {
            console.error('Toggle views failed:', error);
            vscode.window.showErrorMessage('Failed to toggle views');
        }
    }

    /**
     * Check if a view is currently visible
     */
    private async isViewVisible(viewId: string): Promise<boolean> {
        try {
            // This is a simplified check - in a real implementation,
            // you might need to track view state more precisely
            return true; // Assume visible for now
        } catch (error) {
            return false;
        }
    }

    /**
     * Get all registered shortcuts
     */
    getRegisteredShortcuts(): ShortcutConfig[] {
        return [...this.shortcuts];
    }

    /**
     * Check if a shortcut can be executed
     */
    canExecuteShortcut(command: string): boolean {
        const shortcut = this.shortcuts.find(s => s.command === command);
        if (!shortcut) {
            return false;
        }

        // Check context conditions
        if (shortcut.when) {
            switch (shortcut.when) {
                case 'editorTextFocus':
                    return !!vscode.window.activeTextEditor;
                case 'editorHasSelection':
                    const editor = vscode.window.activeTextEditor;
                    return !!(editor && !editor.selection.isEmpty);
                default:
                    return true;
            }
        }

        return true;
    }

    /**
     * Execute a shortcut by command name
     */
    async executeShortcut(command: string): Promise<boolean> {
        try {
            if (!this.canExecuteShortcut(command)) {
                return false;
            }

            await vscode.commands.executeCommand(command);
            return true;
        } catch (error) {
            console.error(`Failed to execute shortcut ${command}:`, error);
            return false;
        }
    }

    /**
     * Get shortcut key combination for a command
     */
    getShortcutKey(command: string): string | undefined {
        const shortcut = this.shortcuts.find(s => s.command === command);
        return shortcut?.key;
    }

    /**
     * Update shortcut configuration
     */
    updateShortcut(command: string, newKey: string): boolean {
        const shortcut = this.shortcuts.find(s => s.command === command);
        if (shortcut) {
            shortcut.key = newKey;
            return true;
        }
        return false;
    }

    /**
     * Add custom shortcut
     */
    addCustomShortcut(config: ShortcutConfig): void {
        // Check if command already exists
        const existingIndex = this.shortcuts.findIndex(s => s.command === config.command);
        if (existingIndex >= 0) {
            this.shortcuts[existingIndex] = config;
        } else {
            this.shortcuts.push(config);
        }
    }

    /**
     * Remove shortcut
     */
    removeShortcut(command: string): boolean {
        const index = this.shortcuts.findIndex(s => s.command === command);
        if (index >= 0) {
            this.shortcuts.splice(index, 1);
            return true;
        }
        return false;
    }

    /**
     * Dispose of all resources
     */
    dispose(): void {
        this.disposables.forEach(disposable => {
            try {
                disposable.dispose();
            } catch (error) {
                console.error('Error disposing shortcut resource:', error);
            }
        });
        this.disposables = [];
        this.shortcuts = [];
    }
}
