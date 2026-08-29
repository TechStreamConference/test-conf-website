import { describe, expect, it } from 'vitest';
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
