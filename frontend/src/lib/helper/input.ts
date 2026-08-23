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

export interface InputValueMap {
	[InputType.Text]: string;
	[InputType.Password]: string;
	[InputType.Email]: string;
	[InputType.Search]: string;
	[InputType.Url]: string;
	[InputType.Tel]: string;
	[InputType.Number]: number;
	[InputType.Range]: number;
	[InputType.Date]: string;
	[InputType.Time]: string;
	[InputType.DatetimeLocal]: string;
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
		default:
			return element.value as InputValue<T>;
	}
}

export function formatInputValue<T extends InputType>(type: T, value: InputValue<T>): string {
	switch (type) {
		case InputType.Number:
		case InputType.Range:
			return Number.isNaN(value) ? '' : String(value);
		default:
			return String(value);
	}
}
