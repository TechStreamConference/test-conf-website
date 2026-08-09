<script lang="ts">
	import LogoBig from '$lib/elements/img/logo_big.svelte';
	import LogoSmall from '$lib/elements/img/logo_small.svelte';

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
