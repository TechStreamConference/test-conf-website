import { validatorNotUnsignedInt } from '$logging/events.gen';
import { clientLogger } from '$logging/client';

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
 * @param origin where the value comes from, e.g. `input.Line.maxlength`. It is part of the log to find the caller.
 * @param defaultValue the value returned for anything that is not an unsigned integer.
 * @returns the value or the default value.
 */
export function unsignedIntOr(
    value: number | undefined | null,
    origin: string,
    defaultValue?: number
): number | undefined {
    if (!isNumber(value)) {
        return defaultValue;
    }

    if (!isUnsignedInt(value)) {
        clientLogger.warning(
            validatorNotUnsignedInt({
                origin,
                value: value.toString(),
                default_value: defaultValue
            })
        );
        return defaultValue;
    }

    return value;
}
