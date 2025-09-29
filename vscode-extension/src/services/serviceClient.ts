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
     * VSC-004: Analyze style with detailed metrics
     */
    async analyzeStyleDetailed(text: string): Promise<any> {
        try {
            const response = await this.client.post('/api/v1/style/analyze', {
                content: text,
                include_metrics: true,
                include_suggestions: true
            }, {
                headers: {
                    'X-Tenant-ID': 'vscode-extension'
                }
            });
            
            return response.data;
        } catch (error) {
            console.error('Detailed style analysis failed:', error);
            throw new Error('Failed to perform detailed style analysis');
        }
    }

    /**
     * VSC-004: Transform text to match target style profile
     */
    async adaptTextToStyle(text: string, targetProfile: any, strength: number = 0.7): Promise<any> {
        try {
            const response = await this.client.post('/api/v1/style/transform', {
                content: text,
                target_style: targetProfile,
                transformation_strength: strength,
                preserve_meaning: true
            }, {
                headers: {
                    'X-Tenant-ID': 'vscode-extension'
                }
            });
            
            return response.data;
        } catch (error) {
            console.error('Text style adaptation failed:', error);
            throw new Error('Failed to adapt text to target style');
        }
    }

    /**
     * VSC-004: Check consistency across multiple text segments
     */
    async checkConsistency(textSegments: string[]): Promise<any> {
        try {
            const response = await this.client.post('/api/v1/style/check-consistency', {
                text_segments: textSegments
            }, {
                headers: {
                    'X-Tenant-ID': 'vscode-extension'
                }
            });
            
            return response.data;
        } catch (error) {
            console.error('Consistency check failed:', error);
            throw new Error('Failed to check text consistency');
        }
    }

    /**
     * VSC-005: Analyze content for live suggestions
     */
    async analyzeLive(content: string, context: any = {}): Promise<any> {
        try {
            const response = await this.client.post('/api/v1/suggestions/analyze-live', {
                content,
                context,
                document_type: context.document_type || 'text',
                real_time: true
            }, {
                headers: {
                    'X-Tenant-ID': 'vscode-extension'
                }
            });
            
            return response.data;
        } catch (error) {
            console.error('Live analysis failed:', error);
            throw new Error('Failed to analyze content for live suggestions');
        }
    }

    /**
     * VSC-005: Accept a suggestion
     */
    async acceptSuggestion(suggestionId: string, context: any = {}): Promise<any> {
        try {
            const response = await this.client.post('/api/v1/suggestions/accept', {
                suggestion_id: suggestionId,
                context
            }, {
                headers: {
                    'X-Tenant-ID': 'vscode-extension'
                }
            });
            
            return response.data;
        } catch (error) {
            console.error('Failed to accept suggestion:', error);
            throw new Error('Failed to accept suggestion');
        }
    }

    /**
     * VSC-005: Configure suggestion display preferences
     */
    async configureSuggestionDisplay(config: any): Promise<any> {
        try {
            const response = await this.client.post('/api/v1/suggestions/display-config', {
                ...config
            }, {
                headers: {
                    'X-Tenant-ID': 'vscode-extension'
                }
            });
            
            return response.data;
        } catch (error) {
            console.error('Failed to configure suggestion display:', error);
            throw new Error('Failed to configure suggestion display');
        }
    }

    /**
     * VSC-004: Compare styles between two text samples
     */
    async compareStyles(text1: string, text2: string): Promise<any> {
        try {
            const response = await this.client.post('/api/v1/style/compare', {
                text1,
                text2,
                include_metrics: true
            }, {
                headers: {
                    'X-Tenant-ID': 'vscode-extension'
                }
            });
            
            return response.data;
        } catch (error) {
            console.error('Style comparison failed:', error);
            throw new Error('Failed to compare styles');
        }
    }
}
