<script lang="ts">
	import Image from '$lib/elements/img/image.svelte';

	interface Props {
		height?: string | undefined;
		width?: string | undefined;
		classes?: string | undefined;
	}
	const { height, width, classes }: Props = $props();
</script>

<Image src="/img/logo_big.png" alt="big Test-Conf logo" {height} {width} {classes} />
