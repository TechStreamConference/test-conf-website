import { DateTime } from 'luxon';

import { MissmatchZonedDateTimeContextError } from '$bff/errors';

export interface DateTimeContext {
    timeZone: string;
    locale: string;
}

/*
 * @brief Values built from a bare calendar concept (date, time, month, week) are `DateTimeKind.TimeZoneUnaware`:
 * they never go through a timezone conversion, on the way in or out, because a calendar
 * day, a time of day, a month or a week has no instant of its own — converting one through
 * a timezone would shift it onto a different day depending on the offset. Only values that
 * represent a real instant (`DateTimeKind.TimeZoneAware`) are projected into `timeZone`.
 */
export enum DateTimeKind {
    TimeZoneAware = 'TimeZoneAware',
    TimeZoneUnaware = 'TimeZoneUnaware'
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

// Luxon format tokens for the values of the native date/time inputs.
const HTML_DATE_FORMAT = 'yyyy-MM-dd';
const HTML_TIME_FORMAT = 'HH:mm';
const HTML_DATE_TIME_FORMAT = "yyyy-MM-dd'T'HH:mm";
const HTML_MONTH_FORMAT = 'yyyy-MM';
const HTML_WEEK_FORMAT = "kkkk-'W'WW";

// Reference date used to anchor a bare time-of-day value; it carries no meaning of its own.
const TIME_ZONE_UNAWARE_TIME_REFERENCE_DATE = '1970-01-01';

/**
 * @brief Wraps a point in time together with the timezone/locale needed to render it,
 * so callers never juggle raw `Date`/Luxon values and timezones themselves.
 */
export class ZonedDateTime<K extends DateTimeKind = DateTimeKind> {
    private constructor(
        private readonly value: DateTime,
        private readonly context: DateTimeContext,
        private readonly kind: K
    ) {}

    /**
     * @brief Reconstructs a value from a UTC timestamp, e.g. one received from the backend.
     * @param value the timestamp as an ISO 8601 string in UTC.
     * @param context the timezone and locale the value is rendered in.
     * @param kind whether the value is a real instant or a calendar concept without a timezone.
     * @returns the value.
     */
    static fromUtc<K extends DateTimeKind>(
        value: string,
        context: DateTimeContext,
        kind: K
    ): ZonedDateTime<K> {
        return new ZonedDateTime(DateTime.fromISO(value, { zone: 'utc' }), context, kind);
    }

    /**
     * @brief Parses the value of a `datetime-local` input. It is interpreted in the timezone of the context.
     * @param value the value of the input, e.g. `2026-06-13T09:05`.
     * @param context the timezone and locale of the user.
     * @returns the value as a real instant.
     */
    static fromHtmlDateTime(
        value: string,
        context: DateTimeContext
    ): ZonedDateTime<DateTimeKind.TimeZoneAware> {
        return new ZonedDateTime<DateTimeKind.TimeZoneAware>(
            DateTime.fromISO(value, { zone: context.timeZone }),
            context,
            DateTimeKind.TimeZoneAware
        );
    }

    /**
     * @brief Parses the value of a `date` input. It is not converted through a timezone.
     * @param value the value of the input, e.g. `2026-09-10`.
     * @param context the timezone and locale of the user.
     * @returns the value without timezone.
     */
    static fromHtmlDate(
        value: string,
        context: DateTimeContext
    ): ZonedDateTime<DateTimeKind.TimeZoneUnaware> {
        return new ZonedDateTime<DateTimeKind.TimeZoneUnaware>(
            DateTime.fromISO(value, { zone: 'utc' }),
            context,
            DateTimeKind.TimeZoneUnaware
        );
    }

    /**
     * @brief Parses the value of a `time` input. It is not converted through a timezone.
     * @param value the value of the input, e.g. `14:30`.
     * @param context the timezone and locale of the user.
     * @returns the value without timezone.
     */
    static fromHtmlTime(
        value: string,
        context: DateTimeContext
    ): ZonedDateTime<DateTimeKind.TimeZoneUnaware> {
        return new ZonedDateTime<DateTimeKind.TimeZoneUnaware>(
            DateTime.fromISO(`${TIME_ZONE_UNAWARE_TIME_REFERENCE_DATE}T${value}`, { zone: 'utc' }),
            context,
            DateTimeKind.TimeZoneUnaware
        );
    }

    /**
     * @brief Parses the value of a `month` input. It is not converted through a timezone.
     * @param value the value of the input, e.g. `2026-09`.
     * @param context the timezone and locale of the user.
     * @returns the value without timezone, set to the first day of the month.
     */
    static fromHtmlMonth(
        value: string,
        context: DateTimeContext
    ): ZonedDateTime<DateTimeKind.TimeZoneUnaware> {
        return new ZonedDateTime<DateTimeKind.TimeZoneUnaware>(
            DateTime.fromISO(`${value}-01`, { zone: 'utc' }),
            context,
            DateTimeKind.TimeZoneUnaware
        );
    }

    /**
     * @brief Parses the value of a `week` input. It is not converted through a timezone.
     * @param value the value of the input, e.g. `2026-W37`.
     * @param context the timezone and locale of the user.
     * @returns the value without timezone, set to the Monday of the week.
     */
    static fromHtmlWeek(
        value: string,
        context: DateTimeContext
    ): ZonedDateTime<DateTimeKind.TimeZoneUnaware> {
        return new ZonedDateTime<DateTimeKind.TimeZoneUnaware>(
            DateTime.fromISO(`${value}-1`, { zone: 'utc' }),
            context,
            DateTimeKind.TimeZoneUnaware
        );
    }

    /**
     * @brief Gets the value in the timezone of the context. A value without timezone is returned unchanged.
     * @returns the value to render.
     */
    private zoned(): DateTime {
        return this.kind === DateTimeKind.TimeZoneUnaware
            ? this.value
            : this.value.setZone(this.context.timeZone);
    }

    /**
     * @brief Serializes to UTC, for sending to the backend.
     * @returns the value as an ISO 8601 string in UTC
     */
    utc(): string {
        return this.value.toUTC().toISO() ?? '';
    }

    /**
     * @brief Formats the value for a `date` input.
     * @returns the value of the input, e.g. `2026-09-10`.
     */
    htmlDate(): string {
        return this.zoned().toFormat(HTML_DATE_FORMAT);
    }

    /**
     * @brief Formats the value for a `time` input.
     * @returns the value of the input, e.g. `14:30`.
     */
    htmlTime(): string {
        return this.zoned().toFormat(HTML_TIME_FORMAT);
    }

    /**
     * @brief Formats the value for a `datetime-local` input.
     * @returns the value of the input, e.g. `2026-06-13T09:05`.
     */
    htmlDateTime(): string {
        return this.zoned().toFormat(HTML_DATE_TIME_FORMAT);
    }

    /**
     * @brief Formats the value for a `month` input.
     * @returns the value of the input, e.g. `2026-09`.
     */
    htmlMonth(): string {
        return this.zoned().toFormat(HTML_MONTH_FORMAT);
    }

    /**
     * @brief Formats the value for a `week` input.
     * @returns the value of the input, e.g. `2026-W37`.
     */
    htmlWeek(): string {
        return this.zoned().toFormat(HTML_WEEK_FORMAT);
    }

    /**
     * @brief Renders for display, using the locale-aware Intl preset behind `format`.
     * @param format the preset used to render the value
     * @returns the localized, human-readable value
     */
    format(format: DateTimeFormat): string {
        return this.zoned().setLocale(this.context.locale).toLocaleString(PRESET_BY_FORMAT[format]);
    }

    /**
     * @brief Whether this instant and `other` represent the same point in time.
     * @param other the instant to compare with
     * @returns true if both represent the same point in time
     */
    equals(
        this: ZonedDateTime<DateTimeKind.TimeZoneAware>,
        other: ZonedDateTime<DateTimeKind.TimeZoneAware>
    ): boolean {
        return this.value.toMillis() === other.value.toMillis();
    }

    /**
     * @brief Whether this instant occurs before `other`.
     * @param other the instant to compare with
     * @returns true if this instant is earlier than `other`
     */
    isBefore(
        this: ZonedDateTime<DateTimeKind.TimeZoneAware>,
        other: ZonedDateTime<DateTimeKind.TimeZoneAware>
    ): boolean {
        return this.value.toMillis() < other.value.toMillis();
    }

    /**
     * @brief Whether this instant occurs after `other`.
     * @param other the instant to compare with
     * @returns true if this instant is later than `other`
     */
    isAfter(
        this: ZonedDateTime<DateTimeKind.TimeZoneAware>,
        other: ZonedDateTime<DateTimeKind.TimeZoneAware>
    ): boolean {
        return this.value.toMillis() > other.value.toMillis();
    }

    /**
     * @brief Compares this instant with `other`.
     * @param other the instant to compare with
     * @returns negative if this instant is before `other`, positive if after, zero if equal
     */
    compareTo(
        this: ZonedDateTime<DateTimeKind.TimeZoneAware>,
        other: ZonedDateTime<DateTimeKind.TimeZoneAware>
    ): number {
        return this.value.toMillis() - other.value.toMillis();
    }

    /**
     * @brief Renders `start`–`end` as a single locale-aware range (e.g. "13.–14.06.2026"), collapsing
     * the parts both ends share, via the native `Intl.DateTimeFormat.formatRange`. `start` and
     * `end` must share the same `DateTimeContext` — the range is rendered in `start`'s locale/zone.
     * @param start the beginning of the range
     * @param end the end of the range
     * @param format the preset used to render both ends
     * @returns the combined, localized range
     */
    static formatRange(start: ZonedDateTime, end: ZonedDateTime, format: DateTimeFormat): string {
        if (
            start.context.timeZone !== end.context.timeZone ||
            start.context.locale !== end.context.locale
        ) {
            throw new MissmatchZonedDateTimeContextError(
                'ZONED_DATE_TIME: formatRange called with mismatched contexts',
                start.context.locale,
                start.context.timeZone,
                end.context.locale,
                end.context.timeZone
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
