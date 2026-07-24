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

	<div>
		<button class="normal-font" type="button" onclick={() => select(Theme.System)}
			>{SYSTEM_ICON} System{current_theme === Theme.System ? ' ✓' : ''}</button
		>
		<button class="normal-font" type="button" onclick={() => select(Theme.Light)}
			>{LIGHT_ICON} Light{current_theme === Theme.Light ? ' ✓' : ''}</button
		>
		<button class="normal-font" type="button" onclick={() => select(Theme.Dark)}
			>{DARK_ICON} Dark{current_theme === Theme.Dark ? ' ✓' : ''}</button
		>
	</div>
</details>

<style>
	details {
		position: relative;
		display: inline-block;
	}

	summary {
		display: flex;
		align-items: center;
		justify-content: center;

		width: 4.4rem;
		height: 4.4rem;

		list-style: none;
		cursor: pointer;
		user-select: none;
		margin: 0.5rem;

		border: none;
		border-radius: var(--border-radius);
		background-color: transparent;
		color: var(--text-color);

		font-size: 2rem;

		transition: background-color var(--transition-duration);
	}

	summary:hover,
	summary:focus-visible {
		background-color: var(--primary-color-light);
	}

	div {
		position: absolute;
		top: calc(100% + 0.8rem);
		right: 0;

		display: flex;
		flex-direction: column;
		gap: 0.4rem;

		min-width: 14rem;
		padding: 0.6rem;

		border-radius: var(--border-radius);

		background-color: var(--background-color);
		box-shadow: 0 0.6rem 2rem rgba(0, 0, 0, 0.25);

		opacity: 0;
		transform: translateY(-0.5rem);
		pointer-events: auto;

		transition: opacity var(--transition-duration);
	}

	details[open] div {
		opacity: 1;
		transform: translateY(0);
		pointer-events: auto;
	}

	button {
		display: flex;
		align-items: center;
		gap: 0.8rem;

		width: 100%;
		padding: 0.8rem 1rem;

		border: none;
		border-radius: var(--border-radius);

		background: transparent;
		color: var(--text-color);

		text-align: left;
		cursor: pointer;
	}

	button:hover,
	button:focus-visible {
		background-color: var(--primary-color-light);
		color: var(--white-color);
		outline: none;
	}

	button:active {
		font-weight: 600;
	}
</style>
