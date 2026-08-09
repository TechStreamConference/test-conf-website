<script lang="ts">
	import type { HTMLImgAttributes } from 'svelte/elements';
	import Image from '$lib/elements/img/image.svelte';

	interface Props extends Omit<HTMLImgAttributes, 'src' | 'alt'> {
		height?: string | undefined;
		width?: string | undefined;
	}
	const { height, width, ...rest }: Props = $props();
</script>

<Image src="/img/logo_small.png" alt="Tech Stream Conference Logo" {height} {width} {...rest} />
