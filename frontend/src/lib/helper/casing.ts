//
// Tech Stream Conference
// 2026
//
// Conversions between casing styles.
//

export function snakeToKebab(value: string): string {
    return value.toLowerCase().replaceAll('_', '-');
}

export function pascalToKebab(value: string): string {
    return value.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase();
}
