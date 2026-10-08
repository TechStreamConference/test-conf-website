import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { readdirSync } from 'node:fs';
import { readFileSync } from 'node:fs';
import path from 'node:path';

const MESSAGES_DIRECTORY = path.resolve(import.meta.dirname, '../../messages');
const BASE_LANGUAGE = 'en'; // Has to match `baseLocale` in `project.inlang/settings.json`.
const SCHEMA_KEY = '$schema';
const SETTINGS_FILE = path.resolve(import.meta.dirname, '../../project.inlang/settings.json');
const PLACEHOLDER_PATTERN = /\{([^{}]*)\}/g; // Also matches an empty `{}`, so it can be reported.
const KEY_POSTFIXES = ['alt', 'aria']; // Allowed last part of a key: `global_logoSmall_alt`, `menu_homepage_aria`. Add new ones here.
const KEY_PREFIXES = ['global', 'menu', 'test']; // Allowed first part (the scope) of a key: `global_logoBig_alt`. Add new ones here.
const KEY_PATTERN = new RegExp(
    `^[a-z][A-Za-z0-9]*_[a-z][A-Za-z0-9]*(?:_(?:${KEY_POSTFIXES.join('|')}))?$`
); // `scope_name` or `scope_name_postfix`, all parts in camelCase.
const PLACEHOLDER_NAME_PATTERN = /^[a-z][A-Za-z0-9]*$/; // camelCase.

type Messages = Record<string, string>;

interface InlangSettings {
    baseLocale: string;
    locales: string[];
}

/**
 * @brief Reads the inlang project settings.
 *
 * @returns the base locale and the locales of the project
 * @throws Error if the file does not contain a base locale and a list of locales
 */
function loadSettings(): InlangSettings {
    const parsed: unknown = JSON.parse(readFileSync(SETTINGS_FILE, 'utf-8'));
    if (typeof parsed !== 'object' || parsed === null) {
        throw new Error('The inlang settings are not a JSON object.');
    }

    const { baseLocale, locales } = parsed as Record<string, unknown>;
    if (typeof baseLocale !== 'string' || !Array.isArray(locales)) {
        throw new Error('The inlang settings need a "baseLocale" and a list of "locales".');
    }
    return {
        baseLocale,
        locales: (locales as unknown[]).filter(
            (locale): locale is string => typeof locale === 'string'
        )
    };
}

/**
 * @brief Reads a message file. The `$schema` entry is left out.
 * The order of the keys is the order in the file.
 *
 * @param fileName the name of the file in the messages directory
 * @returns the messages by key
 * @throws Error if the file is not a JSON object or a value is not a string
 */
function loadMessages(fileName: string): Messages {
    const parsed: unknown = JSON.parse(
        readFileSync(path.join(MESSAGES_DIRECTORY, fileName), 'utf-8')
    );
    if (typeof parsed !== 'object' || parsed === null) {
        throw new Error(`${fileName} is not a JSON object.`);
    }

    const messages: Messages = {};
    for (const [key, value] of Object.entries(parsed as Record<string, unknown>)) {
        if (key === SCHEMA_KEY) {
            continue;
        }
        if (typeof value !== 'string') {
            throw new Error(`The value of "${key}" in ${fileName} is not a string.`);
        }
        messages[key] = value;
    }
    return messages;
}

/**
 * @brief Finds the placeholders (`{name}`) of a message.
 *
 * @param text the text of the message
 * @returns the sorted placeholder names without repetitions. The order inside a text and how often a name appears may
 * differ between languages, because the values are passed by name.
 */
function getPlaceholders(text: string): string[] {
    return [
        ...new Set([...text.matchAll(PLACEHOLDER_PATTERN)].map((match) => match[1] ?? ''))
    ].sort();
}

function getPlaceholdersByKey(messages: Messages, keys: string[]): Record<string, string[]> {
    return Object.fromEntries(keys.map((key) => [key, getPlaceholders(messages[key] ?? '')]));
}

const BASE_FILE = `${BASE_LANGUAGE}.json`;
const FILE_NAMES = readdirSync(MESSAGES_DIRECTORY)
    .filter((fileName) => fileName.endsWith('.json'))
    .sort();
const OTHER_FILES = FILE_NAMES.filter((fileName) => fileName !== BASE_FILE);

describe('message files', () => {
    it('should contain the file of the base language', () => {
        expect(FILE_NAMES).toContain(BASE_FILE);
    });
});

describe('inlang settings', () => {
    const settings = loadSettings();

    it('should list exactly the languages that have a message file', () => {
        const fileLanguages = FILE_NAMES.map((fileName) => path.basename(fileName, '.json'));

        expect([...settings.locales].sort()).toEqual(fileLanguages);
    });

    it('should have the base language of this test as base locale', () => {
        expect(settings.baseLocale).toBe(BASE_LANGUAGE);
    });
});

describe.each(FILE_NAMES)('%s naming', (fileName) => {
    const messages = loadMessages(fileName);

    it(`${fileName}: should use the format scope_name or scope_name_postfix for every key (allowed postfixes: see KEY_POSTFIXES)`, () => {
        expect(Object.keys(messages).filter((key) => !KEY_PATTERN.test(key))).toEqual([]);
    });

    it(`${fileName}: should start every key with an allowed prefix (allowed prefixes: see KEY_PREFIXES)`, () => {
        const keysWithUnknownPrefix = Object.keys(messages).filter(
            (key) => !KEY_PREFIXES.includes(key.split('_')[0] ?? '')
        );

        expect(keysWithUnknownPrefix).toEqual([]);
    });

    it(`${fileName}: should sort the keys alphabetically (ignoring case, "_" before letters)`, () => {
        const keys = Object.keys(messages);
        const sortedKeys = [...keys].sort((a, b) => {
            const lowerA = a.toLowerCase();
            const lowerB = b.toLowerCase();
            if (lowerA === lowerB) {
                return 0;
            }
            return lowerA < lowerB ? -1 : 1;
        });

        expect(keys).toEqual(sortedKeys);
    });

    it(`${fileName}: should use camelCase for every placeholder`, () => {
        const invalidPlaceholders = Object.entries(messages).flatMap(([key, text]) =>
            getPlaceholders(text)
                .filter((name) => name.trim() !== '' && !PLACEHOLDER_NAME_PATTERN.test(name))
                .map((name) => `${key}: {${name}}`)
        );

        expect(invalidPlaceholders).toEqual([]);
    });
});

describe.each(FILE_NAMES)('%s placeholders', (fileName) => {
    it(`${fileName}: should have a name for every placeholder`, () => {
        const keysWithEmptyPlaceholder = Object.entries(loadMessages(fileName))
            .filter(([, text]) => getPlaceholders(text).some((name) => name.trim() === ''))
            .map(([key]) => key);

        expect(keysWithEmptyPlaceholder).toEqual([]);
    });
});

describe.each(OTHER_FILES)('%s', (fileName) => {
    const baseMessages = loadMessages(BASE_FILE);
    const messages = loadMessages(fileName);

    it(`${fileName}: should have the same keys as the base language, in the same order`, () => {
        expect(Object.keys(messages)).toEqual(Object.keys(baseMessages));
    });

    it(`${fileName}: should have the same placeholders as the base language for every key`, () => {
        const commonKeys = Object.keys(baseMessages).filter((key) => key in messages);

        expect(getPlaceholdersByKey(messages, commonKeys)).toEqual(
            getPlaceholdersByKey(baseMessages, commonKeys)
        );
    });
});
