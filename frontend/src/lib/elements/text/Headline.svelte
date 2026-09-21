<!--
    Tech Stream Conference
    2026

    Headline with an optional decorative line.
-->
<script lang="ts">
    import type { HTMLAttributes } from 'svelte/elements';
    import type { Snippet } from 'svelte';

    interface Props extends HTMLAttributes<HTMLParagraphElement> {
        children: Snippet;
        renderLine?: boolean;
    }

    const { children, renderLine = false, ...rest }: Props = $props();
</script>

<h2 {...rest} class:headline-font={true} class:render-line={renderLine}>
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
