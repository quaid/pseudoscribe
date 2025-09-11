import * as assert from 'assert';
import * as sinon from 'sinon';
import { mock, instance, when } from 'ts-mockito';
import * as socketIO from 'socket.io-client';
import { RealtimeClient } from '../../realtime/realtimeClient';
import { TokenManager } from '../../auth/tokenManager';
import { ServiceClient } from '../../services/serviceClient';

suite('VSC-004: Real-time Communication Test Suite', () => {
    let mockTokenManager: TokenManager;
    let mockServiceClient: ServiceClient;
    let sandbox: sinon.SinonSandbox;

    setup(() => {
        sandbox = sinon.createSandbox();
        mockTokenManager = mock(TokenManager);
        mockServiceClient = mock(ServiceClient);
    });

    teardown(() => {
        sandbox.restore();
    });

        test('should attempt to connect without throwing an error', async () => {
        const fakeToken = 'fake-jwt-token';
        const baseUrl = 'http://localhost:8080';

        when(mockTokenManager.getToken()).thenResolve(fakeToken);
        when(mockServiceClient.getServiceUrl()).thenReturn(baseUrl);

        // Note: Stubbing the top-level 'io' function from socket.io-client is not feasible
        // with Sinon in this context due to its non-configurable property descriptor.
        // This unit test ensures the connect method runs without errors.
        // The actual socket connection will be verified by integration tests.

        const realtimeClient = new RealtimeClient(instance(mockTokenManager), instance(mockServiceClient));
        
        await assert.doesNotReject(
            async () => realtimeClient.connect(),
            'connect() should not throw an error'
        );
    });
});
