import * as path from 'path';
import * as fs from 'fs';
import * as vscode from 'vscode';
import Mocha from 'mocha';
import { ExtensionApi } from '../../extension';

// Make the API globally available for tests
declare global {
    var extensionApi: ExtensionApi;
}

export function run(): Promise<void> {
	// Create the mocha test
	const mochaInstance = new Mocha({
		ui: 'tdd',
		color: true
	});

	// Add global setup and teardown
	mochaInstance.suite.beforeAll(async function (this: Mocha.Context) {
		this.timeout(15000); // Increase timeout for activation
		const extensionId = 'pseudoscribe.pseudoscribe-writer-assistant';
		const extension = vscode.extensions.getExtension(extensionId);
		if (!extension) {
			throw new Error(`Extension ${extensionId} not found.`);
		}
		const api = await extension.activate();
		(global as any).extensionApi = api;
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
		function findTestFiles(dir: string): string[] {
			const files: string[] = [];
			const items = fs.readdirSync(dir);
			
			for (const item of items) {
				const fullPath = path.join(dir, item);
				const stat = fs.statSync(fullPath);
				
				if (stat.isDirectory()) {
					files.push(...findTestFiles(fullPath));
				} else if (item.endsWith('.test.js')) {
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
			mochaInstance.run((failures: number) => {
				if (failures > 0) {
					reject(new Error(`${failures} tests failed.`));
				} else {
					resolve();
				}
			});
		} catch (err) {
			console.error('Error running tests:', err);
				reject(err);
		}
	});
}
