import type { DateTimeContext } from '$lib/helper/zoned_date_time';
import { ZonedDateTime } from '$lib/helper/zoned_date_time';

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

export type DateInputType = (typeof DATE_INPUT_TYPE_VALUES)[number];

/**
 * Ties the `context` field to `T`: required for the date/time input types (they need a
 * `DateTimeContext` to parse the raw HTML input value into a `ZonedDateTime`), absent otherwise.
 */
export type InputContextProp<T extends InputType> = T extends DateInputType
	? { context: DateTimeContext }
	: { context?: undefined };

export const MAX_LENGTH_INPUT_TYPE = new Set<InputType>([
	InputType.Text,
	InputType.Password,
	InputType.Email,
	InputType.Search,
	InputType.Tel,
	InputType.Url
]);

export interface InputValueMap {
	[InputType.Text]: string;
	[InputType.Password]: string;
	[InputType.Email]: string;
	[InputType.Search]: string;
	[InputType.Url]: string;
	[InputType.Tel]: string;
	[InputType.Number]: number;
	[InputType.Date]: ZonedDateTime;
	[InputType.Time]: ZonedDateTime;
	[InputType.DatetimeLocal]: ZonedDateTime;
	[InputType.Month]: ZonedDateTime;
	[InputType.Week]: ZonedDateTime;
	[InputType.Color]: string;
}

export type InputValue<T extends InputType> = InputValueMap[T];

export function isDateInputType(type: InputType): type is DateInputType {
	return (DATE_INPUT_TYPE_VALUES as readonly InputType[]).includes(type);
}

export function parseDateInputValue<T extends DateInputType>(
	type: T,
	element: HTMLInputElement,
	context: DateTimeContext
): InputValue<T> {
	switch (type) {
		case InputType.Date:
			return ZonedDateTime.fromHtmlDate(element.value, context);
		case InputType.Time:
			return ZonedDateTime.fromHtmlTime(element.value, context);
		case InputType.DatetimeLocal:
			return ZonedDateTime.fromHtmlDateTime(element.value, context);
		case InputType.Month:
			return ZonedDateTime.fromHtmlMonth(element.value, context);
		case InputType.Week:
			return ZonedDateTime.fromHtmlWeek(element.value, context);
	}
}

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

export function isMaxLengthVisible(maxLength: number, value: string): boolean {
	return value.length >= maxLength * MAX_LENGTH_VISIBLE_FACTOR;
}

export function isMaxLengthOrange(maxLength: number, value: string): boolean {
	return !isMaxLengthRed(maxLength, value) && maxLength * MAX_LENGTH_ORANGE_FACTOR <= value.length;
}
export function isMaxLengthRed(maxLength: number, value: string): boolean {
	return maxLength * MAX_LENGTH_RED_FACTOR <= value.length;
}
