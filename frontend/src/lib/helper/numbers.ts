export function isNumber(value: unknown): value is number {
    return typeof value === 'number';
}

export function isUnsignedInt(value: number): boolean {
    return Number.isInteger(value) && value >= 0;
}

export function clampNumberToInt(
    value: number,
    min: number = Number.MIN_SAFE_INTEGER,
    max: number = Number.MAX_SAFE_INTEGER
): number {
    value = Math.round(value);
    min = Math.round(min);
    max = Math.round(max);

    return Math.min(Math.max(value, min), max);
}
