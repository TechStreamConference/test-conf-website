// Using a JavaScript file here because the native TypeScript implementation in newer
// Node.js versions currently causes the following warning:
//
// `(node:8902) ExperimentalWarning: Type Stripping is an experimental feature and might change at any time`

import { parseArgs } from 'node:util';
import { createClient } from '@hey-api/openapi-ts';
import { access } from 'node:fs';


const {
	values: { input, output, generateOutput }
} = parseArgs({
	options: {
		input: {
			type: 'string',
			short: 'i'
		},
		output: {
			type: 'string',
			short: 'o'
		},
		generateOutput: {
			type: 'boolean',
			short: 'g'
		}
	}
});

if (!input || !output) {
	console.error('Usage: generate -i <input> -o <output>');
	process.exit(1);
}

if (!generateOutput) {
	try {
		await access(output)
	} catch {
		console.error(`Output directors "${output}" does not exist. use -g to generate it.`)
		process.exit(1)
	}
}

await createClient({
	input: input,
	output: {
		clean: false,
		path: output
	}
});
