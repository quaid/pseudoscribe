import io from 'socket.io-client';
import { TokenManager } from '../auth/tokenManager';
import { ServiceClient } from '../services/serviceClient';

/**
 * VSC-004: Manages the real-time communication with the backend service.
 */
export class RealtimeClient {
    // TODO: Revisit the 'any' type. The socket.io-client type definitions
    // are causing persistent and contradictory module resolution errors in this environment.
    // Using 'any' as a pragmatic workaround to ensure a stable build.
    private socket: any;

    constructor(
        private tokenManager: TokenManager,
        private serviceClient: ServiceClient
    ) {}

    /**
     * Initializes the real-time client and attempts to connect.
     */
    public async initialize(): Promise<void> {
        try {
            await this.connect();
        } catch (error) {
            console.error('Failed to connect to real-time service:', error);
            // Gracefully handle connection errors without crashing the extension.
        }
    }

    /**
     * Establishes a connection to the real-time service.
     */
    public async connect(): Promise<void> {
        const token = await this.tokenManager.getToken();
        const baseUrl = this.serviceClient.getServiceUrl();
        const wsUrl = baseUrl.replace(/^http/, 'ws');

                this.socket = io(wsUrl, {
            auth: {
                token
            }
        });
    }
}

