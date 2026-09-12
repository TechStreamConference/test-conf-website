import { describe, expect, it } from 'vitest';
import { toDate, formatDate } from '$lib/helper/date';

describe('toDate', () => {
	it('should return the same Date instance when given a Date', () => {
		const date = new Date('2026-09-02T20:51:00Z');
		expect(toDate(date)).toBe(date);
	});

	it('should parse an ISO date string', () => {
		const result = toDate('2026-09-02T20:51:00Z');
		expect(result).toBeInstanceOf(Date);
		expect(result.getTime()).toBe(Date.parse('2026-09-02T20:51:00Z'));
	});

	it('should create a Date from a timestamp number', () => {
		const timestamp = 1_756_800_000_000;
		expect(toDate(timestamp).getTime()).toBe(timestamp);
	});

	it('should return an invalid Date for an unparseable string', () => {
		expect(Number.isNaN(toDate('not a date').getTime())).toBe(true);
	});
});

describe('formatDate', () => {
	const utcDate = new Date('2026-09-02T20:51:30.123Z');

	it('should return an empty string for an invalid Date', () => {
		expect(formatDate(new Date(NaN), 10, false)).toBe('');
		expect(formatDate(new Date(NaN), 10, true)).toBe('');
	});

	it('should format the date part in UTC with length 10', () => {
		expect(formatDate(utcDate, 10, false)).toBe('2026-09-02');
	});

	it('should format date and time in UTC with length 16', () => {
		expect(formatDate(utcDate, 16, false)).toBe('2026-09-02T20:51');
	});

	it('should format the full ISO string in UTC with length 24', () => {
		expect(formatDate(utcDate, 24, false)).toBe('2026-09-02T20:51:30.123Z');
	});

	it('should not mutate the input date', () => {
		const date = new Date('2026-09-02T20:51:30.123Z');
		formatDate(date, 16, true);
		expect(date.getTime()).toBe(utcDate.getTime());
	});

	it('should keep the local calendar date when asLocalTime is true', () => {
		expect(formatDate(new Date(2026, 7, 30), 10, true)).toBe('2026-08-30');
	});

	it('should format as local time when asLocalTime is true', () => {
		const date = new Date('2026-09-02T20:51:30.123Z');
		const expected =
			`${String(date.getFullYear())}-` +
			`${String(date.getMonth() + 1).padStart(2, '0')}-` +
			`${String(date.getDate()).padStart(2, '0')}T` +
			`${String(date.getHours()).padStart(2, '0')}:` +
			String(date.getMinutes()).padStart(2, '0');
		expect(formatDate(date, 16, true)).toBe(expected);
	});
});
