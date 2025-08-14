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
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = __importStar(require("vscode"));
const commandManager_1 = require("./commands/commandManager");
const viewManager_1 = require("./views/viewManager");
let viewManager;
/**
 * Main extension entry point
 * Implements VSC-001: Command Integration
 */
async function activate(context) {
    try {
        // Initialize command manager
        const commandManager = new commandManager_1.CommandManager();
        await commandManager.registerCommands(context);
        // Initialize view manager
        viewManager = new viewManager_1.ViewManager(context);
        await viewManager.initializeViews();
        // Set context to indicate extension is activated
        vscode.commands.executeCommand('setContext', 'pseudoscribe:activated', true);
        // Show activation notification
        vscode.window.showInformationMessage('PseudoScribe Writer Assistant activated!');
        console.log('PseudoScribe extension activated successfully');
    }
    catch (error) {
        console.error('Failed to activate PseudoScribe extension:', error);
        vscode.window.showErrorMessage('Failed to activate PseudoScribe extension');
    }
}
exports.activate = activate;
function deactivate() {
    // Dispose view manager
    if (viewManager) {
        viewManager.dispose();
        viewManager = undefined;
    }
    // Set context to indicate extension is deactivated
    vscode.commands.executeCommand('setContext', 'pseudoscribe:activated', false);
    console.log('PseudoScribe extension deactivated');
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map