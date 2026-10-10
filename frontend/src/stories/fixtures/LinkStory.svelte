<script lang="ts">
    import InlineLink from '$lib/elements/link/InlineLink.svelte';
    import Link from '$lib/elements/link/Link.svelte';
    import { LinkTarget } from '$lib/helper/link-options';
    import { LinkVariant } from '$lib/helper/link-options';

    type Variant = 'Inline' | keyof typeof LinkVariant;

    interface Props {
        variant: Variant;
        label: string;
        href: string;
        'aria-label': string;
        target: LinkTarget;
    }
    let { variant, label, href, 'aria-label': ariaLabel, target }: Props = $props();
</script>

<!-- The menu, footer and plain variants are made for the colored bars of the header and the footer. -->
<div class:colored={variant !== 'Inline' && variant !== 'Button'}>
    {#if variant === 'Inline'}
        <InlineLink {href} aria-label={ariaLabel} {target}>{label}</InlineLink>
    {:else}
        <Link {href} aria-label={ariaLabel} {target} variant={LinkVariant[variant]}>{label}</Link>
    {/if}
</div>

<style>
    .colored {
        padding: 1rem;

        background-color: var(--primary-color-600);
    }
</style>
