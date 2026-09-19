<script lang="ts">
	import type { AriaAttributes } from 'svelte/elements';
	import type { HTMLInputAttributes } from 'svelte/elements';

	interface Props
		extends
			Pick<
				HTMLInputAttributes,
				'class' | 'disabled' | 'max' | 'min' | 'name' | 'required' | 'step'
			>,
			AriaAttributes {
		id: string;
		label: string;
		value: number;
	}
	let { id, label, value = $bindable(), ...rest }: Props = $props();
</script>

<div>
	<div class:header={true}>
		<label class:normal-font={true} for={id}>{label}</label>
		<output class:normal-font={true} for={id}>{value.toString()}</output>
	</div>
	<input {...rest} {id} type="range" bind:value />
</div>

<style>
	div {
		width: 100%;
		height: fit-content;
		margin-top: 0.5rem;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 0.5rem;
		margin-bottom: 0.4rem;
	}

	label {
		flex: 1 1 auto;
		min-width: 0;
		overflow: hidden;

		font-size: 1rem;
		white-space: nowrap;
		text-overflow: ellipsis;
	}

	output {
		flex: 0 0 auto;

		font-size: 0.9rem;
		color: var(--text-color-gray);
	}

	input {
		appearance: none;
		width: 100%;
		height: 0.3rem;

		background-color: var(--background-color-400);
		border-radius: var(--border-radius);

		cursor: pointer;

		transition: box-shadow var(--transition-duration-fast);
	}

	input::-webkit-slider-thumb {
		appearance: none;

		width: 1rem;
		height: 1rem;

		background-color: var(--line-color);
		border-radius: 50%;

		transition: box-shadow var(--transition-duration-fast);
	}

	input::-moz-range-thumb {
		width: 1rem;
		height: 1rem;

		background-color: var(--line-color);
		border: 0;
		border-radius: 50%;

		transition: box-shadow var(--transition-duration-fast);
	}

	input:hover::-webkit-slider-thumb,
	input:focus-visible::-webkit-slider-thumb {
		box-shadow: 0 0 0 2px var(--line-color);
	}

	input:hover::-moz-range-thumb,
	input:focus-visible::-moz-range-thumb {
		box-shadow: 0 0 0 2px var(--line-color);
	}

	input:disabled {
		opacity: 0.5;
		cursor: default;
	}
</style>
