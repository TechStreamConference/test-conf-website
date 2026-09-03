import { snakeToKebab } from '$lib/helper/casing';

export enum TagColor {
	Blue = 1,
	Blue_Light
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
		background: `var(--tag-background-color-${snakeToKebab(TagColor[tagColor])})`,
		text: `var(--tag-text-color-${snakeToKebab(TagColor[tagColor])})`
	};
}
