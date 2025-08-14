import * as vscode from 'vscode';

/**
 * Interface for context menu item configuration
 */
interface MenuItemConfig {
    command: string;
    title: string;
    group?: string;
    when?: string;
    icon?: string;
}

/**
 * Provides context menu integration for PseudoScribe extension
 * Implements VSC-003: Input Handling - Context menus
 */
export class ContextMenuProvider implements vscode.Disposable {
    private disposables: vscode.Disposable[] = [];
    private menuItems: MenuItemConfig[] = [];

    constructor(private context: vscode.ExtensionContext) {
        this.initializeMenuItems();
    }

    /**
     * Initialize default context menu items
     */
    private initializeMenuItems(): void {
        this.menuItems = [
            {
                command: 'pseudoscribe.analyzeStyle',
                title: 'Analyze Writing Style',
                group: 'pseudoscribe@1',
                when: 'editorTextFocus',
                icon: '$(symbol-property)'
            },
            {
                command: 'pseudoscribe.adaptContent',
                title: 'Adapt Content Style',
                group: 'pseudoscribe@2',
                when: 'editorHasSelection',
                icon: '$(arrow-swap)'
            },
            {
                command: 'pseudoscribe.showStyleProfile',
                title: 'Show Style Profile',
                group: 'pseudoscribe@3',
                when: 'editorTextFocus',
                icon: '$(account)'
            },
            {
                command: 'pseudoscribe.connectService',
                title: 'Connect to PseudoScribe Service',
                group: 'pseudoscribe@4',
                icon: '$(plug)'
            }
        ];
    }

    /**
     * Register context menus with VSCode
     */
    async registerMenus(): Promise<void> {
        try {
            // Context menus are primarily configured through package.json
            // but we can register dynamic menu providers here if needed
            
            // Register menu command handlers (if not already registered)
            await this.ensureCommandsRegistered();
            
            console.log('PseudoScribe context menus registered successfully');
        } catch (error) {
            console.error('Failed to register context menus:', error);
        }
    }

    /**
     * Ensure all menu commands are registered
     */
    private async ensureCommandsRegistered(): Promise<void> {
        const commands = await vscode.commands.getCommands();
        
        for (const menuItem of this.menuItems) {
            if (!commands.includes(menuItem.command)) {
                // Register a placeholder command if not already registered
                const disposable = vscode.commands.registerCommand(
                    menuItem.command,
                    this.createCommandHandler(menuItem.command)
                );
                this.disposables.push(disposable);
            }
        }
    }

    /**
     * Create a command handler for menu items
     */
    private createCommandHandler(command: string) {
        return async (...args: any[]) => {
            try {
                switch (command) {
                    case 'pseudoscribe.analyzeStyle':
                        await this.handleAnalyzeStyle();
                        break;
                    case 'pseudoscribe.adaptContent':
                        await this.handleAdaptContent();
                        break;
                    case 'pseudoscribe.showStyleProfile':
                        await this.handleShowStyleProfile();
                        break;
                    case 'pseudoscribe.connectService':
                        await this.handleConnectService();
                        break;
                    default:
                        console.warn(`Unknown command: ${command}`);
                }
            } catch (error) {
                console.error(`Error executing command ${command}:`, error);
                vscode.window.showErrorMessage(`Failed to execute ${command}`);
            }
        };
    }

    /**
     * Handle analyze style menu action
     */
    private async handleAnalyzeStyle(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active editor found');
            return;
        }

        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Analyzing writing style...',
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0 });
            
            // Get text content
            const text = editor.document.getText();
            if (!text.trim()) {
                vscode.window.showWarningMessage('No content to analyze');
                return;
            }
            
            progress.report({ increment: 50, message: 'Processing content...' });
            
            // Simulate analysis
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            progress.report({ increment: 100, message: 'Analysis complete' });
            
            vscode.window.showInformationMessage('Style analysis completed');
        });
    }

    /**
     * Handle adapt content menu action
     */
    private async handleAdaptContent(): Promise<void> {
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

        const selectedText = editor.document.getText(selection);
        
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Adapting content style...',
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0 });
            
            progress.report({ increment: 30, message: 'Analyzing selected text...' });
            await new Promise(resolve => setTimeout(resolve, 500));
            
            progress.report({ increment: 70, message: 'Generating adaptations...' });
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            progress.report({ increment: 100, message: 'Adaptation complete' });
            
            vscode.window.showInformationMessage(`Adapted ${selectedText.length} characters`);
        });
    }

    /**
     * Handle show style profile menu action
     */
    private async handleShowStyleProfile(): Promise<void> {
        try {
            // Focus on the style profile view
            await vscode.commands.executeCommand('pseudoscribe.styleProfile.focus');
            vscode.window.showInformationMessage('Style profile view opened');
        } catch (error) {
            console.error('Failed to show style profile:', error);
            vscode.window.showErrorMessage('Failed to open style profile view');
        }
    }

    /**
     * Handle connect service menu action
     */
    private async handleConnectService(): Promise<void> {
        const serviceUrl = await vscode.window.showInputBox({
            prompt: 'Enter PseudoScribe service URL',
            placeHolder: 'http://localhost:8000',
            value: 'http://localhost:8000'
        });

        if (!serviceUrl) {
            return;
        }

        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Connecting to PseudoScribe service...',
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0 });
            
            // Simulate connection attempt
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            progress.report({ increment: 100 });
            
            vscode.window.showInformationMessage(`Connected to ${serviceUrl}`);
        });
    }

    /**
     * Get all menu items
     */
    getMenuItems(): MenuItemConfig[] {
        return [...this.menuItems];
    }

    /**
     * Get menu items for specific context
     */
    getMenuItemsForContext(context: string): MenuItemConfig[] {
        switch (context) {
            case 'selection':
                return this.menuItems.filter(item => 
                    !item.when || item.when === 'editorHasSelection' || item.when === 'editorTextFocus'
                );
            case 'editor':
                return this.menuItems.filter(item => 
                    !item.when || item.when === 'editorTextFocus'
                );
            default:
                return this.menuItems;
        }
    }

    /**
     * Add custom menu item
     */
    addMenuItem(config: MenuItemConfig): void {
        const existingIndex = this.menuItems.findIndex(item => item.command === config.command);
        if (existingIndex >= 0) {
            this.menuItems[existingIndex] = config;
        } else {
            this.menuItems.push(config);
        }
    }

    /**
     * Remove menu item
     */
    removeMenuItem(command: string): boolean {
        const index = this.menuItems.findIndex(item => item.command === command);
        if (index >= 0) {
            this.menuItems.splice(index, 1);
            return true;
        }
        return false;
    }

    /**
     * Update menu item
     */
    updateMenuItem(command: string, updates: Partial<MenuItemConfig>): boolean {
        const item = this.menuItems.find(item => item.command === command);
        if (item) {
            Object.assign(item, updates);
            return true;
        }
        return false;
    }

    /**
     * Check if menu item should be visible in current context
     */
    isMenuItemVisible(command: string): boolean {
        const item = this.menuItems.find(item => item.command === command);
        if (!item) {
            return false;
        }

        if (!item.when) {
            return true;
        }

        switch (item.when) {
            case 'editorTextFocus':
                return !!vscode.window.activeTextEditor;
            case 'editorHasSelection':
                const editor = vscode.window.activeTextEditor;
                return !!(editor && !editor.selection.isEmpty);
            default:
                return true;
        }
    }

    /**
     * Get visible menu items for current context
     */
    getVisibleMenuItems(): MenuItemConfig[] {
        return this.menuItems.filter(item => this.isMenuItemVisible(item.command));
    }

    /**
     * Dispose of all resources
     */
    dispose(): void {
        this.disposables.forEach(disposable => {
            try {
                disposable.dispose();
            } catch (error) {
                console.error('Error disposing context menu resource:', error);
            }
        });
        this.disposables = [];
        this.menuItems = [];
    }
}
