<script lang="ts">
	import type { HTMLInputAttributes } from 'svelte/elements';

	interface Props extends Omit<HTMLInputAttributes, 'id' | 'label' | 'type' | 'value' | 'checked'> {
		id: string;
		label: string;
		checked: boolean;
	}

	let { id, label, checked = $bindable(), ...rest }: Props = $props();
</script>

<div>
	<input {id} type="checkbox" bind:checked {...rest} />
	<label class="normal-font" for={id}>{label}</label>
</div>

<style>
	div {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
	}
	input {
		accent-color: var(--line-color);

		width: 1.1rem;
		height: 1.1rem;

		cursor: pointer;
		border-radius: var(--border-radius);

		transition:
			outline var(--transition-duration-fast),
			box-shadow var(--transition-duration-fast);
	}

	input:hover {
		outline: 2px solid var(--line-color);
		outline-offset: 2px;
	}

	input:focus-visible {
		outline: 2px solid var(--line-color);
		outline-offset: 2px;
	}

	label {
		font-size: 1rem;
	}
</style>
