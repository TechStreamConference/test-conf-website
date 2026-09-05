export function toDate(value: Date | string | number): Date {
	if (value instanceof Date) {
		return value;
	}
	if (typeof value === 'string' || typeof value === 'number') {
		return new Date(value);
	}
	return new Date(NaN);
}

export function formatDate(value: Date, length: number, asLocalTime: boolean): string {
	if (Number.isNaN(value.getTime())) {
		return '';
	}
	const date = asLocalTime ? new Date(value.getTime() - value.getTimezoneOffset() * 60_000) : value;
	return date.toISOString().slice(0, length);
}
