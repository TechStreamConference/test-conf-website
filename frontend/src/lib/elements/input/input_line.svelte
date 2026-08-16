<script lang="ts">
	import type { HTMLInputAttributes } from 'svelte/elements';

	interface Props extends Omit<HTMLInputAttributes, 'id'> {
		id: string;
		label: string;
	}
	const { id, label, ...rest }: Props = $props();
</script>

<div>
	<label for={id}>{label}</label>
	<input class="normal-font" {id} {...rest} />
</div>

<style>
    div {
        position: relative;
        margin-block-start: 1.5rem;
        height: 2rem;
    }

    input {
        box-sizing: border-box;
        width: 100%;
        height: 100%;

        background-color: transparent;
        border-radius: var(--border-radius);
        border-color: var(--line-color);
    }

    label {
        position: absolute;

        inset-block-start: 50%;
        inset-inline-start: 0.2rem;

        transform: translateY(-50%);

        background-color: var(--background-color-500);
        border-radius: var(--border-radius);
        padding: 0.2rem;
        transition:
                inset-block-start var(--transition-duration-fast),
                transform  var(--transition-duration-fast),
                font-size var(--transition-duration-fast),
                inset-inline-start var(--transition-duration-fast);
    }

    div:has(input:hover) label,
    div:has(input:focus) label,
    div:has(input:placeholder-shown) label,
    div:has(input:has-value) label {
        inset-block-start: 0;
        transform: translateY(-50%);

        font-size: 0.8rem;
        inset-inline-start: 0.5rem;
    }
</style>
