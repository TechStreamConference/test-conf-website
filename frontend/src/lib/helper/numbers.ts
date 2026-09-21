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

/**
 * @brief Returns the value if it is an unsigned integer, otherwise the default value.
 * A number that is not an unsigned integer is logged.
 * @param value the value to check.
 * @param defaultValue the value returned for anything that is not an unsigned integer.
 * @returns the value or the default value.
 */
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
