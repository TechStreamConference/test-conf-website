<!--
    Tech Stream Conference
    2026

    Sub-headline.
-->
<script lang="ts">
    import type { HTMLAttributes } from 'svelte/elements';
    import type { Snippet } from 'svelte';

    interface Props extends HTMLAttributes<HTMLParagraphElement> {
        children: Snippet;
    }

    const { children, ...rest }: Props = $props();
</script>

<h4 {...rest} class:sub-headline-font={true}>
    {@render children()}
</h4>

<style>
    h4 {
        align-self: center;

        font-size: var(--subheadline-font-size);
    }
</style>
