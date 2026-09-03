<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLAttributes } from 'svelte/elements';

	interface Props extends HTMLAttributes<HTMLParagraphElement> {
		children: Snippet;
		render_line?: boolean;
	}

	const { children, render_line = false, ...rest }: Props = $props();
</script>

<h2 {...rest} class:headline-font={true} class:render-line={render_line}>
	{@render children()}
</h2>

<style>
	h2 {
		display: inline-block;
		align-self: center;

		font-size: var(--headline-font-size);
	}

	h2.render-line::after {
		display: block;

		height: var(--headline-after-height);
		width: var(--headline-after-width);
		margin-inline-start: var(--headline-after-margin-start);

		content: '';
		background: var(--secondary-color);
	}
</style>
