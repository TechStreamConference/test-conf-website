<script lang="ts">
	import type { HTMLImgAttributes } from 'svelte/elements';
	interface Props extends HTMLImgAttributes {
		src: string;
		alt: string;
		height?: string | undefined;
		width?: string | undefined;
	}
	const { src, alt, height, width, ...rest }: Props = $props();
</script>

<img {...rest} {src} {alt} style:width style:height />

<style>
	img {
		display: block;
		height: auto;
		width: auto;
	}
</style>
