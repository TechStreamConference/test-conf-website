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
	Range = 'range',
	Date = 'date',
	Time = 'time',
	DatetimeLocal = 'datetime-local',
	Month = 'month',
	Week = 'week',
	Color = 'color'
}

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
	[InputType.Range]: number;
	[InputType.Date]: Date;
	[InputType.Time]: string;
	[InputType.DatetimeLocal]: Date;
	[InputType.Month]: string;
	[InputType.Week]: string;
	[InputType.Color]: string;
}

export type InputValue<T extends InputType> = InputValueMap[T];

export function parseInputValue<T extends InputType>(
	type: T,
	element: HTMLInputElement
): InputValue<T> {
	switch (type) {
		case InputType.Number:
		case InputType.Range:
			return element.valueAsNumber as InputValue<T>;
		case InputType.Date:
			return (element.valueAsDate ?? new Date(NaN)) as InputValue<T>;
		case InputType.DatetimeLocal:
			return new Date(element.value) as InputValue<T>;
		default:
			return element.value as InputValue<T>;
	}
}

export function formatInputValue<T extends InputType>(type: T, value: InputValue<T>): string {
	switch (type) {
		case InputType.Number:
		case InputType.Range:
			return Number.isNaN(value) ? '' : String(value);
		case InputType.Date:
			return formatDate(toDate(value), 10, false);
		case InputType.DatetimeLocal:
			return formatDate(toDate(value), 16, true);
		default:
			return String(value);
	}
}

function toDate(value: unknown): Date {
	if (value instanceof Date) {
		return value;
	}
	if (typeof value === 'string' || typeof value === 'number') {
		return new Date(value);
	}
	return new Date(NaN);
}

function formatDate(value: Date, length: number, asLocalTime: boolean): string {
	if (Number.isNaN(value.getTime())) {
		return '';
	}
	const date = asLocalTime ? new Date(value.getTime() - value.getTimezoneOffset() * 60_000) : value;
	return date.toISOString().slice(0, length);
}

export function isMaxLengthVisible(maxLength: number, value: string): boolean {
	return value.length > maxLength * MAX_LENGTH_VISIBLE_FACTOR;
}

export function calculateMaxLengthColor(maxLength: number, value: string): string {
	if (maxLength * MAX_LENGTH_RED_FACTOR <= value.length) {
		return 'red';
	}
	if (maxLength * MAX_LENGTH_ORANGE_FACTOR <= value.length) {
		return 'orange';
	}
	return '';
}
