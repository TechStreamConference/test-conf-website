<script lang="ts">
	interface Props {
		src: string;
		alt: string;
		height?: string;
		width?: string;
		classes?: string;
	}

	const { src, alt, height, width, classes }: Props = $props();
</script>

<img {src} {alt} class={classes} style:width style:height />

<style>
	img {
		display: block;
		height: auto;
		width: auto;
	}
</style>
