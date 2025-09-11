import * as vscode from 'vscode';
import { InputManager } from '../input/inputManager';
import { ViewManager } from '../views/viewManager';

/**
 * A helper class to manage the test environment for VSCode extension tests.
 * This ensures a clean state for each test suite by managing the lifecycle
 * of managers and other disposables.
 */
export class TestHelper {
    public mockContext: vscode.ExtensionContext;
    public inputManager: InputManager | undefined;
    public viewManager: ViewManager | undefined;

    constructor() {
        this.mockContext = this.createMockContext();
    }

    public async setup() {
        this.inputManager = new InputManager(this.mockContext);
        this.viewManager = new ViewManager(this.mockContext);
        await this.inputManager.initialize();
        await this.viewManager.initializeViews();
    }

    public teardown() {
        this.inputManager?.dispose();
        this.viewManager?.dispose();
    }

    private createMockContext(): vscode.ExtensionContext {
        return {
            subscriptions: [],
            workspaceState: { get: () => undefined, update: () => Promise.resolve(), keys: () => [] },
            globalState: { get: () => undefined, update: () => Promise.resolve(), setKeysForSync: () => {}, keys: () => [] },
            extensionUri: vscode.Uri.file('/test'),
            extensionPath: '/test',
            asAbsolutePath: (relativePath: string) => `/test/${relativePath}`,
            storagePath: '/test/storage',
            storageUri: vscode.Uri.file('/test/storage'),
            globalStoragePath: '/test/global',
            globalStorageUri: vscode.Uri.file('/test/global'),
            logPath: '/test/logs',
            logUri: vscode.Uri.file('/test/logs'),
            extensionMode: vscode.ExtensionMode.Test,
            secrets: {} as any,
            environmentVariableCollection: {} as any,
            extension: {} as any,
            languageModelAccessInformation: {} as any
        };
    }
}
