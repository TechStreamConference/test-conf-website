<script lang="ts">
	import { Theme } from '$lib/helper/light_dark';
	import { set_theme } from '$lib/helper/light_dark';
	import { get_theme } from '$lib/helper/light_dark';
	import { onMount } from 'svelte';
	import Sun from '@lucide/svelte/icons/sun';
	import Moon from '@lucide/svelte/icons/moon';
	import SunMoon from '@lucide/svelte/icons/sun-moon';
	import Hourglass from '@lucide/svelte/icons/hourglass';

	let current_theme: Theme | undefined = $state(undefined);
	let is_open: boolean = $state(false);

	onMount(() => {
		current_theme = get_theme();
	});

	function select(theme: Theme): void {
		set_theme(theme);
		is_open = false;
		current_theme = theme;
	}
</script>

<details bind:open={is_open}>
	<summary aria-label="Theme selector">
		{#if current_theme === Theme.Dark}
			<Moon aria-hidden="true" />
		{:else if current_theme === Theme.Light}
			<Sun aria-hidden="true" />
		{:else if current_theme === Theme.System}
			<SunMoon aria-hidden="true" />
		{:else}
			<Hourglass aria-hidden="true" />
		{/if}
	</summary>

	<div>
		<button
			class:selected={current_theme === Theme.System}
			type="button"
			aria-pressed={current_theme === Theme.System}
			onclick={() => select(Theme.System)}><SunMoon aria-hidden="true" /> System</button
		>
		<button
			class:selected={current_theme === Theme.Light}
			type="button"
			aria-pressed={current_theme === Theme.Light}
			onclick={() => select(Theme.Light)}><Sun aria-hidden="true" /> Light</button
		>
		<button
			class:selected={current_theme === Theme.Dark}
			type="button"
			aria-pressed={current_theme === Theme.Dark}
			onclick={() => select(Theme.Dark)}><Moon aria-hidden="true" /> Dark</button
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
		color: var(--white-color);
	}

	div {
		background-color: var(--background-color-base);
		position: absolute;
		top: calc(100% + 0.8rem);
		inset-inline-end: 0;

		display: flex;
		flex-direction: column;
		gap: 0.4rem;

		min-width: 15rem;
		padding: 0.6rem;

		border-radius: var(--border-radius);

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
