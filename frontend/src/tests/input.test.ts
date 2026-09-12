import { describe, expect, it } from 'vitest';
import {
	InputType,
	formatInputValue,
	isMaxLengthOrange,
	isMaxLengthRed,
	isMaxLengthVisible,
	parseInputValue
} from '$lib/helper/input';

describe('isMaxLengthVisible', () => {
	it('should be false when the value is well below the max length', () => {
		expect(isMaxLengthVisible(10, '')).toBe(false);
		expect(isMaxLengthVisible(10, 'ab')).toBe(false);
	});

	it('should be true exactly at half of the max length', () => {
		expect(isMaxLengthVisible(10, '12345')).toBe(true);
	});

	it('should be false just below half of the max length', () => {
		expect(isMaxLengthVisible(10, '1234')).toBe(false);
	});

	it('should be true once the value reaches the max length', () => {
		expect(isMaxLengthVisible(10, '1234567890')).toBe(true);
	});

	it('should be true once the value exceeds the max length', () => {
		expect(isMaxLengthVisible(10, '12345678901234')).toBe(true);
	});
});

describe('isMaxLengthRed', () => {
	it('should be false clearly below the red threshold', () => {
		expect(isMaxLengthRed(20, '12345')).toBe(false);
	});

	it('should be false just below the red threshold', () => {
		expect(isMaxLengthRed(20, 'a'.repeat(17))).toBe(false);
	});

	it('should be true exactly at the red threshold', () => {
		expect(isMaxLengthRed(20, 'a'.repeat(18))).toBe(true);
	});

	it('should be true once the max length is reached', () => {
		expect(isMaxLengthRed(20, 'a'.repeat(20))).toBe(true);
	});

	it('should be true once the value exceeds the max length', () => {
		expect(isMaxLengthRed(20, 'a'.repeat(25))).toBe(true);
	});
});

describe('isMaxLengthOrange', () => {
	it('should be false clearly below the orange threshold', () => {
		expect(isMaxLengthOrange(20, '12345')).toBe(false);
	});

	it('should be true exactly at the orange threshold', () => {
		expect(isMaxLengthOrange(20, 'a'.repeat(15))).toBe(true);
	});

	it('should be true between the orange and red thresholds', () => {
		expect(isMaxLengthOrange(20, 'a'.repeat(17))).toBe(true);
	});

	it('should be false once the red threshold is reached, even though the orange threshold is also met', () => {
		expect(isMaxLengthOrange(20, 'a'.repeat(18))).toBe(false);
	});

	it('should be false once the value exceeds the max length', () => {
		expect(isMaxLengthOrange(20, 'a'.repeat(25))).toBe(false);
	});
});

describe('isMaxLengthOrange and isMaxLengthRed interlocking', () => {
	it('should never both be true at once, for any max length and value length', () => {
		for (const maxLength of [0, 1, 5, 10, 20, 33, 100]) {
			for (let length = 0; length <= maxLength * 2 + 1; length++) {
				const value = 'a'.repeat(length);
				const orange = isMaxLengthOrange(maxLength, value);
				const red = isMaxLengthRed(maxLength, value);
				expect(
					orange && red,
					`maxLength=${maxLength.toString()}, length=${length.toString()}`
				).toBe(false);
			}
		}
	});
});

describe('formatInputValue', () => {
	it('should format a text-like value as-is', () => {
		expect(formatInputValue(InputType.Text, 'hello world')).toBe('hello world');
		expect(formatInputValue(InputType.Text, '')).toBe('');
		expect(formatInputValue(InputType.Color, '#ff0000')).toBe('#ff0000');
		expect(formatInputValue(InputType.Time, '13:45')).toBe('13:45');
	});

	it('should format a finite number as a string', () => {
		expect(formatInputValue(InputType.Number, 42)).toBe('42');
		expect(formatInputValue(InputType.Number, -5.25)).toBe('-5.25');
	});

	it('should format zero as "0" rather than an empty string', () => {
		expect(formatInputValue(InputType.Number, 0)).toBe('0');
	});

	it('should format NaN as an empty string', () => {
		expect(formatInputValue(InputType.Number, NaN)).toBe('');
	});

	it('should format a valid date as an ISO date (YYYY-MM-DD) in UTC', () => {
		expect(formatInputValue(InputType.Date, new Date('2026-09-02T20:51:00Z'))).toBe('2026-09-02');
	});

	it('should format an invalid date as an empty string', () => {
		expect(formatInputValue(InputType.Date, new Date(NaN))).toBe('');
	});

	it('should format a valid datetime-local value as local YYYY-MM-DDTHH:mm', () => {
		const date = new Date('2026-09-02T20:51:30.123Z');
		const expected =
			`${String(date.getFullYear())}-` +
			`${String(date.getMonth() + 1).padStart(2, '0')}-` +
			`${String(date.getDate()).padStart(2, '0')}T` +
			`${String(date.getHours()).padStart(2, '0')}:` +
			String(date.getMinutes()).padStart(2, '0');
		expect(formatInputValue(InputType.DatetimeLocal, date)).toBe(expected);
	});

	it('should format an invalid datetime-local value as an empty string', () => {
		expect(formatInputValue(InputType.DatetimeLocal, new Date(NaN))).toBe('');
	});
});

function createInputElement(
	overrides: Partial<Pick<HTMLInputElement, 'value' | 'valueAsNumber' | 'valueAsDate'>>
): HTMLInputElement {
	return {
		value: '',
		valueAsNumber: NaN,
		valueAsDate: null,
		...overrides
	} as HTMLInputElement;
}

describe('parseInputValue', () => {
	it('should read the numeric value for a number input', () => {
		const element = createInputElement({ valueAsNumber: 42 });
		expect(parseInputValue(InputType.Number, element)).toBe(42);
	});

	it('should be NaN for an empty number input', () => {
		const element = createInputElement({ valueAsNumber: NaN });
		expect(Number.isNaN(parseInputValue(InputType.Number, element))).toBe(true);
	});

	it('should read the parsed date for a date input', () => {
		const date = new Date('2026-09-02T00:00:00Z');
		const element = createInputElement({ valueAsDate: date });
		expect(parseInputValue(InputType.Date, element)).toBe(date);
	});

	it('should return an invalid date when a date input has no value', () => {
		const element = createInputElement({ valueAsDate: null });
		const result = parseInputValue(InputType.Date, element);
		expect(result).toBeInstanceOf(Date);
		expect(Number.isNaN(result.getTime())).toBe(true);
	});

	it('should parse the raw string as a local date-time for a datetime-local input', () => {
		const element = createInputElement({ value: '2026-09-02T20:51' });
		const result = parseInputValue(InputType.DatetimeLocal, element);
		expect(result.getTime()).toBe(new Date('2026-09-02T20:51').getTime());
	});

	it('should return an invalid date for an empty datetime-local input', () => {
		const element = createInputElement({ value: '' });
		const result = parseInputValue(InputType.DatetimeLocal, element);
		expect(Number.isNaN(result.getTime())).toBe(true);
	});

	it('should read the raw string value for text-like inputs', () => {
		const element = createInputElement({ value: 'hello@example.com' });
		expect(parseInputValue(InputType.Email, element)).toBe('hello@example.com');
	});
});
