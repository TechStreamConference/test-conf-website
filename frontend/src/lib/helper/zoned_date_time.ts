import { DateTime } from 'luxon';

export interface DateTimeContext {
	timeZone: string;
	locale: string;
}

export enum DateTimeKind {
	Instant = 'Instant',
	Floating = 'Floating'
}

export enum DateTimeFormat {
	DateShort = 'DateShort', // de : '13.6.2026', en : '6/13/2026'
	FullDateShort = 'FullDateShort', // de : '13.06.2026', en : '06/13/2026'
	DateLong = 'DateLong', // de : '13. Juni 2026', en : 'June 13, 2026'
	TimeShort = 'TimeShort', // de : '09:05', en : '9:05 AM'
	FullTimeShort = 'FullTimeShort', // de : '09:05', en : '09:05 AM'
	DateTimeShort = 'DateTimeShort', // de : '13.6.2026, 09:05', en : '6/13/2026, 9:05 AM'
	FullDateTimeShort = 'FullDateTimeShort', // de : '13.06.2026, 09:05', en : '06/13/2026, 09:05 AM'
	DateTimeLong = 'DateTimeLong' // de : '13. Juni 2026 um 09:05 MESZ', en : 'June 13, 2026 at 9:05 AM GMT+2'
}

const PRESET_BY_FORMAT: Record<DateTimeFormat, Intl.DateTimeFormatOptions> = {
	[DateTimeFormat.DateShort]: DateTime.DATE_SHORT,
	[DateTimeFormat.FullDateShort]: { year: 'numeric', month: '2-digit', day: '2-digit' },
	[DateTimeFormat.DateLong]: DateTime.DATE_FULL,
	[DateTimeFormat.TimeShort]: DateTime.TIME_SIMPLE,
	[DateTimeFormat.FullTimeShort]: { hour: '2-digit', minute: '2-digit' },
	[DateTimeFormat.DateTimeShort]: DateTime.DATETIME_SHORT,
	[DateTimeFormat.FullDateTimeShort]: {
		year: 'numeric',
		month: '2-digit',
		day: '2-digit',
		hour: '2-digit',
		minute: '2-digit'
	},
	[DateTimeFormat.DateTimeLong]: DateTime.DATETIME_FULL
};

const HTML_DATE_FORMAT = 'yyyy-MM-dd';
const HTML_TIME_FORMAT = 'HH:mm';
const HTML_DATE_TIME_FORMAT = "yyyy-MM-dd'T'HH:mm";
const HTML_MONTH_FORMAT = 'yyyy-MM';
const HTML_WEEK_FORMAT = "kkkk-'W'WW";

// Reference date used to anchor a bare time-of-day value; it carries no meaning of its own.
const FLOATING_TIME_REFERENCE_DATE = '1970-01-01';

/**
 * Wraps a point in time together with the timezone/locale needed to render it,
 * so callers never juggle raw `Date`/Luxon values and timezones themselves.
 *
 * Values built from a bare calendar concept (date, time, month, week) are `DateTimeKind.Floating`:
 * they never go through a timezone conversion, on the way in or out, because a calendar
 * day, a time of day, a month or a week has no instant of its own — converting one through
 * a timezone would shift it onto a different day depending on the offset. Only values that
 * represent a real instant (`DateTimeKind.Instant`) are projected into `timeZone`.
 */
export class ZonedDateTime<K extends DateTimeKind = DateTimeKind> {
	private constructor(
		private readonly value: DateTime,
		private readonly context: DateTimeContext,
		private readonly kind: K
	) {}

	static fromUtc<K extends DateTimeKind>(
		value: string,
		context: DateTimeContext,
		kind: K
	): ZonedDateTime<K> {
		return new ZonedDateTime(DateTime.fromISO(value, { zone: 'utc' }), context, kind);
	}

	static fromHtmlDateTime(
		value: string,
		context: DateTimeContext
	): ZonedDateTime<DateTimeKind.Instant> {
		return new ZonedDateTime<DateTimeKind.Instant>(
			DateTime.fromISO(value, { zone: context.timeZone }),
			context,
			DateTimeKind.Instant
		);
	}

	static fromHtmlDate(
		value: string,
		context: DateTimeContext
	): ZonedDateTime<DateTimeKind.Floating> {
		return new ZonedDateTime<DateTimeKind.Floating>(
			DateTime.fromISO(value, { zone: 'utc' }),
			context,
			DateTimeKind.Floating
		);
	}

	static fromHtmlTime(
		value: string,
		context: DateTimeContext
	): ZonedDateTime<DateTimeKind.Floating> {
		return new ZonedDateTime<DateTimeKind.Floating>(
			DateTime.fromISO(`${FLOATING_TIME_REFERENCE_DATE}T${value}`, { zone: 'utc' }),
			context,
			DateTimeKind.Floating
		);
	}

	static fromHtmlMonth(
		value: string,
		context: DateTimeContext
	): ZonedDateTime<DateTimeKind.Floating> {
		return new ZonedDateTime<DateTimeKind.Floating>(
			DateTime.fromISO(`${value}-01`, { zone: 'utc' }),
			context,
			DateTimeKind.Floating
		);
	}

	static fromHtmlWeek(
		value: string,
		context: DateTimeContext
	): ZonedDateTime<DateTimeKind.Floating> {
		return new ZonedDateTime<DateTimeKind.Floating>(
			DateTime.fromISO(`${value}-1`, { zone: 'utc' }),
			context,
			DateTimeKind.Floating
		);
	}

	private zoned(): DateTime {
		return this.kind === DateTimeKind.Floating
			? this.value
			: this.value.setZone(this.context.timeZone);
	}

	/** Serializes to UTC, for sending to the backend. */
	utc(): string {
		return this.value.toUTC().toISO() ?? '';
	}

	htmlDate(): string {
		return this.zoned().toFormat(HTML_DATE_FORMAT);
	}

	htmlTime(): string {
		return this.zoned().toFormat(HTML_TIME_FORMAT);
	}

	htmlDateTime(): string {
		return this.zoned().toFormat(HTML_DATE_TIME_FORMAT);
	}

	htmlMonth(): string {
		return this.zoned().toFormat(HTML_MONTH_FORMAT);
	}

	htmlWeek(): string {
		return this.zoned().toFormat(HTML_WEEK_FORMAT);
	}

	/** Renders for display, using the locale-aware Intl preset behind `format`. */
	format(format: DateTimeFormat): string {
		return this.zoned().setLocale(this.context.locale).toLocaleString(PRESET_BY_FORMAT[format]);
	}

	/** Whether this instant and `other` represent the same point in time. */
	equals(
		this: ZonedDateTime<DateTimeKind.Instant>,
		other: ZonedDateTime<DateTimeKind.Instant>
	): boolean {
		return this.value.toMillis() === other.value.toMillis();
	}

	/** Whether this instant occurs before `other`. */
	isBefore(
		this: ZonedDateTime<DateTimeKind.Instant>,
		other: ZonedDateTime<DateTimeKind.Instant>
	): boolean {
		return this.value.toMillis() < other.value.toMillis();
	}

	/** Whether this instant occurs after `other`. */
	isAfter(
		this: ZonedDateTime<DateTimeKind.Instant>,
		other: ZonedDateTime<DateTimeKind.Instant>
	): boolean {
		return this.value.toMillis() > other.value.toMillis();
	}

	/** Negative if this instant is before `other`, positive if after, zero if equal. */
	compareTo(
		this: ZonedDateTime<DateTimeKind.Instant>,
		other: ZonedDateTime<DateTimeKind.Instant>
	): number {
		return this.value.toMillis() - other.value.toMillis();
	}

	/**
	 * Renders `start`–`end` as a single locale-aware range (e.g. "13.–14.06.2026"), collapsing
	 * the parts both ends share, via the native `Intl.DateTimeFormat.formatRange`. `start` and
	 * `end` must share the same `DateTimeContext` — the range is rendered in `start`'s locale/zone.
	 */
	static formatRange(start: ZonedDateTime, end: ZonedDateTime, format: DateTimeFormat): string {
		if (
			start.context.timeZone !== end.context.timeZone ||
			start.context.locale !== end.context.locale
		) {
			// TODO: replace with the logging service once it exposes a client-side log function.
			console.log(
				"ZONED_DATE_TIME: formatRange called with mismatched contexts - rendering with start's context",
				{ start: start.context, end: end.context }
			);
		}

		const startZoned = start.zoned();
		const formatter = new Intl.DateTimeFormat(start.context.locale, {
			...PRESET_BY_FORMAT[format],
			timeZone: startZoned.zoneName ?? undefined
		});
		return formatter.formatRange(startZoned.toJSDate(), end.zoned().toJSDate());
	}
}
