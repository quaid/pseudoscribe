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
exports.run = void 0;
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const vscode = __importStar(require("vscode"));
const mocha_1 = __importDefault(require("mocha"));
function run() {
    // Create the mocha test
    const mochaInstance = new mocha_1.default({
        ui: 'tdd',
        color: true
    });
    // Add global setup and teardown
    mochaInstance.suite.beforeAll(async function () {
        this.timeout(15000); // Increase timeout for activation
        const extensionId = 'pseudoscribe.pseudoscribe-writer-assistant';
        const extension = vscode.extensions.getExtension(extensionId);
        if (!extension) {
            throw new Error(`Extension ${extensionId} not found.`);
        }
        const api = await extension.activate();
        global.extensionApi = api;
        console.log('Test Setup: PseudoScribe extension activated and API captured.');
    });
    mochaInstance.suite.afterAll(async () => {
        // This is a bit of a hack, but there's no official deactivate API for tests
        await vscode.commands.executeCommand('workbench.action.closeAllEditors');
        console.log('Test Teardown: Closed all editors.');
    });
    const testsRoot = path.resolve(__dirname, '..');
    return new Promise((resolve, reject) => {
        // Simple recursive file finder for test files
        function findTestFiles(dir) {
            const files = [];
            const items = fs.readdirSync(dir);
            for (const item of items) {
                const fullPath = path.join(dir, item);
                const stat = fs.statSync(fullPath);
                if (stat.isDirectory()) {
                    files.push(...findTestFiles(fullPath));
                }
                else if (item.endsWith('.test.js')) {
                    files.push(fullPath);
                }
            }
            return files;
        }
        try {
            // Find all test files
            const testFiles = findTestFiles(testsRoot);
            // Add files to the test suite
            testFiles.forEach(f => mochaInstance.addFile(path.resolve(testsRoot, f)));
            // Run the mocha test
            mochaInstance.run((failures) => {
                if (failures > 0) {
                    reject(new Error(`${failures} tests failed.`));
                }
                else {
                    resolve();
                }
            });
        }
        catch (err) {
            console.error('Error running tests:', err);
            reject(err);
        }
    });
}
exports.run = run;
//# sourceMappingURL=index.js.map