<script lang="ts" generics="T extends InputType">
	import type { HTMLInputAttributes } from 'svelte/elements';
	import type { InputValue } from '$lib/helper/input';
	import type { InputType } from '$lib/helper/input';
	import { parseInputValue } from '$lib/helper/input';
	import { formatInputValue } from '$lib/helper/input';

	interface Props extends Omit<HTMLInputAttributes, 'id' | 'type' | 'value'> {
		id: string;
		label: string;
		type: T;
		value: InputValue<T>;
	}
	let { id, label, type, value = $bindable(), ...rest }: Props = $props();

	function oninput(event: Event & { currentTarget: HTMLInputElement }) {
		value = parseInputValue(type, event.currentTarget);
	}
</script>

<div>
	<label for={id}>{label}</label>
	<input
		class="normal-font"
		{id}
		{type}
		value={formatInputValue(type, value)}
		{oninput}
		{...rest}
	/>
</div>

<style>
	div {
		width: 100%;
		height: fit-content;
		position: relative;
		margin-top: 1.1rem;
	}

	input {
		background-color: var(--background-color-500);
		padding: 0.25rem;
		width: 100%;
		font-size: 1rem;
		border-radius: var(--border-radius);
		border: 0px;
		outline: 1px solid var(--line-color);
		box-shadow: 0 0 0 0 transparent;
		transition:
			box-shadow var(--transition-duration-fast),
			border-radius var(--transition-duration-fast);
	}

	input:hover {
		border-radius: 0;
		box-shadow: 0 0 0 2px var(--line-color);
	}

	input:focus {
		box-shadow: 0 0 0 2px var(--line-color);
	}

	label {
		background-color: var(--background-color-500);
		display: inline-block;
		inset-inline-start: 0.2rem;
		inset-block-start: -0.9rem;
		position: absolute;
		font-size: 1rem;
		padding: 0 0.3rem;
		border-radius: var(--border-radius);
	}
</style>
