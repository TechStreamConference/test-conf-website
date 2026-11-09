import { readdirSync } from 'node:fs';
import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';

const SRC_DIR = path.resolve(import.meta.dirname, '..');
const GENERATED_TYPES_FILE = path.join(SRC_DIR, 'generated', 'types.gen.ts');

// The generated code and the tests are not part of the application code that calls the backend.
const EXCLUDED_DIRECTORIES = ['generated', 'tests'];

const SOURCE_FILE_PATTERN = /\.(ts|svelte)$/;

// An operation whose `query` has an optional `language` returns content in one language.
const LANGUAGE_QUERY_PATTERN = /^\s*language\?: string \| null;$/m;

/**
 * @brief Finds the generated SDK functions whose operation has a `language` query parameter.
 *
 * @returns the names of the SDK functions, for example `getGlobalsV1`
 */
function findContentOperations(): string[] {
    const generatedTypes = readFileSync(GENERATED_TYPES_FILE, 'utf-8');
    const operationPattern = /export type (\w+)Data = \{([\s\S]*?)\n\};/g;
    const operations: string[] = [];
    for (const [, typeName, body] of generatedTypes.matchAll(operationPattern)) {
        if (typeName !== undefined && body !== undefined && LANGUAGE_QUERY_PATTERN.test(body)) {
            operations.push(typeName.charAt(0).toLowerCase() + typeName.slice(1));
        }
    }
    return operations;
}

/**
 * @brief Lists the source files of the application, relative to `src`.
 *
 * @returns the paths of all `.ts` and `.svelte` files outside of the excluded directories
 */
function findSourceFiles(): string[] {
    return readdirSync(SRC_DIR, { recursive: true, encoding: 'utf-8' }).filter(
        (file) =>
            SOURCE_FILE_PATTERN.test(file) &&
            !EXCLUDED_DIRECTORIES.includes(file.split(path.sep)[0] ?? '')
    );
}

/**
 * @brief Finds the text between the parentheses of every call of a function.
 *
 * @param source the source code to search
 * @param functionName the name of the called function
 * @returns the arguments of each call, as written in the source
 */
function findCallArguments(source: string, functionName: string): string[] {
    const calls: string[] = [];
    for (const match of source.matchAll(new RegExp(`\\b${functionName}\\(`, 'g'))) {
        const start = match.index + match[0].length;
        let depth = 1;
        let end = start;
        while (depth > 0 && end < source.length) {
            depth += source[end] === '(' ? 1 : source[end] === ')' ? -1 : 0;
            end += 1;
        }
        calls.push(source.slice(start, end - 1));
    }
    return calls;
}

describe('calls of backend operations that return content in one language', () => {
    const operations = findContentOperations();

    it('finds the operations in the generated types', () => {
        expect(operations.length).toBeGreaterThan(0);
    });

    it('always pass the language query, so that the choice of the visitor is not forgotten', () => {
        const callsWithoutLanguageQuery: string[] = [];
        for (const file of findSourceFiles()) {
            const source = readFileSync(path.join(SRC_DIR, file), 'utf-8');
            for (const operation of operations) {
                for (const args of findCallArguments(source, operation)) {
                    if (!args.includes('query: getLanguageQuery(')) {
                        callsWithoutLanguageQuery.push(`${file}: ${operation}`);
                    }
                }
            }
        }

        expect(callsWithoutLanguageQuery).toEqual([]);
    });
});
