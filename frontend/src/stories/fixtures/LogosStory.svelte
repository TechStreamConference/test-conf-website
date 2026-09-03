<script lang="ts">
	import LogoBig from '$lib/elements/img/LogoBig.svelte';
	import LogoSmall from '$lib/elements/img/LogoSmall.svelte';

	interface Props {
		variant: 'big' | 'small';
		width: string;
	}

	let { variant, width }: Props = $props();
</script>

{#if variant === 'big'}
	<LogoBig {width} />
{:else}
	<LogoSmall {width} />
{/if}
