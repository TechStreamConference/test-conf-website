<script lang="ts">
	import type { HTMLTextareaAttributes } from 'svelte/elements';
	import { validate_unsigned_int } from '$lib/helper/numbers';
	import { calculateMaxLengthColor } from '$lib/helper/input';
	import { isMaxLengthVisible } from '$lib/helper/input';

	interface Props extends Omit<HTMLTextareaAttributes, 'id' | 'maxlength' | 'checked'> {
		id: string;
		label: string;
		maxlength?: number | undefined;
		value: string;
	}
	let { id, label, maxlength, value = $bindable(), ...rest }: Props = $props();

	const validMaxLength: number | undefined = $derived(validate_unsigned_int(maxlength));
</script>

<div>
	<label for={id}>{label}</label>
	<textarea class="normal-font" {id} maxlength={validMaxLength} bind:value {...rest}></textarea>
	{#if validMaxLength !== undefined}
		<p
			class:visible={isMaxLengthVisible(validMaxLength, value)}
			class="normal-font max-length-indicator {calculateMaxLengthColor(validMaxLength, value)}"
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

	textarea {
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

	textarea:hover {
		border-radius: 0;
		box-shadow: 0 0 0 2px var(--line-color);
	}

	textarea:focus {
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
