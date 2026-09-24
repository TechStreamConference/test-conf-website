import type { DateTimeContext } from '$lib/helper/zoned-date-time';
import type { DateTimeKind } from '$lib/helper/zoned-date-time';
import { ZonedDateTime } from '$lib/helper/zoned-date-time';

// Share of the max length at which the character counter becomes visible, orange and red.
const MAX_LENGTH_VISIBLE_FACTOR = 0.5;
const MAX_LENGTH_ORANGE_FACTOR = 0.75;
const MAX_LENGTH_RED_FACTOR = 0.9;

export enum InputType {
    Text = 'text',
    Password = 'password',
    Email = 'email',
    Search = 'search',
    Url = 'url',
    Tel = 'tel',
    Number = 'number',
    Date = 'date',
    Time = 'time',
    DatetimeLocal = 'datetime-local',
    Month = 'month',
    Week = 'week',
    Color = 'color'
}

const DATE_INPUT_TYPE_VALUES = [
    InputType.Date,
    InputType.Time,
    InputType.DatetimeLocal,
    InputType.Month,
    InputType.Week
] as const;

/**
 * @brief The input types whose value is a `ZonedDateTime`.
 */
export type DateInputType = (typeof DATE_INPUT_TYPE_VALUES)[number];

/**
 * @brief Ties the `context` field to `T`: required for the date/time input types (they need a
 * `DateTimeContext` to parse the raw HTML input value into a `ZonedDateTime`), absent otherwise.
 */
export type InputContextProp<T extends InputType> = T extends DateInputType
    ? { context: DateTimeContext }
    : { context?: undefined };

export const INPUT_TYPES_WITH_MAX_LENGTH = new Set<InputType>([
    InputType.Text,
    InputType.Password,
    InputType.Email,
    InputType.Search,
    InputType.Tel,
    InputType.Url
]);

/**
 * @brief this interface defines the value types for each input type.
 */
export interface InputValueMap {
    [InputType.Text]: string;
    [InputType.Password]: string;
    [InputType.Email]: string;
    [InputType.Search]: string;
    [InputType.Url]: string;
    [InputType.Tel]: string;
    [InputType.Number]: number;
    [InputType.Date]: ZonedDateTime<DateTimeKind.TimeZoneUnaware>;
    [InputType.Time]: ZonedDateTime<DateTimeKind.TimeZoneUnaware>;
    [InputType.DatetimeLocal]: ZonedDateTime<DateTimeKind.TimeZoneAware>;
    [InputType.Month]: ZonedDateTime<DateTimeKind.TimeZoneUnaware>;
    [InputType.Week]: ZonedDateTime<DateTimeKind.TimeZoneUnaware>;
    [InputType.Color]: string;
}
export type InputValue<T extends InputType> = InputValueMap[T];

export function isDateInputType(type: InputType): type is DateInputType {
    return (DATE_INPUT_TYPE_VALUES as readonly InputType[]).includes(type);
}

type DateInputParser<T extends DateInputType> = (
    value: string,
    context: DateTimeContext
) => InputValue<T>;

// One parser per date input type, so that TypeScript checks each return type against
// `InputValueMap` individually instead of against the intersection of all of them.
const DATE_INPUT_PARSERS: { [K in DateInputType]: DateInputParser<K> } = {
    [InputType.Date]: (value, context) => ZonedDateTime.fromHtmlDate(value, context),
    [InputType.Time]: (value, context) => ZonedDateTime.fromHtmlTime(value, context),
    [InputType.DatetimeLocal]: (value, context) => ZonedDateTime.fromHtmlDateTime(value, context),
    [InputType.Month]: (value, context) => ZonedDateTime.fromHtmlMonth(value, context),
    [InputType.Week]: (value, context) => ZonedDateTime.fromHtmlWeek(value, context)
};

/**
 * @brief Parses the raw value of a date/time input element into a `ZonedDateTime`.
 *
 * @param type the date/time input type of the element.
 * @param element the native input element the value is read from.
 * @param context the timezone and locale the value is interpreted in.
 * @returns the parsed value, typed according to the input type.
 */
export function parseDateInputValue<T extends DateInputType>(
    type: T,
    element: HTMLInputElement,
    context: DateTimeContext
): InputValue<T> {
    return DATE_INPUT_PARSERS[type](element.value, context);
}

/**
 * @brief Parses the raw value of a non-date input element into its typed value.
 *
 * @param type the input type of the element.
 * @param element the native input element the value is read from.
 * @returns the number for number inputs, otherwise the raw string value.
 */
export function parseInputValue<T extends Exclude<InputType, DateInputType>>(
    type: T,
    element: HTMLInputElement
): InputValue<T> {
    switch (type) {
        case InputType.Number:
            return element.valueAsNumber as InputValue<T>;
        default:
            return element.value as InputValue<T>;
    }
}

/**
 * @brief this generate a frontend string based on the provided type.
 *
 * @param type the type the value should be formatted from.
 * @param value the value formatted from.
 * @returns the formatted string, suitable for the native input's `value` attribute.
 */
export function formatInputValue<T extends InputType>(type: T, value: InputValue<T>): string {
    switch (type) {
        case InputType.Number:
            return typeof value === 'number' && !Number.isNaN(value) ? String(value) : '';
        case InputType.Date:
            return (value as ZonedDateTime).htmlDate();
        case InputType.Time:
            return (value as ZonedDateTime).htmlTime();
        case InputType.DatetimeLocal:
            return (value as ZonedDateTime).htmlDateTime();
        case InputType.Month:
            return (value as ZonedDateTime).htmlMonth();
        case InputType.Week:
            return (value as ZonedDateTime).htmlWeek();
        default:
            return typeof value === 'string' ? value : '';
    }
}

/**
 * @brief Whether the character counter should be shown.
 * @param maxLength the max length of the input.
 * @param value the current value of the input.
 * @returns true once the value has reached the visibility threshold of the max length.
 */
export function isMaxLengthVisible(maxLength: number, value: string): boolean {
    return value.length >= maxLength * MAX_LENGTH_VISIBLE_FACTOR;
}

/**
 * @brief Whether the character counter should be shown as a warning (orange).
 * @param maxLength the max length of the input.
 * @param value the current value of the input.
 * @returns true if the warning threshold is reached but the error threshold (red) is not.
 */
export function isMaxLengthOrange(maxLength: number, value: string): boolean {
    return (
        !isMaxLengthRed(maxLength, value) && maxLength * MAX_LENGTH_ORANGE_FACTOR <= value.length
    );
}
/**
 * @brief Whether the character counter should be shown as an error (red).
 * @param maxLength the max length of the input.
 * @param value the current value of the input.
 * @returns true once the value has reached the error threshold of the max length.
 */
export function isMaxLengthRed(maxLength: number, value: string): boolean {
    return maxLength * MAX_LENGTH_RED_FACTOR <= value.length;
}
