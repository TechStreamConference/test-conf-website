import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { readdirSync } from 'node:fs';
import { readFileSync } from 'node:fs';
import path from 'node:path';

const SOURCE_DIRECTORY = path.resolve(import.meta.dirname, '..');
const SOURCE_EXTENSIONS = ['.ts', '.js', '.svelte'];
const EXCLUDED_DIRECTORIES = ['paraglide', 'tests']; // Generated code, and tests that call the messages on purpose to compare them with `i18n`.
const MESSAGES_IMPORT_PATTERN =
    /import\s+(?!type\b)([^;]*?)\s+from\s+['"]\$paraglide\/messages(?:\.js)?['"]/g; // `import type` is left out, because it cannot be called.
const MESSAGES_NAMESPACE = 'm'; // The name under which Paraglide exports all messages (`import { m } from '$paraglide/messages'`).
const BLOCK_COMMENT_PATTERN = /\/\*[\s\S]*?\*\/|<!--[\s\S]*?-->/g;
const LINE_COMMENT_PATTERN = /^[ \t]*\/\/.*$/gm; // Only whole-line comments, so a `//` in a URL string does not hide a call behind it.
const IDENTIFIER_PATTERN = '[A-Za-z_$][\\w$]*';

interface DirectCall {
    line: number;
    call: string;
}

/**
 * @brief Replaces comments with blanks of the same length, so a mentioned `m.save()` is not found,
 * but the line numbers of the rest stay the same.
 *
 * @param source the content of a source file
 * @returns the source without the comments
 */
function blankComments(source: string): string {
    const blank = (comment: string): string => comment.replace(/[^\n]/g, ' ');
    return source.replace(BLOCK_COMMENT_PATTERN, blank).replace(LINE_COMMENT_PATTERN, blank);
}

/**
 * @brief Finds the local names under which a file imports the messages of Paraglide.
 *
 * @param source the content of a source file
 * @returns the names that hold all messages (`m`, `* as x`) and the names that are a single message each
 */
function findMessageImports(source: string): { namespaces: string[]; functions: string[] } {
    const namespaces: string[] = [];
    const functions: string[] = [];

    for (const [, bindings = ''] of source.matchAll(MESSAGES_IMPORT_PATTERN)) {
        const namespace = /\*\s*as\s+([\w$]+)/.exec(bindings)?.[1];
        if (namespace !== undefined) {
            namespaces.push(namespace);
        }

        const named = /\{([^}]*)\}/.exec(bindings)?.[1] ?? '';
        for (const entry of named.split(',')) {
            const [imported = '', local = imported] = entry
                .replace(/^\s*type\s+/, '')
                .trim()
                .split(/\s+as\s+/);
            if (imported === '') {
                continue;
            }
            (imported === MESSAGES_NAMESPACE ? namespaces : functions).push(local);
        }
    }
    return { namespaces, functions };
}

/**
 * @brief Finds the calls of a message that bypass `i18n`.
 * Passing a message to `i18n` (`i18n(m.global_save, languageTag)`) is no call and is not reported.
 *
 * @see i18n in `$lib/helper/translate`
 *
 * @param source the content of a source file
 * @returns every direct call with its line number
 */
export function findDirectMessageCalls(source: string): DirectCall[] {
    const code = blankComments(source);
    const { namespaces, functions } = findMessageImports(code);

    const patterns = [
        ...namespaces.map(
            (name) => new RegExp(`(?<![\\w$.])${name}\\s*\\.\\s*${IDENTIFIER_PATTERN}\\s*\\(`, 'g')
        ),
        ...functions.map((name) => new RegExp(`(?<![\\w$.])${name}\\s*\\(`, 'g'))
    ];

    return patterns
        .flatMap((pattern) => [...code.matchAll(pattern)])
        .map((match) => ({
            line: code.slice(0, match.index).split('\n').length,
            call: match[0].replace(/\s+/g, '')
        }))
        .sort((a, b) => a.line - b.line);
}

function findSourceFiles(): string[] {
    return readdirSync(SOURCE_DIRECTORY, { recursive: true, encoding: 'utf-8' })
        .filter((file) => SOURCE_EXTENSIONS.includes(path.extname(file)))
        .filter((file) => !EXCLUDED_DIRECTORIES.includes(file.split(path.sep)[0] ?? ''))
        .sort();
}

describe('direct message calls', () => {
    it('should not occur in any source file (use i18n from $lib/helper/translate instead)', () => {
        const directCalls = findSourceFiles().flatMap((file) =>
            findDirectMessageCalls(readFileSync(path.join(SOURCE_DIRECTORY, file), 'utf-8')).map(
                ({ line, call }) => `${file}:${String(line)}: ${call}`
            )
        );

        expect(directCalls).toEqual([]);
    });
});

describe('findDirectMessageCalls', () => {
    const IMPORT = `import { m } from '$paraglide/messages';\n`;

    it('should find a direct call of a message', () => {
        expect(findDirectMessageCalls(`${IMPORT}const text = m.global_save();`)).toEqual([
            { line: 2, call: 'm.global_save(' }
        ]);
    });

    it('should find a direct call with placeholders and a locale', () => {
        const source = `${IMPORT}const text = m.footer_copyright({ year: 2026 }, { locale: 'de' });`;

        expect(findDirectMessageCalls(source)).toHaveLength(1);
    });

    it('should find a direct call in the markup of a svelte file', () => {
        const source = `<script lang="ts">\n${IMPORT}</script>\n\n<p>{m.global_save()}</p>\n`;

        expect(findDirectMessageCalls(source)).toEqual([{ line: 5, call: 'm.global_save(' }]);
    });

    it('should find a call with whitespace between the parts', () => {
        expect(findDirectMessageCalls(`${IMPORT}m\n    .global_save\n    ();`)).toHaveLength(1);
    });

    it('should find a call through a namespace import', () => {
        const source = `import * as messages from '$paraglide/messages';\nmessages.global_save();`;

        expect(findDirectMessageCalls(source)).toEqual([
            { line: 2, call: 'messages.global_save(' }
        ]);
    });

    it('should find a call of a single imported message, also if it is renamed', () => {
        const source = `import { global_save, global_cancel as cancel } from '$paraglide/messages';\nglobal_save();\ncancel();`;

        expect(findDirectMessageCalls(source)).toEqual([
            { line: 2, call: 'global_save(' },
            { line: 3, call: 'cancel(' }
        ]);
    });

    it('should find a call inside a multi-line import', () => {
        const source = `import {\n    m\n} from '$paraglide/messages';\nm.global_save();`;

        expect(findDirectMessageCalls(source)).toHaveLength(1);
    });

    it('should not report a message that is passed to i18n', () => {
        const source = `${IMPORT}i18n(m.global_save, languageTag);\ni18n(m.footer_copyright, languageTag, { year: 2026 });`;

        expect(findDirectMessageCalls(source)).toEqual([]);
    });

    it('should not report a call in a comment', () => {
        const source = `${IMPORT}// m.global_save()\n/* m.global_save() */\n<!-- m.global_save() -->`;

        expect(findDirectMessageCalls(source)).toEqual([]);
    });

    it('should not report a call of another object named like a message', () => {
        const source = `${IMPORT}other.m.global_save();\nsomething.global_save();`;

        expect(findDirectMessageCalls(source)).toEqual([]);
    });

    it('should not report a file that does not import the messages', () => {
        expect(findDirectMessageCalls(`const m = { save: () => '' };\nm.save();`)).toEqual([]);
    });

    it('should not report a type import', () => {
        const source = `import type { m } from '$paraglide/messages';\nm.global_save();`;

        expect(findDirectMessageCalls(source)).toEqual([]);
    });
});
