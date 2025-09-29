import * as vscode from 'vscode';
import { ServiceClient } from '../services/serviceClient';
import { StyleTemplateManager } from '../services/styleTemplates';

/**
 * Text transformation commands for VSC-004
 * Implements BDD scenarios for style-based text transformation
 */
export class TextTransformationCommands {
    private serviceClient: ServiceClient;
    private templateManager: StyleTemplateManager;

    constructor(serviceClient: ServiceClient, context: vscode.ExtensionContext) {
        this.serviceClient = serviceClient;
        this.templateManager = new StyleTemplateManager(context);
    }

    /**
     * Register text transformation commands
     * BDD: Given the extension is activated, transformation commands should be available
     */
    registerCommands(context: vscode.ExtensionContext): void {
        // Style-based transformation command
        const transformStyleCommand = vscode.commands.registerCommand(
            'pseudoscribe.transformToStyle',
            this.handleStyleTransformation.bind(this)
        );

        // Quick style transformations
        const transformCasualCommand = vscode.commands.registerCommand(
            'pseudoscribe.transformToCasual',
            () => this.handleQuickTransformation('casual')
        );

        const transformFormalCommand = vscode.commands.registerCommand(
            'pseudoscribe.transformToFormal',
            () => this.handleQuickTransformation('formal')
        );

        const transformTechnicalCommand = vscode.commands.registerCommand(
            'pseudoscribe.transformToTechnical',
            () => this.handleQuickTransformation('technical')
        );

        // Save style template command
        const saveTemplateCommand = vscode.commands.registerCommand(
            'pseudoscribe.saveStyleTemplate',
            this.handleSaveStyleTemplate.bind(this)
        );

        // Apply style template command
        const applyTemplateCommand = vscode.commands.registerCommand(
            'pseudoscribe.applyStyleTemplate',
            this.handleApplyStyleTemplate.bind(this)
        );

        context.subscriptions.push(
            transformStyleCommand,
            transformCasualCommand,
            transformFormalCommand,
            transformTechnicalCommand,
            saveTemplateCommand,
            applyTemplateCommand
        );
    }

    /**
     * Handle custom style transformation
     * BDD: When I choose "Transform to Style", text should be replaced with transformed version
     */
    private async handleStyleTransformation(): Promise<void> {
        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active text editor found');
                return;
            }

            const selection = editor.selection;
            const selectedText = editor.document.getText(selection);

            if (!selectedText.trim()) {
                vscode.window.showWarningMessage('Please select text to transform');
                return;
            }

            // Get available style templates
            const templates = await this.templateManager.getAllTemplates();
            const templateOptions = templates.map(template => ({
                label: template.name,
                description: template.description,
                template: template
            }));

            // Add predefined style options
            const predefinedOptions = [
                { label: 'Casual', description: 'Informal, conversational tone' },
                { label: 'Formal', description: 'Professional, structured tone' },
                { label: 'Technical', description: 'Precise, technical language' },
                { label: 'Creative', description: 'Expressive, imaginative style' }
            ];

            const allOptions = [...predefinedOptions, ...templateOptions];

            const selectedStyle = await vscode.window.showQuickPick(allOptions, {
                placeHolder: 'Select target style for transformation'
            });

            if (!selectedStyle) return;

            // Get transformation strength
            const strengthInput = await vscode.window.showInputBox({
                prompt: 'Transformation strength (0.1 - 1.0)',
                value: '0.7',
                validateInput: (value) => {
                    const num = parseFloat(value);
                    if (isNaN(num) || num < 0.1 || num > 1.0) {
                        return 'Please enter a number between 0.1 and 1.0';
                    }
                    return null;
                }
            });

            if (!strengthInput) return;

            const strength = parseFloat(strengthInput);

            // Perform transformation
            await this.performTransformation(editor, selection, selectedText, selectedStyle, strength);

        } catch (error) {
            console.error('Style transformation failed:', error);
            vscode.window.showErrorMessage(`Style transformation failed: ${error}`);
        }
    }

    /**
     * Handle quick style transformations
     * BDD: When I choose "Transform to Casual Style", transformation should complete within 3 seconds
     */
    private async handleQuickTransformation(targetStyle: string): Promise<void> {
        const startTime = Date.now();

        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active text editor found');
                return;
            }

            const selection = editor.selection;
            const selectedText = editor.document.getText(selection);

            if (!selectedText.trim()) {
                vscode.window.showWarningMessage('Please select text to transform');
                return;
            }

            // Validate text length for performance requirement
            if (selectedText.length > 2500) { // ~500 words
                const proceed = await vscode.window.showWarningMessage(
                    'Selected text is quite long. Transformation may take longer than 3 seconds. Continue?',
                    'Yes', 'No'
                );
                if (proceed !== 'Yes') return;
            }

            const styleOption = {
                label: targetStyle.charAt(0).toUpperCase() + targetStyle.slice(1),
                description: `Transform to ${targetStyle} style`
            };

            await this.performTransformation(editor, selection, selectedText, styleOption, 0.7);

            // Verify performance requirement: < 3 seconds
            const elapsedTime = Date.now() - startTime;
            if (elapsedTime > 3000) {
                console.warn(`Transformation took ${elapsedTime}ms, exceeding 3s target`);
            }

        } catch (error) {
            console.error('Quick transformation failed:', error);
            vscode.window.showErrorMessage(`Transformation failed: ${error}`);
        }
    }

    /**
     * Perform the actual text transformation
     * BDD: Transformation should preserve original meaning and be undoable
     */
    private async performTransformation(
        editor: vscode.TextEditor,
        selection: vscode.Selection,
        originalText: string,
        styleOption: any,
        strength: number
    ): Promise<void> {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `Transforming to ${styleOption.label} style...`,
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0 });

            try {
                // Determine target style profile
                let targetStyleProfile;
                
                if (styleOption.template) {
                    // Use custom template
                    targetStyleProfile = styleOption.template.styleProfile;
                } else {
                    // Use predefined style
                    targetStyleProfile = this.getPredefinedStyleProfile(styleOption.label.toLowerCase());
                }

                progress.report({ increment: 30, message: "Analyzing original text..." });

                // Get original style analysis for comparison
                const originalAnalysis = await this.serviceClient.analyzeStyleDetailed(originalText);

                progress.report({ increment: 60, message: "Transforming text..." });

                // Perform transformation
                const transformationResult = await this.serviceClient.adaptTextToStyle(
                    originalText,
                    targetStyleProfile,
                    strength
                );

                progress.report({ increment: 90, message: "Applying changes..." });

                // Apply transformation with undo support
                await editor.edit((editBuilder) => {
                    editBuilder.replace(selection, transformationResult.adapted_text);
                });

                progress.report({ increment: 100 });

                // Show success message with comparison
                const message = `Text transformed successfully! ` +
                    `Original style: ${this.formatStyleSummary(originalAnalysis)} → ` +
                    `New style: ${this.formatStyleSummary(transformationResult.adapted_profile)}`;

                vscode.window.showInformationMessage(message);

            } catch (error) {
                throw error;
            }
        });
    }

    /**
     * Handle saving current text as a style template
     * BDD: When I choose "Save as Style Template", the style profile should be saved for future use
     */
    private async handleSaveStyleTemplate(): Promise<void> {
        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active text editor found');
                return;
            }

            const selection = editor.selection;
            const selectedText = editor.document.getText(selection);

            if (!selectedText.trim()) {
                vscode.window.showWarningMessage('Please select text to create template from');
                return;
            }

            if (selectedText.length < 100) {
                vscode.window.showWarningMessage('Please select more text (at least 100 characters) for a reliable style template');
                return;
            }

            // Get template name
            const templateName = await vscode.window.showInputBox({
                prompt: 'Enter a name for this style template',
                placeHolder: 'e.g., "Technical Blog Post", "Marketing Copy"',
                validateInput: (value) => {
                    if (!value.trim()) return 'Template name cannot be empty';
                    if (value.length > 50) return 'Template name must be 50 characters or less';
                    return null;
                }
            });

            if (!templateName) return;

            // Get optional description
            const description = await vscode.window.showInputBox({
                prompt: 'Enter a description for this template (optional)',
                placeHolder: 'Brief description of when to use this style...'
            });

            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "Creating style template...",
                cancellable: false
            }, async (progress) => {
                progress.report({ increment: 0 });

                // Analyze the selected text to create style profile
                progress.report({ increment: 30, message: "Analyzing text style..." });
                const styleProfile = await this.serviceClient.analyzeStyleDetailed(selectedText);

                progress.report({ increment: 70, message: "Saving template..." });

                // Save template
                await this.templateManager.saveTemplate({
                    name: templateName.trim(),
                    description: description?.trim(),
                    styleProfile: styleProfile,
                    sampleText: selectedText.substring(0, 200) + (selectedText.length > 200 ? '...' : '')
                });

                progress.report({ increment: 100 });
            });

            vscode.window.showInformationMessage(`Style template "${templateName}" saved successfully!`);

        } catch (error) {
            console.error('Failed to save style template:', error);
            vscode.window.showErrorMessage(`Failed to save style template: ${error}`);
        }
    }

    /**
     * Handle applying a saved style template
     * BDD: Template should appear in style template library and be applicable to other text
     */
    private async handleApplyStyleTemplate(): Promise<void> {
        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active text editor found');
                return;
            }

            const selection = editor.selection;
            const selectedText = editor.document.getText(selection);

            if (!selectedText.trim()) {
                vscode.window.showWarningMessage('Please select text to apply template to');
                return;
            }

            // Get available templates
            const templates = await this.templateManager.getAllTemplates();

            if (templates.length === 0) {
                vscode.window.showInformationMessage('No style templates found. Create one first by selecting text and using "Save as Style Template"');
                return;
            }

            // Show template selection
            const templateOptions = templates.map(template => ({
                label: template.name,
                description: template.description || 'No description',
                detail: `Created: ${template.createdAt.toLocaleDateString()}`,
                template: template
            }));

            const selectedTemplate = await vscode.window.showQuickPick(templateOptions, {
                placeHolder: 'Select a style template to apply'
            });

            if (!selectedTemplate) return;

            // Apply the template
            await this.performTransformation(
                editor,
                selection,
                selectedText,
                { label: selectedTemplate.template.name, template: selectedTemplate.template },
                0.8 // Higher strength for template application
            );

            // Update template usage
            await this.templateManager.updateTemplateUsage(selectedTemplate.template.id);

        } catch (error) {
            console.error('Failed to apply style template:', error);
            vscode.window.showErrorMessage(`Failed to apply style template: ${error}`);
        }
    }

    /**
     * Get predefined style profile for common styles
     */
    private getPredefinedStyleProfile(style: string): any {
        const profiles: { [key: string]: any } = {
            casual: {
                complexity: 0.3,
                formality: 0.2,
                tone: 0.7,
                readability: 0.8
            },
            formal: {
                complexity: 0.7,
                formality: 0.9,
                tone: 0.4,
                readability: 0.6
            },
            technical: {
                complexity: 0.8,
                formality: 0.8,
                tone: 0.3,
                readability: 0.5
            },
            creative: {
                complexity: 0.6,
                formality: 0.3,
                tone: 0.8,
                readability: 0.7
            }
        };

        return profiles[style] || profiles.casual;
    }

    /**
     * Format style analysis for display
     */
    private formatStyleSummary(analysis: any): string {
        const complexity = analysis.complexity ? `C:${(analysis.complexity * 100).toFixed(0)}%` : '';
        const formality = analysis.formality ? `F:${(analysis.formality * 100).toFixed(0)}%` : '';
        const tone = analysis.tone ? `T:${(analysis.tone * 100).toFixed(0)}%` : '';
        const readability = analysis.readability ? `R:${(analysis.readability * 100).toFixed(0)}%` : '';
        
        return [complexity, formality, tone, readability].filter(Boolean).join(', ');
    }

    /**
     * Dispose of resources
     */
    dispose(): void {
        // Clean up any resources if needed
    }
}
