//
// Tech Stream Conference
// 2026
//
// Conversions between casing styles.
//

export function snakeToKebab(value: string): string {
    return value.toLowerCase().replaceAll('_', '-');
}

/**
 * @brief Converts a PascalCase or camelCase value to kebab-case.
 * @param value the value to convert.
 * @returns the value in kebab-case.
 */
export function pascalToKebab(value: string): string {
    return value.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase();
}
