<!--
    Tech Stream Conference
    2026

    Paragraph with optional preservation of line breaks.
-->
<script lang="ts">
    import type { HTMLAttributes } from 'svelte/elements';
    import type { Snippet } from 'svelte';

    interface Props extends HTMLAttributes<HTMLParagraphElement> {
        children: Snippet;
        preserveNewlines?: boolean;
    }
    const { children, preserveNewlines = false, ...rest }: Props = $props();
</script>

<p {...rest} class:normal-font={true} class:preserve-newlines={preserveNewlines}>
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
