export function isNumber(value: unknown): value is number {
	return typeof value === 'number';
}

export function isUnsignedInt(value: number): boolean {
	return Number.isInteger(value) && value >= 0;
}

export function unsignedIntOr<T>(value: number | undefined | null, defaultValue: T): number | T {
	if (!isNumber(value)) {
		return defaultValue;
	}

	if (!isUnsignedInt(value)) {
		console.log(`VALIDATOR: ${value.toString()} is not unsigned int - set to undefined`);
		return defaultValue;
	}

	return value;
}
