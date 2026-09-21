import { describe, expect, it } from 'vitest';
import {
	InputType,
	formatInputValue,
	isDateInputType,
	isMaxLengthOrange,
	isMaxLengthRed,
	isMaxLengthVisible,
	parseDateInputValue,
	parseInputValue
} from '$lib/helper/input';
import type { DateTimeContext } from '$lib/helper/zoned_date_time';
import { ZonedDateTime } from '$lib/helper/zoned_date_time';

const BERLIN: DateTimeContext = { timeZone: 'Europe/Berlin', locale: 'de-DE' };

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
	it.each([0, 1, 5, 10, 20, 33, 100])(
		'never both true for maxLength=%i, across every value length up to 2x maxLength',
		(maxLength) => {
			for (let length = 0; length <= maxLength * 2 + 1; length++) {
				const value = 'a'.repeat(length);
				expect(
					isMaxLengthOrange(maxLength, value) && isMaxLengthRed(maxLength, value),
					`length=${length.toString()}`
				).toBe(false);
			}
		}
	);
});

describe('isDateInputType', () => {
	it.each([
		InputType.Date,
		InputType.Time,
		InputType.DatetimeLocal,
		InputType.Month,
		InputType.Week
	])('is true for %s', (type) => {
		expect(isDateInputType(type)).toBe(true);
	});

	it.each([
		InputType.Text,
		InputType.Password,
		InputType.Email,
		InputType.Search,
		InputType.Url,
		InputType.Tel,
		InputType.Number,
		InputType.Color
	])('is false for %s', (type) => {
		expect(isDateInputType(type)).toBe(false);
	});
});

describe('formatInputValue', () => {
	it('should format a text-like value as-is', () => {
		expect(formatInputValue(InputType.Text, 'hello world')).toBe('hello world');
		expect(formatInputValue(InputType.Text, '')).toBe('');
		expect(formatInputValue(InputType.Color, '#ff0000')).toBe('#ff0000');
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

	it('should format a TimeZoneUnaware date value as YYYY-MM-DD', () => {
		const value = ZonedDateTime.fromHtmlDate('2026-09-10', BERLIN);
		expect(formatInputValue(InputType.Date, value)).toBe('2026-09-10');
	});

	it('should format a TimeZoneUnaware time value as HH:mm', () => {
		const value = ZonedDateTime.fromHtmlTime('14:30', BERLIN);
		expect(formatInputValue(InputType.Time, value)).toBe('14:30');
	});

	it('should format a TimeZoneAware value as local YYYY-MM-DDTHH:mm', () => {
		const value = ZonedDateTime.fromHtmlDateTime('2026-06-13T09:05', BERLIN);
		expect(formatInputValue(InputType.DatetimeLocal, value)).toBe('2026-06-13T09:05');
	});

	it('should format a TimeZoneUnaware month value as YYYY-MM', () => {
		const value = ZonedDateTime.fromHtmlMonth('2026-09', BERLIN);
		expect(formatInputValue(InputType.Month, value)).toBe('2026-09');
	});

	it('should format a TimeZoneUnaware week value as YYYY-Www', () => {
		const value = ZonedDateTime.fromHtmlWeek('2026-W37', BERLIN);
		expect(formatInputValue(InputType.Week, value)).toBe('2026-W37');
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

	it('should read the raw string value for text-like inputs', () => {
		const element = createInputElement({ value: 'hello@example.com' });
		expect(parseInputValue(InputType.Email, element)).toBe('hello@example.com');
	});
});

describe('parseDateInputValue', () => {
	it('should parse a date input into a TimeZoneUnaware value', () => {
		const element = createInputElement({ value: '2026-09-10' });
		expect(parseDateInputValue(InputType.Date, element, BERLIN).htmlDate()).toBe('2026-09-10');
	});

	it('should parse a time input into a TimeZoneUnaware value', () => {
		const element = createInputElement({ value: '14:30' });
		expect(parseDateInputValue(InputType.Time, element, BERLIN).htmlTime()).toBe('14:30');
	});

	it('should parse a month input into a TimeZoneUnaware value', () => {
		const element = createInputElement({ value: '2026-09' });
		expect(parseDateInputValue(InputType.Month, element, BERLIN).htmlMonth()).toBe('2026-09');
	});

	it('should parse a week input into a TimeZoneUnaware value', () => {
		const element = createInputElement({ value: '2026-W37' });
		expect(parseDateInputValue(InputType.Week, element, BERLIN).htmlWeek()).toBe('2026-W37');
	});

	it('should parse a datetime-local input into a TimeZoneAware, converted via the given timezone', () => {
		const element = createInputElement({ value: '2026-06-13T09:05' });
		expect(parseDateInputValue(InputType.DatetimeLocal, element, BERLIN).utc()).toBe(
			'2026-06-13T07:05:00.000Z'
		);
	});

	it('should shift the UTC day when the local wall-clock time is close to midnight', () => {
		// 2026-09-10 23:30 in New York (UTC-4 in September) is already 2026-09-11 in UTC.
		const element = createInputElement({ value: '2026-09-10T23:30' });
		const result = parseDateInputValue(InputType.DatetimeLocal, element, {
			timeZone: 'America/New_York',
			locale: 'en-US'
		});
		expect(result.utc()).toBe('2026-09-11T03:30:00.000Z');
	});
});
