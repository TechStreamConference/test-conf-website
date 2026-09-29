<script lang="ts">
    import type { HTMLImgAttributes } from 'svelte/elements';

    interface Props extends HTMLImgAttributes {
        src: string;
        alt: string;
        height?: string | undefined;
        width?: string | undefined;
    }
    let { src, alt, height, width, ...rest }: Props = $props();

    $effect(() => {
        if (height !== undefined) {
            width = undefined;
        }
    });
</script>

<img {...rest} {src} {alt} style:width style:height />

<style>
    img {
        display: block;

        height: auto;
        width: auto;
    }
</style>
