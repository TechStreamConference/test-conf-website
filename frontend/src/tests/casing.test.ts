import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';

import { pascalToKebab } from '$lib/helper/casing';
import { snakeToKebab } from '$lib/helper/casing';

describe('snakeToKebab', () => {
    it('should lowercase an already-lowercase word', () => {
        expect(snakeToKebab('blue')).toBe('blue');
    });

    it('should lowercase an uppercase word', () => {
        expect(snakeToKebab('BLUE')).toBe('blue');
    });

    it('should replace a single underscore with a hyphen', () => {
        expect(snakeToKebab('Blue_Light')).toBe('blue-light');
    });

    it('should replace every underscore with a hyphen, not just the first', () => {
        expect(snakeToKebab('foo_bar_baz')).toBe('foo-bar-baz');
    });

    it('should handle consecutive underscores', () => {
        expect(snakeToKebab('foo__bar')).toBe('foo--bar');
    });

    it('should leave a string without underscores unchanged apart from casing', () => {
        expect(snakeToKebab('Blue')).toBe('blue');
    });

    it('should handle an empty string', () => {
        expect(snakeToKebab('')).toBe('');
    });

    it('should handle a string of only underscores', () => {
        expect(snakeToKebab('___')).toBe('---');
    });
});

describe('pascalToKebab', () => {
    it('should lowercase a single-word PascalCase word', () => {
        expect(pascalToKebab('Blue')).toBe('blue');
    });

    it('should insert a hyphen at a two-word PascalCase boundary', () => {
        expect(pascalToKebab('BlueLight')).toBe('blue-light');
    });

    it('should insert a hyphen at every word boundary for three or more words', () => {
        expect(pascalToKebab('DarkModeToggle')).toBe('dark-mode-toggle');
    });

    it('should work for camelCase input, not just PascalCase', () => {
        expect(pascalToKebab('camelCase')).toBe('camel-case');
    });

    it('should insert a hyphen between a digit and a following uppercase letter', () => {
        expect(pascalToKebab('Item2Go')).toBe('item2-go');
    });

    it('should leave an all-lowercase word unchanged', () => {
        expect(pascalToKebab('blue')).toBe('blue');
    });

    it('should handle an empty string', () => {
        expect(pascalToKebab('')).toBe('');
    });
});
