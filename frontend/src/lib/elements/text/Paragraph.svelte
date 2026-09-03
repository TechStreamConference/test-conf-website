<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLAttributes } from 'svelte/elements';

	interface Props extends HTMLAttributes<HTMLParagraphElement> {
		children: Snippet;
		preserve_newlines?: boolean;
	}
	const { children, preserve_newlines = false, ...rest }: Props = $props();
</script>

<p {...rest} class:normal-font={true} class:preserve-newlines={preserve_newlines}>
	{@render children()}
</p>

<style>
	p {
		font-size: var(--paragraph-font-size);
	}

	.preserve-newlines {
		white-space: pre-line;
	}
</style>
