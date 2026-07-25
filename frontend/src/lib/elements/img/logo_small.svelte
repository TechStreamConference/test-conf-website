<script lang="ts">
	import Image from '$lib/elements/img/image.svelte';

	interface Props {
		height?: string | undefined;
		width?: string | undefined;
		classes?: string | undefined;
	}
	const { height, width, classes }: Props = $props();
</script>

<Image src="/logo_small.png" alt="small Test-Conf logo" {height} {width} {classes} />
