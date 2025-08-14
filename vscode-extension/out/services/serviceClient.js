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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ServiceClient = void 0;
const axios_1 = __importDefault(require("axios"));
const vscode = __importStar(require("vscode"));
/**
 * ServiceClient handles communication with the PseudoScribe backend service
 * Supports the command execution requirements for VSC-001
 */
class ServiceClient {
    constructor() {
        this.baseUrl = this.getServiceUrl();
        this.client = axios_1.default.create({
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
    getServiceUrl() {
        const config = vscode.workspace.getConfiguration('pseudoscribe');
        return config.get('serviceUrl') || 'http://localhost:8000';
    }
    /**
     * Test connection to the PseudoScribe service
     */
    async testConnection() {
        try {
            const response = await this.client.get('/health');
            return response.status === 200;
        }
        catch (error) {
            console.error('Service connection test failed:', error);
            return false;
        }
    }
    /**
     * Analyze writing style of provided text
     */
    async analyzeStyle(text) {
        try {
            const response = await this.client.post('/api/style/analyze', {
                content: text
            });
            return {
                summary: response.data.summary || 'Analysis completed',
                details: response.data
            };
        }
        catch (error) {
            console.error('Style analysis failed:', error);
            throw new Error('Failed to analyze writing style');
        }
    }
    /**
     * Adapt content to match target style
     */
    async adaptContent(text, targetStyle) {
        try {
            const response = await this.client.post('/api/style/adapt', {
                content: text,
                target_style: targetStyle || 'default'
            });
            return response.data.adapted_content || text;
        }
        catch (error) {
            console.error('Content adaptation failed:', error);
            throw new Error('Failed to adapt content style');
        }
    }
    /**
     * Get user's style profile
     */
    async getStyleProfile() {
        try {
            const response = await this.client.get('/api/style/profile');
            return response.data;
        }
        catch (error) {
            console.error('Failed to get style profile:', error);
            throw new Error('Failed to load style profile');
        }
    }
}
exports.ServiceClient = ServiceClient;
//# sourceMappingURL=serviceClient.js.map