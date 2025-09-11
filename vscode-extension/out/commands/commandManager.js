"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.CommandManager = void 0;
const vscode = __importStar(require("vscode"));
const serviceClient_1 = require("../services/serviceClient");
const statusBarManager_1 = require("../ui/statusBarManager");
const notificationManager_1 = require("../ui/notificationManager");
/**
 * CommandManager handles registration and execution of all PseudoScribe commands
 * Implements VSC-001: Command Integration acceptance criteria
 */
class CommandManager {
    constructor() {
        this.serviceClient = new serviceClient_1.ServiceClient();
        this.statusBar = new statusBarManager_1.StatusBarManager();
        this.notifications = new notificationManager_1.NotificationManager();
    }
    /**
     * Register all PseudoScribe commands with VSCode
     * Fulfills BDD scenario: "Register commands"
     */
    async registerCommands(context) {
        if (!context) {
            console.warn('Invalid context provided to registerCommands');
            return;
        }
        try {
            // Register analyzeStyle command
            const analyzeStyleCommand = vscode.commands.registerCommand('pseudoscribe.analyzeStyle', this.handleAnalyzeStyle.bind(this));
            // Register adaptContent command
            const adaptContentCommand = vscode.commands.registerCommand('pseudoscribe.adaptContent', this.handleAdaptContent.bind(this));
            // Register connectService command
            const connectServiceCommand = vscode.commands.registerCommand('pseudoscribe.connectService', this.handleConnectService.bind(this));
            // Register showStyleProfile command
            const showStyleProfileCommand = vscode.commands.registerCommand('pseudoscribe.showStyleProfile', this.handleShowStyleProfile.bind(this));
            // Add all commands to context subscriptions
            // Register setApiToken command
            const setApiTokenCommand = vscode.commands.registerCommand('pseudoscribe.setApiToken', this.handleSetApiToken.bind(this));
            // Register activate command
            const activateCommand = vscode.commands.registerCommand('pseudoscribe.activate', this.handleActivate.bind(this));
            context.subscriptions.push(analyzeStyleCommand, adaptContentCommand, connectServiceCommand, showStyleProfileCommand, setApiTokenCommand, activateCommand);
            console.log('All PseudoScribe commands registered successfully');
        }
        catch (error) {
            console.error('Error registering commands:', error);
            throw error;
        }
    }
    /**
     * Handle analyzeStyle command execution
     * Fulfills BDD scenario: "Execute command" with feedback
     */
    async handleAnalyzeStyle() {
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
        }
        catch (error) {
            this.statusBar.hideProgress();
            this.notifications.showError(`Style analysis failed: ${error}`);
            return 'error';
        }
    }
    /**
     * Handle adaptContent command execution
     */
    async handleAdaptContent() {
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
        }
        catch (error) {
            this.statusBar.hideProgress();
            this.notifications.showError(`Content adaptation failed: ${error}`);
            return 'error';
        }
    }
    /**
     * Handle connectService command execution
     */
    async handleConnectService() {
        try {
            this.statusBar.showProgress('Connecting to PseudoScribe service...');
            const connected = await this.serviceClient.testConnection();
            this.statusBar.hideProgress();
            if (connected) {
                this.notifications.showInfo('Successfully connected to PseudoScribe service');
                return 'success';
            }
            else {
                this.notifications.showError('Failed to connect to PseudoScribe service');
                return 'error';
            }
        }
        catch (error) {
            this.statusBar.hideProgress();
            this.notifications.showError(`Connection failed: ${error}`);
            return 'error';
        }
    }
    /**
     * Handle showStyleProfile command execution
     */
    async handleSetApiToken() {
        const token = await vscode.window.showInputBox({ prompt: 'Enter your PseudoScribe API Token' });
        if (token) {
            // In a real scenario, we'd use the tokenManager to save this.
            this.notifications.showInfo('API Token received.');
        }
    }
    async handleActivate() {
        // This command is for manual activation or testing.
        this.notifications.showInfo('PseudoScribe is active.');
    }
    async handleShowStyleProfile() {
        try {
            this.statusBar.showProgress('Loading style profile...');
            const profile = await this.serviceClient.getStyleProfile();
            this.statusBar.hideProgress();
            this.notifications.showInfo('Style profile loaded successfully');
            return 'success';
        }
        catch (error) {
            this.statusBar.hideProgress();
            this.notifications.showError(`Failed to load style profile: ${error}`);
            return 'error';
        }
    }
}
exports.CommandManager = CommandManager;
//# sourceMappingURL=commandManager.js.map