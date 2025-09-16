import * as vscode from 'vscode';

/**
 * Style template interface
 */
export interface StyleTemplate {
    id: string;
    name: string;
    description?: string;
    styleProfile: any;
    sampleText?: string;
    createdAt: Date;
    lastUsed: Date;
    usageCount: number;
}

/**
 * Style template manager for custom style templates
 * Implements BDD scenario: "Custom style template creation"
 */
export class StyleTemplateManager {
    private context: vscode.ExtensionContext;
    private readonly TEMPLATES_KEY = 'pseudoscribe_style_templates';

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    /**
     * Save a new style template
     * BDD: When I choose "Save as Style Template", the style profile should be saved for future use
     */
    async saveTemplate(templateData: {
        name: string;
        description?: string;
        styleProfile: any;
        sampleText?: string;
    }): Promise<StyleTemplate> {
        const templates = await this.getAllTemplates();
        
        // Check for duplicate names
        const existingTemplate = templates.find(t => t.name.toLowerCase() === templateData.name.toLowerCase());
        if (existingTemplate) {
            throw new Error(`A template with the name "${templateData.name}" already exists`);
        }

        const newTemplate: StyleTemplate = {
            id: this.generateId(),
            name: templateData.name,
            description: templateData.description,
            styleProfile: templateData.styleProfile,
            sampleText: templateData.sampleText,
            createdAt: new Date(),
            lastUsed: new Date(),
            usageCount: 0
        };

        templates.push(newTemplate);
        await this.saveTemplates(templates);

        return newTemplate;
    }

    /**
     * Get all saved style templates
     * BDD: Template should appear in style template library
     */
    async getAllTemplates(): Promise<StyleTemplate[]> {
        const templates = this.context.globalState.get(this.TEMPLATES_KEY, []) as StyleTemplate[];
        
        // Convert date strings back to Date objects (in case they were serialized)
        return templates.map(template => ({
            ...template,
            createdAt: new Date(template.createdAt),
            lastUsed: new Date(template.lastUsed)
        }));
    }

    /**
     * Get a specific template by ID
     */
    async getTemplate(id: string): Promise<StyleTemplate | null> {
        const templates = await this.getAllTemplates();
        return templates.find(t => t.id === id) || null;
    }

    /**
     * Update template usage statistics
     * BDD: Template usage should be tracked for analytics
     */
    async updateTemplateUsage(id: string): Promise<void> {
        const templates = await this.getAllTemplates();
        const template = templates.find(t => t.id === id);
        
        if (template) {
            template.lastUsed = new Date();
            template.usageCount++;
            await this.saveTemplates(templates);
        }
    }

    /**
     * Delete a style template
     */
    async deleteTemplate(id: string): Promise<boolean> {
        const templates = await this.getAllTemplates();
        const initialLength = templates.length;
        const filteredTemplates = templates.filter(t => t.id !== id);
        
        if (filteredTemplates.length < initialLength) {
            await this.saveTemplates(filteredTemplates);
            return true;
        }
        
        return false;
    }

    /**
     * Update an existing template
     */
    async updateTemplate(id: string, updates: Partial<StyleTemplate>): Promise<StyleTemplate | null> {
        const templates = await this.getAllTemplates();
        const templateIndex = templates.findIndex(t => t.id === id);
        
        if (templateIndex === -1) {
            return null;
        }

        // Merge updates with existing template
        templates[templateIndex] = {
            ...templates[templateIndex],
            ...updates,
            id: id, // Ensure ID cannot be changed
            createdAt: templates[templateIndex].createdAt // Preserve creation date
        };

        await this.saveTemplates(templates);
        return templates[templateIndex];
    }

    /**
     * Get templates sorted by usage
     */
    async getTemplatesByUsage(): Promise<StyleTemplate[]> {
        const templates = await this.getAllTemplates();
        return templates.sort((a, b) => b.usageCount - a.usageCount);
    }

    /**
     * Get recently used templates
     */
    async getRecentTemplates(limit: number = 5): Promise<StyleTemplate[]> {
        const templates = await this.getAllTemplates();
        return templates
            .sort((a, b) => b.lastUsed.getTime() - a.lastUsed.getTime())
            .slice(0, limit);
    }

    /**
     * Search templates by name or description
     */
    async searchTemplates(query: string): Promise<StyleTemplate[]> {
        const templates = await this.getAllTemplates();
        const lowerQuery = query.toLowerCase();
        
        return templates.filter(template => 
            template.name.toLowerCase().includes(lowerQuery) ||
            (template.description && template.description.toLowerCase().includes(lowerQuery))
        );
    }

    /**
     * Export templates to JSON
     */
    async exportTemplates(): Promise<string> {
        const templates = await this.getAllTemplates();
        return JSON.stringify(templates, null, 2);
    }

    /**
     * Import templates from JSON
     */
    async importTemplates(jsonData: string, overwrite: boolean = false): Promise<{imported: number, skipped: number}> {
        try {
            const importedTemplates = JSON.parse(jsonData) as StyleTemplate[];
            const existingTemplates = await this.getAllTemplates();
            
            let imported = 0;
            let skipped = 0;

            for (const template of importedTemplates) {
                // Validate template structure
                if (!this.isValidTemplate(template)) {
                    skipped++;
                    continue;
                }

                const existingTemplate = existingTemplates.find(t => t.name.toLowerCase() === template.name.toLowerCase());
                
                if (existingTemplate && !overwrite) {
                    skipped++;
                    continue;
                }

                // Generate new ID and update dates
                const newTemplate: StyleTemplate = {
                    ...template,
                    id: this.generateId(),
                    createdAt: new Date(),
                    lastUsed: new Date(),
                    usageCount: 0
                };

                if (existingTemplate && overwrite) {
                    // Replace existing template
                    const index = existingTemplates.findIndex(t => t.id === existingTemplate.id);
                    existingTemplates[index] = newTemplate;
                } else {
                    // Add new template
                    existingTemplates.push(newTemplate);
                }

                imported++;
            }

            await this.saveTemplates(existingTemplates);
            return { imported, skipped };

        } catch (error) {
            throw new Error(`Failed to import templates: ${error}`);
        }
    }

    /**
     * Get template statistics
     */
    async getStats(): Promise<{
        totalTemplates: number;
        totalUsage: number;
        mostUsedTemplate: StyleTemplate | null;
        oldestTemplate: StyleTemplate | null;
    }> {
        const templates = await this.getAllTemplates();
        
        if (templates.length === 0) {
            return {
                totalTemplates: 0,
                totalUsage: 0,
                mostUsedTemplate: null,
                oldestTemplate: null
            };
        }

        const totalUsage = templates.reduce((sum, t) => sum + t.usageCount, 0);
        const mostUsedTemplate = templates.reduce((max, t) => t.usageCount > max.usageCount ? t : max);
        const oldestTemplate = templates.reduce((oldest, t) => t.createdAt < oldest.createdAt ? t : oldest);

        return {
            totalTemplates: templates.length,
            totalUsage,
            mostUsedTemplate,
            oldestTemplate
        };
    }

    /**
     * Save templates to storage
     */
    private async saveTemplates(templates: StyleTemplate[]): Promise<void> {
        await this.context.globalState.update(this.TEMPLATES_KEY, templates);
    }

    /**
     * Generate unique ID for templates
     */
    private generateId(): string {
        return `template_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Validate template structure
     */
    private isValidTemplate(template: any): template is StyleTemplate {
        return (
            template &&
            typeof template.name === 'string' &&
            template.name.trim().length > 0 &&
            template.styleProfile &&
            typeof template.styleProfile === 'object'
        );
    }
}
