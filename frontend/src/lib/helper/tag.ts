import { to_kebab_case } from '$lib/helper/kebab';

export enum TagColor {
	Blue = 1,
	Blue_Light
}
const DEFAULT_COLOR: TagColor = TagColor.Blue;

export function get_tag_color(id: number): TagColor {
	return TagColor[id] ? id : DEFAULT_COLOR;
}

export interface ThemeColor {
	background: string;
	text: string;
}

export function get_theme_color(tag_color: TagColor): ThemeColor {
	return {
		background: `var(--tag-background-color-${to_kebab_case(TagColor[tag_color])})`,
		text: `var(--tag-text-color-${to_kebab_case(TagColor[tag_color])})`
	};
}
