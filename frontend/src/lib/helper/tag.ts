//
// Tech Stream Conference
// 2026
//
// Tag colors and their theme colors.
//

import { pascalToKebab } from '$lib/helper/casing';

/**
 * @brief The available tag colors. The numeric values are the color ids of the backend.
 */
export enum TagColor {
    Blue = 1,
    BlueLight
}
const DEFAULT_COLOR: TagColor = TagColor.Blue;

export function tagColorFromId(id: number): TagColor {
    return TagColor[id] ? id : DEFAULT_COLOR;
}

/**
 * @brief The CSS values of the colors of a tag.
 */
export interface ThemeColor {
    background: string;
    text: string;
}

/**
 * @brief Gets the CSS custom properties that define the colors of a tag color.
 * @param tagColor the tag color.
 * @returns the background and text color as `var(...)` references.
 */
export function getTagThemeColor(tagColor: TagColor): ThemeColor {
    return {
        background: `var(--tag-background-color-${pascalToKebab(TagColor[tagColor])})`,
        text: `var(--tag-text-color-${pascalToKebab(TagColor[tagColor])})`
    };
}
