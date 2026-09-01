<script lang="ts" generics="T extends InputType">
	import type { AriaAttributes } from 'svelte/elements';
	import type { HTMLInputAttributes } from 'svelte/elements';
	import type { InputValue } from '$lib/helper/input';
	import type { InputType } from '$lib/helper/input';
	import { calculateOrange } from '$lib/helper/input';
	import { calculateRed } from '$lib/helper/input';
	import { MAX_LENGTH_INPUT_TYPE } from '$lib/helper/input';
	import { parseInputValue } from '$lib/helper/input';
	import { formatInputValue } from '$lib/helper/input';
	import { validate_unsigned_int } from '$lib/helper/numbers';
	import { isMaxLengthVisible } from '$lib/helper/input';

	interface Props
		extends
			Pick<
				HTMLInputAttributes,
				| 'autocomplete'
				| 'class'
				| 'disabled'
				| 'max'
				| 'min'
				| 'name'
				| 'placeholder'
				| 'readonly'
				| 'required'
				| 'step'
			>,
			AriaAttributes {
		id: string;
		label: string;
		type: T;
		maxlength?: number | undefined;
		value: InputValue<T>;
	}
	let { id, label, type, maxlength, value = $bindable(), ...rest }: Props = $props();

	const validMaxLength: number | undefined = $derived(validate_unsigned_int(maxlength));

	function oninput(event: Event & { currentTarget: HTMLInputElement }) {
		value = parseInputValue(type, event.currentTarget);
	}
</script>

<div>
	<label for={id}>{label}</label>
	<input
		{...rest}
		class:normal-font={true}
		{id}
		{type}
		value={formatInputValue(type, value)}
		{oninput}
		maxlength={validMaxLength}
	/>
	{#if validMaxLength !== undefined && MAX_LENGTH_INPUT_TYPE.has(type) && typeof value === 'string'}
		<p
			class:visible={isMaxLengthVisible(validMaxLength, value)}
			class:normal-font={true}
			class:orange={calculateOrange(validMaxLength, value)}
			class:red={calculateRed(validMaxLength, value)}
		>
			{value.length.toString()} / {validMaxLength.toString()}
		</p>
	{/if}
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
		border: 0;
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

	p {
		background-color: var(--background-color-500);
		position: absolute;
		display: inline-block;
		inset-inline-end: 0.2rem;
		inset-block-start: -0.9rem;
		padding: 0 0.3rem;
		font-size: 0.8rem;
		border-radius: var(--border-radius);
		opacity: 0;
		visibility: hidden;
		transition:
			opacity var(--transition-duration),
			visibility var(--transition-duration);
	}

	p.visible {
		opacity: 1;
		visibility: visible;
	}

	.orange {
		color: orange;
	}

	.red {
		color: red;
	}
</style>
