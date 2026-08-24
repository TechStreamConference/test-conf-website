export function is_number(value: unknown): value is number {
	return typeof value === 'number';
}

export function is_valid_unsigned_int(value: number): boolean {
	return Number.isInteger(value) && value >= 0;
}

export function validate_unsigned_int(value: number | undefined | null): number | undefined {
	if (!is_number(value)) {
		return undefined;
	}

	if (!is_valid_unsigned_int(value)) {
		console.log(`VALIDATOR: ${value.toString()} is not unsigned int - set to undefined`);
		return undefined;
	}

	return value;
}
