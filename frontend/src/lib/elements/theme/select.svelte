<script lang="ts">
	const SYSTEM_ICON: string = '💻';
	const LIGHT_ICON: string = '☀️';
	const DARK_ICON: string = '🌙';

	let current_icon: string = SYSTEM_ICON;
	let is_open: boolean = $state(false);

	function highlight_current_state(current: string): string {
		if (current === current_icon) {
			return ' ✓';
		}
		return '';
	}

	function select(theme: Theme): void {
		set_theme(theme);
		is_open = false;
	}
</script>

<details bind:open={is_open}>
	<summary aria-label="Theme">{current_icon}</summary>

	<button type="button" onclick={() => select(Theme.System)}
		>{SYSTEM_ICON} System{highlight_current_state(SYSTEM_ICON)}</button
	>
	<button type="button" onclick={() => select(Theme.Light)}
		>{LIGHT_ICON} Light{highlight_current_state(LIGHT_ICON)}</button
	>
	<button type="button" onclick={() => select(Theme.Dark)}
		>{DARK_ICON} Dark{highlight_current_state(DARK_ICON)}</button
	>
</details>

<style>
</style>
