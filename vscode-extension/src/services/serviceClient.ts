import axios, { AxiosInstance } from 'axios';
import * as vscode from 'vscode';

/**
 * ServiceClient handles communication with the PseudoScribe backend service
 * Supports the command execution requirements for VSC-001
 */
export class ServiceClient {
    private client: AxiosInstance;
    private baseUrl: string;

    constructor() {
        this.baseUrl = this.getServiceUrl();
        this.client = axios.create({
            baseURL: this.baseUrl,
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    /**
     * Get service URL from VSCode configuration
     */
    public getServiceUrl(): string {
        const config = vscode.workspace.getConfiguration('pseudoscribe');
        return config.get<string>('serviceUrl') || 'http://localhost:8000';
    }

    /**
     * Test connection to the PseudoScribe service
     */
    async testConnection(): Promise<boolean> {
        try {
            const response = await this.client.get('/health');
            return response.status === 200;
        } catch (error) {
            console.error('Service connection test failed:', error);
            return false;
        }
    }

    /**
     * Analyze writing style of provided text
     */
    async analyzeStyle(text: string): Promise<{ summary: string; details: any }> {
        try {
            const response = await this.client.post('/api/style/analyze', {
                content: text
            });
            
            return {
                summary: response.data.summary || 'Analysis completed',
                details: response.data
            };
        } catch (error) {
            console.error('Style analysis failed:', error);
            throw new Error('Failed to analyze writing style');
        }
    }

    /**
     * Adapt content to match target style
     */
    async adaptContent(text: string, targetStyle?: string): Promise<string> {
        try {
            const response = await this.client.post('/api/style/adapt', {
                content: text,
                target_style: targetStyle || 'default'
            });
            
            return response.data.adapted_content || text;
        } catch (error) {
            console.error('Content adaptation failed:', error);
            throw new Error('Failed to adapt content style');
        }
    }

    /**
     * Get user's style profile
     */
    async getStyleProfile(): Promise<any> {
        try {
            const response = await this.client.get('/api/style/profile');
            return response.data;
        } catch (error) {
            console.error('Failed to get style profile:', error);
            throw new Error('Failed to load style profile');
        }
    }

    /**
     * Analyze style with detailed characteristics (VSC-004)
     */
    async analyzeStyleDetailed(text: string): Promise<any> {
        try {
            const response = await this.client.post('/api/v1/style/analyze', {
                text: text
            });
            return response.data;
        } catch (error) {
            console.error('Detailed style analysis failed:', error);
            throw new Error('Failed to perform detailed style analysis');
        }
    }

    /**
     * Adapt text to specific style characteristics (VSC-004)
     */
    async adaptTextToStyle(text: string, styleCharacteristics: any, strength?: number): Promise<any> {
        try {
            const response = await this.client.post('/api/v1/style/transform', {
                text: text,
                target_characteristics: styleCharacteristics,
                strength: strength || 0.5
            });
            return response.data;
        } catch (error) {
            console.error('Text style adaptation failed:', error);
            throw new Error('Failed to adapt text to target style');
        }
    }

    /**
     * Compare styles between two texts (VSC-004)
     */
    async compareStyles(text1: string, text2: string): Promise<any> {
        try {
            const response = await this.client.post('/api/v1/style/check-consistency', {
                texts: [text1, text2]
            });
            return response.data;
        } catch (error) {
            console.error('Style comparison failed:', error);
            throw new Error('Failed to compare text styles');
        }
    }

}
