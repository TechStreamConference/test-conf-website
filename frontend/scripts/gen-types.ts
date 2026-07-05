import { parseArgs } from 'node:util';
import { createClient } from '@hey-api/openapi-ts';

const {
	values: { i: input, o: output }
} = parseArgs({
	options: {
		i: {
			type: 'string',
			short: 'i'
		},
		o: {
			type: 'string',
			short: 'o'
		}
	}
});

if (!input || !output) {
	console.error('Usage: generate -i <input> -o <output>');
	process.exit(1);
}

await createClient({
	input: input,
	output: {
		clean: false,
		path: output
	}
});
