/**
 * @brief A color for the light and the dark theme. Every CSS color value is allowed, e.g. `#fff` or `var(--text-color)`.
 */
export interface LightDarkColor {
    light: string;
    dark: string;
}

/**
 * @brief A single color that is used in both themes, or a pair of colors, one for each theme.
 */
export type ThemeColor = string | LightDarkColor;

/**
 * @brief Converts a theme color into a CSS color value.
 * @param color the color, or undefined if nothing is set
 * @returns the CSS value; a pair becomes `light-dark(...)`, so it follows the `color-scheme` of the page
 */
export function toCssColor(color: ThemeColor | undefined): string | undefined {
    if (color === undefined || typeof color === 'string') {
        return color;
    }
    return `light-dark(${color.light}, ${color.dark})`;
}
