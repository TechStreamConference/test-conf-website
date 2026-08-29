export function snakeToKebab(value: string): string {
	return value.toLowerCase().replaceAll('_', '-');
}
