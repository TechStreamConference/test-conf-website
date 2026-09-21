//
// Tech Stream Conference
// 2026
//
// Tag colors and their theme colors.
//

import { pascalToKebab } from '$lib/helper/casing';

export enum TagColor {
    Blue = 1,
    BlueLight
}
const DEFAULT_COLOR: TagColor = TagColor.Blue;

export function getTagColor(id: number): TagColor {
    return TagColor[id] ? id : DEFAULT_COLOR;
}

export interface ThemeColor {
    background: string;
    text: string;
}

export function getThemeColor(tagColor: TagColor): ThemeColor {
    return {
        background: `var(--tag-background-color-${pascalToKebab(TagColor[tagColor])})`,
        text: `var(--tag-text-color-${pascalToKebab(TagColor[tagColor])})`
    };
}
