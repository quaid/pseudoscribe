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
const inputManager_1 = require("./input/inputManager");
const tokenManager_1 = require("./auth/tokenManager");
const serviceClient_1 = require("./services/serviceClient");
const activation_1 = require("./activation");
let viewManager;
let inputManager;
async function activate(context) {
    try {
        const tokenManager = new tokenManager_1.TokenManager(context);
        const serviceClient = new serviceClient_1.ServiceClient();
        const commandManager = new commandManager_1.CommandManager();
        viewManager = new viewManager_1.ViewManager(context);
        inputManager = new inputManager_1.InputManager(context);
        await (0, activation_1.handleActivation)(context, tokenManager, serviceClient, commandManager, viewManager, inputManager);
        return {
            viewManager,
            inputManager
        };
    }
    catch (error) {
        console.error('Failed to activate PseudoScribe extension:', error);
        vscode.window.showErrorMessage('Failed to activate PseudoScribe extension');
        // Return a dummy API on failure to satisfy the type contract
        return {
            viewManager: undefined,
            inputManager: undefined
        };
    }
}
exports.activate = activate;
function deactivate() {
    // Dispose view manager
    if (viewManager) {
        viewManager.dispose();
        viewManager = undefined;
    }
    // Dispose input manager
    if (inputManager) {
        inputManager.dispose();
        inputManager = undefined;
    }
    // Set context to indicate extension is deactivated
    vscode.commands.executeCommand('setContext', 'pseudoscribe:activated', false);
    console.log('PseudoScribe extension deactivated');
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map