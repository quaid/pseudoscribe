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
exports.NotificationManager = void 0;
const vscode = __importStar(require("vscode"));
/**
 * NotificationManager handles user notifications and feedback
 * Supports VSC-001 user feedback requirements
 */
class NotificationManager {
    /**
     * Show information notification
     */
    showInfo(message) {
        vscode.window.showInformationMessage(`PseudoScribe: ${message}`);
    }
    /**
     * Show warning notification
     */
    showWarning(message) {
        vscode.window.showWarningMessage(`PseudoScribe: ${message}`);
    }
    /**
     * Show error notification
     */
    showError(message) {
        vscode.window.showErrorMessage(`PseudoScribe: ${message}`);
    }
    /**
     * Show progress notification with cancellation support
     */
    async showProgress(title, task) {
        return vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `PseudoScribe: ${title}`,
            cancellable: true
        }, task);
    }
    /**
     * Show quick pick selection
     */
    async showQuickPick(items, placeholder) {
        return vscode.window.showQuickPick(items, {
            placeHolder: placeholder
        });
    }
    /**
     * Show input box for user input
     */
    async showInputBox(prompt, placeholder) {
        return vscode.window.showInputBox({
            prompt,
            placeHolder: placeholder
        });
    }
}
exports.NotificationManager = NotificationManager;
//# sourceMappingURL=notificationManager.js.map