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
		current_theme = get_theme();
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
		current_theme = theme;
	}
</script>

<details bind:open={is_open}>
	<summary aria-label="Theme selector">{get_icon_from_theme(current_theme)}</summary>

	<div>
		<button
			class:selected={current_theme === Theme.System}
			class="normal-font"
			type="button"
			aria-pressed={current_theme === Theme.System}
			onclick={() => select(Theme.System)}>{SYSTEM_ICON} System</button
		>
		<button
			class:selected={current_theme === Theme.Light}
			class="normal-font"
			type="button"
			aria-pressed={current_theme === Theme.Light}
			onclick={() => select(Theme.Light)}>{LIGHT_ICON} Light</button
		>
		<button
			class:selected={current_theme === Theme.Dark}
			class="normal-font"
			type="button"
			aria-pressed={current_theme === Theme.Dark}
			onclick={() => select(Theme.Dark)}>{DARK_ICON} Dark</button
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
		inset-inline-end: 0;

		display: flex;
		flex-direction: column;
		gap: 0.4rem;

		min-width: 15rem;
		padding: 0.6rem;

		border-radius: var(--border-radius);

		background-color: var(--background-color);
		box-shadow: 0 0.6rem 2rem rgba(0, 0, 0, 0.25);

		opacity: 0;
		transform: translateY(-0.5rem);
		pointer-events: none;

		transition:
			opacity var(--transition-duration),
			transform var(--transition-duration);
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

		text-align: start;
		cursor: pointer;
	}

	button.selected {
		font-weight: 700;
	}
	button.selected::after {
		content: '●';
		margin-inline-start: auto;
		color: var(--gray-color);
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
