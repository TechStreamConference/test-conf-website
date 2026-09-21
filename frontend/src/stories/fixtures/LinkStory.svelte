<!--
    Tech Stream Conference
    2026

    Storybook fixture for the links.
-->
<script lang="ts">
    import InlineLink from '$lib/elements/link/InlineLink.svelte';
    import Link from '$lib/elements/link/Link.svelte';
    import { LinkTarget } from '$lib/helper/link-options';

    interface Props {
        variant: 'inline' | 'button';
        label: string;
        href: string;
        'aria-label': string;
        target: LinkTarget;
    }
    let { variant, label, href, 'aria-label': ariaLabel, target }: Props = $props();
</script>

{#if variant === 'inline'}
    <InlineLink {href} aria-label={ariaLabel} {target}>{label}</InlineLink>
{:else}
    <Link {href} aria-label={ariaLabel} {target}>{label}</Link>
{/if}
