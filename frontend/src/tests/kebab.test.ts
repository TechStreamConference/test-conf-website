import { describe, expect, it } from 'vitest';
import { to_kebab_case } from '$lib/helper/kebab';

describe('to_kebab_case', () => {
	it('should lowercase an already-lowercase word', () => {
		expect(to_kebab_case('blue')).toBe('blue');
	});

	it('should lowercase an uppercase word', () => {
		expect(to_kebab_case('BLUE')).toBe('blue');
	});

	it('should replace a single underscore with a hyphen', () => {
		expect(to_kebab_case('Blue_Light')).toBe('blue-light');
	});

	it('should replace every underscore with a hyphen, not just the first', () => {
		expect(to_kebab_case('foo_bar_baz')).toBe('foo-bar-baz');
	});

	it('should handle consecutive underscores', () => {
		expect(to_kebab_case('foo__bar')).toBe('foo--bar');
	});

	it('should leave a string without underscores unchanged apart from casing', () => {
		expect(to_kebab_case('Blue')).toBe('blue');
	});

	it('should handle an empty string', () => {
		expect(to_kebab_case('')).toBe('');
	});

	it('should handle a string of only underscores', () => {
		expect(to_kebab_case('___')).toBe('---');
	});
});
