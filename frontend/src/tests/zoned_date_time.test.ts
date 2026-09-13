import { describe, expect, it, vi } from 'vitest';
import { DateTimeFormat, DateTimeKind, ZonedDateTime } from '$lib/helper/zoned_date_time';
import type { DateTimeContext } from '$lib/helper/zoned_date_time';

const BERLIN_DE: DateTimeContext = { timeZone: 'Europe/Berlin', locale: 'de-DE' };
const BERLIN_EN: DateTimeContext = { timeZone: 'Europe/Berlin', locale: 'en-US' };
const NEW_YORK_DE: DateTimeContext = { timeZone: 'America/New_York', locale: 'de-DE' };

describe('fromHtmlDateTime', () => {
	it('converts a local wall-clock string into the correct UTC instant (summer / DST)', () => {
		const value = ZonedDateTime.fromHtmlDateTime('2026-06-13T09:05', BERLIN_DE);
		expect(value.utc()).toBe('2026-06-13T07:05:00.000Z');
	});

	it('converts a local wall-clock string into the correct UTC instant (winter / no DST)', () => {
		const value = ZonedDateTime.fromHtmlDateTime('2026-01-13T09:05', BERLIN_DE);
		expect(value.utc()).toBe('2026-01-13T08:05:00.000Z');
	});

	it('round-trips back to the same local string via htmlDateTime()', () => {
		const value = ZonedDateTime.fromHtmlDateTime('2026-06-13T09:05', BERLIN_DE);
		expect(value.htmlDateTime()).toBe('2026-06-13T09:05');
	});
});

describe('fromHtmlDate', () => {
	it('stores the calendar date as literal UTC, independent of the timezone', () => {
		const value = ZonedDateTime.fromHtmlDate('2026-09-10', NEW_YORK_DE);
		expect(value.utc()).toBe('2026-09-10T00:00:00.000Z');
	});

	it('round-trips back to the same date string', () => {
		const value = ZonedDateTime.fromHtmlDate('2026-09-10', BERLIN_DE);
		expect(value.htmlDate()).toBe('2026-09-10');
	});
});

describe('fromHtmlTime', () => {
	it('stores the bare time anchored to 1970-01-01, independent of the timezone', () => {
		const value = ZonedDateTime.fromHtmlTime('14:30', NEW_YORK_DE);
		expect(value.utc()).toBe('1970-01-01T14:30:00.000Z');
	});

	it('round-trips back to the same time string', () => {
		const value = ZonedDateTime.fromHtmlTime('14:30', BERLIN_DE);
		expect(value.htmlTime()).toBe('14:30');
	});
});

describe('fromHtmlMonth', () => {
	it('stores the month as the 1st, as literal UTC, independent of the timezone', () => {
		const value = ZonedDateTime.fromHtmlMonth('2026-09', NEW_YORK_DE);
		expect(value.utc()).toBe('2026-09-01T00:00:00.000Z');
	});

	it('round-trips back to the same month string', () => {
		const value = ZonedDateTime.fromHtmlMonth('2026-09', BERLIN_DE);
		expect(value.htmlMonth()).toBe('2026-09');
	});
});

describe('fromHtmlWeek', () => {
	it('resolves to the Monday of that ISO week, as literal UTC', () => {
		// ISO week 37 of 2026 starts on Monday, 2026-09-07.
		const value = ZonedDateTime.fromHtmlWeek('2026-W37', NEW_YORK_DE);
		expect(value.utc()).toBe('2026-09-07T00:00:00.000Z');
	});

	it('round-trips back to the same week string', () => {
		const value = ZonedDateTime.fromHtmlWeek('2026-W37', BERLIN_DE);
		expect(value.htmlWeek()).toBe('2026-W37');
	});

	it('uses the ISO week-numbering year, not the calendar year, at the year boundary', () => {
		// ISO week 1 of 2026 starts on Monday, 2025-12-29 - a date that still falls in
		// calendar year 2025, but belongs to week-numbering year 2026.
		const value = ZonedDateTime.fromHtmlWeek('2026-W01', BERLIN_DE);
		expect(value.utc()).toBe('2025-12-29T00:00:00.000Z');
		expect(value.htmlWeek()).toBe('2026-W01');
	});
});

describe('fromUtc', () => {
	it('reconstructs an Instant value and projects it into the given timezone', () => {
		const value = ZonedDateTime.fromUtc(
			'2026-06-13T07:05:00.000Z',
			BERLIN_DE,
			DateTimeKind.Instant
		);
		expect(value.htmlDateTime()).toBe('2026-06-13T09:05');
		expect(value.utc()).toBe('2026-06-13T07:05:00.000Z');
	});

	it('reconstructs a Floating value without projecting it into the given timezone', () => {
		const value = ZonedDateTime.fromUtc(
			'2026-09-10T00:00:00.000Z',
			NEW_YORK_DE,
			DateTimeKind.Floating
		);
		expect(value.htmlDate()).toBe('2026-09-10');
		expect(value.utc()).toBe('2026-09-10T00:00:00.000Z');
	});
});

describe('utc', () => {
	it('always serializes to a UTC ISO string, regardless of the context timezone', () => {
		const value = ZonedDateTime.fromHtmlDateTime('2026-06-13T09:05', NEW_YORK_DE);
		expect(value.utc().endsWith('Z')).toBe(true);
	});
});

describe('format', () => {
	// Reference instant: 2026-06-13, 09:05 local time in Europe/Berlin (CEST, UTC+2).
	const instantDe = ZonedDateTime.fromHtmlDateTime('2026-06-13T09:05', BERLIN_DE);
	const instantEn = ZonedDateTime.fromHtmlDateTime('2026-06-13T09:05', BERLIN_EN);

	it('renders DateShort', () => {
		expect(instantDe.format(DateTimeFormat.DateShort)).toBe('13.6.2026');
		expect(instantEn.format(DateTimeFormat.DateShort)).toBe('6/13/2026');
	});

	it('renders FullDateShort', () => {
		expect(instantDe.format(DateTimeFormat.FullDateShort)).toBe('13.06.2026');
		expect(instantEn.format(DateTimeFormat.FullDateShort)).toBe('06/13/2026');
	});

	it('renders DateMedium', () => {
		expect(instantDe.format(DateTimeFormat.DateMedium)).toBe('13. Juni 2026');
		expect(instantEn.format(DateTimeFormat.DateMedium)).toBe('Jun 13, 2026');
	});

	it('renders DateLong', () => {
		expect(instantDe.format(DateTimeFormat.DateLong)).toBe('13. Juni 2026');
		expect(instantEn.format(DateTimeFormat.DateLong)).toBe('June 13, 2026');
	});

	it('renders TimeShort', () => {
		expect(instantDe.format(DateTimeFormat.TimeShort)).toBe('09:05');
		expect(instantEn.format(DateTimeFormat.TimeShort)).toBe('9:05 AM');
	});

	it('renders FullTimeShort', () => {
		expect(instantDe.format(DateTimeFormat.FullTimeShort)).toBe('09:05');
		expect(instantEn.format(DateTimeFormat.FullTimeShort)).toBe('09:05 AM');
	});

	it('renders DateTimeShort', () => {
		expect(instantDe.format(DateTimeFormat.DateTimeShort)).toBe('13.6.2026, 09:05');
		expect(instantEn.format(DateTimeFormat.DateTimeShort)).toBe('6/13/2026, 9:05 AM');
	});

	it('renders FullDateTimeShort', () => {
		expect(instantDe.format(DateTimeFormat.FullDateTimeShort)).toBe('13.06.2026, 09:05');
		expect(instantEn.format(DateTimeFormat.FullDateTimeShort)).toBe('06/13/2026, 09:05 AM');
	});

	it('renders DateTimeMedium', () => {
		expect(instantDe.format(DateTimeFormat.DateTimeMedium)).toBe('13. Juni 2026, 09:05');
		expect(instantEn.format(DateTimeFormat.DateTimeMedium)).toBe('Jun 13, 2026, 9:05 AM');
	});

	it('renders DateTimeLong', () => {
		expect(instantDe.format(DateTimeFormat.DateTimeLong)).toBe('13. Juni 2026 um 09:05 MESZ');
		expect(instantEn.format(DateTimeFormat.DateTimeLong)).toBe('June 13, 2026 at 9:05 AM GMT+2');
	});

	it('renders a Floating date without needing zone projection', () => {
		const value = ZonedDateTime.fromHtmlDate('2026-06-13', BERLIN_DE);
		expect(value.format(DateTimeFormat.DateMedium)).toBe('13. Juni 2026');
	});
});

describe('formatRange', () => {
	it('collapses the shared parts of two dates in the same month', () => {
		const start = ZonedDateTime.fromHtmlDate('2026-06-13', BERLIN_DE);
		const end = ZonedDateTime.fromHtmlDate('2026-06-14', BERLIN_DE);
		expect(ZonedDateTime.formatRange(start, end, DateTimeFormat.FullDateShort)).toBe(
			'13.–14.06.2026'
		);
	});

	it('logs a warning but still renders when start/end contexts differ', () => {
		const logSpy = vi.spyOn(console, 'log').mockImplementation(() => undefined);
		const start = ZonedDateTime.fromHtmlDate('2026-06-13', BERLIN_DE);
		const end = ZonedDateTime.fromHtmlDate('2026-06-14', NEW_YORK_DE);

		const result = ZonedDateTime.formatRange(start, end, DateTimeFormat.FullDateShort);

		expect(logSpy).toHaveBeenCalledOnce();
		expect(result).toBe('13.–14.06.2026');
		logSpy.mockRestore();
	});

	it('does not log anything when start/end share the same context', () => {
		const logSpy = vi.spyOn(console, 'log').mockImplementation(() => undefined);
		const start = ZonedDateTime.fromHtmlDate('2026-06-13', BERLIN_DE);
		const end = ZonedDateTime.fromHtmlDate('2026-06-14', BERLIN_DE);

		ZonedDateTime.formatRange(start, end, DateTimeFormat.FullDateShort);

		expect(logSpy).not.toHaveBeenCalled();
		logSpy.mockRestore();
	});
});

describe('equals', () => {
	it('is true for the same instant represented in two different timezones', () => {
		const berlin = ZonedDateTime.fromHtmlDateTime('2026-06-13T09:05', BERLIN_DE);
		const utc = ZonedDateTime.fromHtmlDateTime('2026-06-13T07:05', { ...BERLIN_DE, timeZone: 'UTC' });
		expect(berlin.equals(utc)).toBe(true);
	});

	it('is false for different instants', () => {
		const a = ZonedDateTime.fromHtmlDateTime('2026-06-13T09:05', BERLIN_DE);
		const b = ZonedDateTime.fromHtmlDateTime('2026-06-13T09:06', BERLIN_DE);
		expect(a.equals(b)).toBe(false);
	});
});

describe('isBefore / isAfter / compareTo', () => {
	const earlier = ZonedDateTime.fromHtmlDateTime('2026-06-13T09:00', BERLIN_DE);
	const later = ZonedDateTime.fromHtmlDateTime('2026-06-13T10:00', BERLIN_DE);

	it('isBefore is true only for the earlier instant', () => {
		expect(earlier.isBefore(later)).toBe(true);
		expect(later.isBefore(earlier)).toBe(false);
		expect(earlier.isBefore(earlier)).toBe(false);
	});

	it('isAfter is true only for the later instant', () => {
		expect(later.isAfter(earlier)).toBe(true);
		expect(earlier.isAfter(later)).toBe(false);
		expect(earlier.isAfter(earlier)).toBe(false);
	});

	it('compareTo is negative, positive, or zero accordingly', () => {
		expect(earlier.compareTo(later)).toBeLessThan(0);
		expect(later.compareTo(earlier)).toBeGreaterThan(0);
		expect(earlier.compareTo(earlier)).toBe(0);
	});
});
