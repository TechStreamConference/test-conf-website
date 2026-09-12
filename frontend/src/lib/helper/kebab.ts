export function to_kebab_case(value: string): string {
	return value.toLowerCase().replaceAll('_', '-');
}
