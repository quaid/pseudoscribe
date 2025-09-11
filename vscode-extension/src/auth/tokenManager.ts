import * as vscode from 'vscode';

const secretKey = 'pseudoscribe.apiToken';

/**
 * Manages the secure storage and retrieval of the API token.
 * Implements VSC-003: Service Authentication
 */
export class TokenManager {
    constructor(private readonly context: vscode.ExtensionContext) {}

    /**
     * Stores the API token securely in VSCode's SecretStorage.
     * @param token The API token to store.
     */
    async setToken(token: string): Promise<void> {
        await this.context.secrets.store(secretKey, token);
    }

    /**
     * Retrieves the stored API token from SecretStorage.
     * @returns The API token, or undefined if it has not been set.
     */
    async getToken(): Promise<string | undefined> {
        return await this.context.secrets.get(secretKey);
    }

    /**
     * Deletes the stored API token from SecretStorage.
     */
    async deleteToken(): Promise<void> {
        await this.context.secrets.delete(secretKey);
    }
}
