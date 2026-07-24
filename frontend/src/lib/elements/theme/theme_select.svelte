<script lang="ts">
	import { Theme } from '$lib/helper/light-dark';
	import { set_theme } from '$lib/helper/light-dark';
	import { get_theme } from '$lib/helper/light-dark';
	import { onMount } from 'svelte';

	const SYSTEM_ICON: string = '💻';
	const LIGHT_ICON: string = '☀️';
	const DARK_ICON: string = '🌙';

	let current_theme: Theme = $state(Theme.System);
	let is_open: boolean = $state(false);

	onMount(() => {
		set(get_theme());
	});

	function get_icon_from_theme(theme: Theme): string {
		switch (theme) {
			case Theme.Light:
				return LIGHT_ICON;
			case Theme.Dark:
				return DARK_ICON;
			case Theme.System:
			default:
				return SYSTEM_ICON;
		}
	}

	function select(theme: Theme): void {
		set_theme(theme);
		is_open = false;
		set(theme);
	}

	function set(theme: Theme): void {
		current_theme = theme;
	}
</script>

<details bind:open={is_open}>
	<summary aria-label="Theme">{get_icon_from_theme(current_theme)}</summary>

	<button type="button" onclick={() => select(Theme.System)}
		>{SYSTEM_ICON} System{current_theme === Theme.System ? ' ✓' : ''}</button
	>
	<button type="button" onclick={() => select(Theme.Light)}
		>{LIGHT_ICON} Light{current_theme === Theme.Light ? ' ✓' : ''}</button
	>
	<button type="button" onclick={() => select(Theme.Dark)}
		>{DARK_ICON} Dark{current_theme === Theme.Dark ? ' ✓' : ''}</button
	>
</details>

<style>
</style>
