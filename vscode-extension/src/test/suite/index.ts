import * as path from 'path';
import * as fs from 'fs';

export function run(): Promise<void> {
	// Create the mocha test
	const { Mocha } = require('mocha');
	const mocha = new Mocha({
		ui: 'tdd',
		color: true
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
			testFiles.forEach((f: string) => mocha.addFile(f));

			// Run the mocha test
			mocha.run((failures: number) => {
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
