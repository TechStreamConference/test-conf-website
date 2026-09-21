//
// Tech Stream Conference
// 2026
//
// Number parsing and validation helpers.
//

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
        console.log(
            `VALIDATOR: ${value.toString()} is not an unsigned int - using the default value`
        );
        return defaultValue;
    }

    return value;
}
