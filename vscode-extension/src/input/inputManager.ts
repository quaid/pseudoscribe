import * as vscode from 'vscode';
import { KeyboardShortcutHandler } from './keyboardShortcutHandler';
import { ContextMenuProvider } from './contextMenuProvider';

/**
 * Manages all input handling for the PseudoScribe extension
 * Implements VSC-003: Input Handling coordination
 */
export class InputManager implements vscode.Disposable {
    private shortcutHandler: KeyboardShortcutHandler | undefined;
    private contextMenuProvider: ContextMenuProvider | undefined;
    private disposables: vscode.Disposable[] = [];

    constructor(private context: vscode.ExtensionContext) {}

    /**
     * Initialize all input handling components
     */
    async initialize(): Promise<void> {
        try {
            // Initialize keyboard shortcut handler
            this.shortcutHandler = new KeyboardShortcutHandler(this.context);
            this.disposables.push(this.shortcutHandler);

            // Initialize context menu provider
            this.contextMenuProvider = new ContextMenuProvider(this.context);
            this.disposables.push(this.contextMenuProvider);

            console.log('InputManager initialized successfully');
        } catch (error) {
            console.error('Failed to initialize InputManager:', error);
        }
    }

    /**
     * Register keyboard shortcuts
     */
    async registerShortcuts(): Promise<void> {
        if (this.shortcutHandler) {
            await this.shortcutHandler.registerShortcuts();
        }
    }

    /**
     * Register context menus
     */
    async registerContextMenus(): Promise<void> {
        if (this.contextMenuProvider) {
            await this.contextMenuProvider.registerMenus();
        }
    }

    /**
     * Get the keyboard shortcut handler
     */
    getShortcutHandler(): KeyboardShortcutHandler | undefined {
        return this.shortcutHandler;
    }

    /**
     * Get the context menu provider
     */
    getContextMenuProvider(): ContextMenuProvider | undefined {
        return this.contextMenuProvider;
    }

    /**
     * Check if event listeners are registered
     */
    hasEventListeners(): boolean {
        return !!(this.shortcutHandler && this.contextMenuProvider);
    }

    /**
     * Dispose of all resources
     */
    dispose(): void {
        this.disposables.forEach(disposable => {
            try {
                disposable.dispose();
            } catch (error) {
                console.error('Error disposing input resource:', error);
            }
        });
        this.disposables = [];
        this.shortcutHandler = undefined;
        this.contextMenuProvider = undefined;
    }
}
