<script lang="ts">
	import InlineLink from '$lib/elements/link/InlineLink.svelte';
	import Link from '$lib/elements/link/Link.svelte';

	import { LinkTarget } from '$lib/helper/link-options';

	interface Props {
		variant: 'inline' | 'button';
		label: string;
		href: string;
		aria_label: string;
		target: LinkTarget;
	}
	let { variant, label, href, aria_label, target }: Props = $props();
</script>

{#if variant === 'inline'}
	<InlineLink {href} {aria_label} {target}>{label}</InlineLink>
{:else}
	<Link {href} {aria_label} {target}>{label}</Link>
{/if}
