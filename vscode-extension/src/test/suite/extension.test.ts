import * as assert from 'assert';
import * as vscode from 'vscode';
import { mock, instance, when } from 'ts-mockito';
import * as sinon from 'sinon';
import { CommandManager } from '../../commands/commandManager';
import { ServiceClient } from '../../services/serviceClient';
import { TokenManager } from '../../auth/tokenManager';
import { ViewManager } from '../../views/viewManager';
import { InputManager } from '../../input/inputManager';
import { handleActivation } from '../../activation';

suite('VSC-001 & VSC-003: Extension Activation and Command Integration', () => {
    let mockContext: vscode.ExtensionContext;
    let mockTokenManager: TokenManager;
    let mockServiceClient: ServiceClient;
    let mockCommandManager: CommandManager;
    let mockViewManager: ViewManager;
    let mockInputManager: InputManager;
    let sandbox: sinon.SinonSandbox;

    setup(() => {
        sandbox = sinon.createSandbox();
        mockContext = { subscriptions: [] } as any;
        mockTokenManager = mock(TokenManager);
        mockServiceClient = mock(ServiceClient);
        mockCommandManager = mock(CommandManager);
        mockViewManager = mock(ViewManager);
        mockInputManager = mock(InputManager);
    });

    teardown(() => {
        sandbox.restore();
    });

    test('should not prompt for token if one exists', async () => {
        const executeCommandStub = sandbox.stub(vscode.commands, 'executeCommand');
        when(mockTokenManager.getToken()).thenResolve('fake-token');

        await handleActivation(
            mockContext,
            instance(mockTokenManager),
            instance(mockServiceClient),
            instance(mockCommandManager),
            instance(mockViewManager),
            instance(mockInputManager)
        );

        assert.ok(executeCommandStub.withArgs('pseudoscribe.setApiToken').notCalled, 'setApiToken should not be called when a token exists');
    });

    test('should prompt for token if none exists', async () => {
        const executeCommandStub = sandbox.stub(vscode.commands, 'executeCommand');
        when(mockTokenManager.getToken()).thenResolve(undefined);

        await handleActivation(
            mockContext,
            instance(mockTokenManager),
            instance(mockServiceClient),
            instance(mockCommandManager),
            instance(mockViewManager),
            instance(mockInputManager)
        );

        assert.ok(executeCommandStub.calledWith('pseudoscribe.setApiToken'), 'setApiToken should be called when no token exists');
    });
});
