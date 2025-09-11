import * as vscode from 'vscode';
import { ServiceClient } from '../services/serviceClient';
import { StatusBarManager } from '../ui/statusBarManager';
import { NotificationManager } from '../ui/notificationManager';

/**
 * CommandManager handles registration and execution of all PseudoScribe commands
 * Implements VSC-001: Command Integration acceptance criteria
 */
export class CommandManager {
    private serviceClient: ServiceClient;
    private statusBar: StatusBarManager;
    private notifications: NotificationManager;

    constructor() {
        this.serviceClient = new ServiceClient();
        this.statusBar = new StatusBarManager();
        this.notifications = new NotificationManager();
    }

    /**
     * Register all PseudoScribe commands with VSCode
     * Fulfills BDD scenario: "Register commands"
     */
    async registerCommands(context: vscode.ExtensionContext): Promise<void> {
        if (!context) {
            console.warn('Invalid context provided to registerCommands');
            return;
        }

        try {
            // Register analyzeStyle command
            const analyzeStyleCommand = vscode.commands.registerCommand(
                'pseudoscribe.analyzeStyle',
                this.handleAnalyzeStyle.bind(this)
            );

            // Register adaptContent command
            const adaptContentCommand = vscode.commands.registerCommand(
                'pseudoscribe.adaptContent',
                this.handleAdaptContent.bind(this)
            );

            // Register connectService command
            const connectServiceCommand = vscode.commands.registerCommand(
                'pseudoscribe.connectService',
                this.handleConnectService.bind(this)
            );

            // Register showStyleProfile command
            const showStyleProfileCommand = vscode.commands.registerCommand(
                'pseudoscribe.showStyleProfile',
                this.handleShowStyleProfile.bind(this)
            );

            // Add all commands to context subscriptions
            // Register setApiToken command
            const setApiTokenCommand = vscode.commands.registerCommand(
                'pseudoscribe.setApiToken',
                this.handleSetApiToken.bind(this)
            );

            // Register activate command
            const activateCommand = vscode.commands.registerCommand(
                'pseudoscribe.activate',
                this.handleActivate.bind(this)
            );

            context.subscriptions.push(
                analyzeStyleCommand,
                adaptContentCommand,
                connectServiceCommand,
                showStyleProfileCommand,
                setApiTokenCommand,
                activateCommand
            );

            console.log('All PseudoScribe commands registered successfully');

        } catch (error) {
            console.error('Error registering commands:', error);
            throw error;
        }
    }

    /**
     * Handle analyzeStyle command execution
     * Fulfills BDD scenario: "Execute command" with feedback
     */
    private async handleAnalyzeStyle(): Promise<string> {
        try {
            this.statusBar.showProgress('Analyzing writing style...');

            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                this.notifications.showError('No active text editor found');
                return 'error';
            }

            const selection = editor.selection;
            const text = editor.document.getText(selection.isEmpty ? undefined : selection);

            if (!text.trim()) {
                this.notifications.showWarning('No text selected or available for analysis');
                return 'warning';
            }

            // Call service to analyze style
            const analysis = await this.serviceClient.analyzeStyle(text);
            
            this.statusBar.hideProgress();
            this.notifications.showInfo(`Style analysis complete: ${analysis.summary}`);
            
            return 'success';

        } catch (error) {
            this.statusBar.hideProgress();
            this.notifications.showError(`Style analysis failed: ${error}`);
            return 'error';
        }
    }

    /**
     * Handle adaptContent command execution
     */
    private async handleAdaptContent(): Promise<string> {
        try {
            this.statusBar.showProgress('Adapting content style...');

            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                this.notifications.showError('No active text editor found');
                return 'error';
            }

            const selection = editor.selection;
            const text = editor.document.getText(selection.isEmpty ? undefined : selection);

            if (!text.trim()) {
                this.notifications.showWarning('No text selected for adaptation');
                return 'warning';
            }

            // Call service to adapt content
            const adaptedContent = await this.serviceClient.adaptContent(text);
            
            this.statusBar.hideProgress();
            this.notifications.showInfo('Content adaptation complete');
            
            return 'success';

        } catch (error) {
            this.statusBar.hideProgress();
            this.notifications.showError(`Content adaptation failed: ${error}`);
            return 'error';
        }
    }

    /**
     * Handle connectService command execution
     */
    private async handleConnectService(): Promise<string> {
        try {
            this.statusBar.showProgress('Connecting to PseudoScribe service...');

            const connected = await this.serviceClient.testConnection();
            
            this.statusBar.hideProgress();
            
            if (connected) {
                this.notifications.showInfo('Successfully connected to PseudoScribe service');
                return 'success';
            } else {
                this.notifications.showError('Failed to connect to PseudoScribe service');
                return 'error';
            }

        } catch (error) {
            this.statusBar.hideProgress();
            this.notifications.showError(`Connection failed: ${error}`);
            return 'error';
        }
    }

    /**
     * Handle showStyleProfile command execution
     */
    private async handleSetApiToken(): Promise<void> {
        const token = await vscode.window.showInputBox({ prompt: 'Enter your PseudoScribe API Token' });
        if (token) {
            // In a real scenario, we'd use the tokenManager to save this.
            this.notifications.showInfo('API Token received.');
        }
    }

    private async handleActivate(): Promise<void> {
        // This command is for manual activation or testing.
        this.notifications.showInfo('PseudoScribe is active.');
    }

    private async handleShowStyleProfile(): Promise<string> {
        try {
            this.statusBar.showProgress('Loading style profile...');

            const profile = await this.serviceClient.getStyleProfile();
            
            this.statusBar.hideProgress();
            this.notifications.showInfo('Style profile loaded successfully');
            
            return 'success';

        } catch (error) {
            this.statusBar.hideProgress();
            this.notifications.showError(`Failed to load style profile: ${error}`);
            return 'error';
        }
    }
}
