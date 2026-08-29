import { toDate } from '$lib/helper/date';
import { formatDate } from '$lib/helper/date';

/**
 * @brief this enum defines the type the HTNL input is working in.
 * it also maps directly to the HTML type string.
 */
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

const MAX_LENGTH_VISIBLE_FACTOR = 0.5;
const MAX_LENGTH_ORANGE_FACTOR = 0.75;
const MAX_LENGTH_RED_FACTOR = 0.9;

/**
 * @brief this set defines the input types that can have a maximum length.
 */
export const MAX_LENGTH_INPUT_TYPE = new Set<InputType>([
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
	[InputType.Date]: Date;
	[InputType.Time]: string;
	[InputType.DatetimeLocal]: Date;
	[InputType.Month]: string;
	[InputType.Week]: string;
	[InputType.Color]: string;
}
export type InputValue<T extends InputType> = InputValueMap[T];

/**
 * @brief this function parses the value of an input element based on its type.
 *
 * @param type the type the value should be parsed as.
 * @param element the input element to parse the value from.
 */
export function parseInputValue<T extends InputType>(
	type: T,
	element: HTMLInputElement
): InputValue<T> {
	switch (type) {
		case InputType.Number:
			return element.valueAsNumber as InputValue<T>;
		case InputType.Date:
			return (element.valueAsDate ?? new Date(NaN)) as InputValue<T>;
		case InputType.DatetimeLocal:
			return new Date(element.value) as InputValue<T>;
		default:
			return element.value as InputValue<T>;
	}
}

/**
 * @brief this generate a frontend string based on the provided type.
 *
 * @param type the type the value should be formatted from.
 * @param value the value formatted from.
 */
export function formatInputValue<T extends InputType>(type: T, value: InputValue<T>): string {
	switch (type) {
		case InputType.Number:
			return Number.isNaN(value) ? '' : String(value);
		case InputType.Date:
			return formatDate(toDate(value), 10, false);
		case InputType.DatetimeLocal:
			return formatDate(toDate(value), 16, true);
		default:
			return String(value);
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
