<script lang="ts">
    import LogoBig from '$lib/elements/img/LogoBig.svelte';
    import LogoSmall from '$lib/elements/img/LogoSmall.svelte';

    const LANGUAGE_TAG = 'en';

    interface Props {
        variant: 'big' | 'small';
        width: string;
    }

    let { variant, width }: Props = $props();
</script>

{#if variant === 'big'}
    <LogoBig languageTag={LANGUAGE_TAG} {width} />
{:else}
    <LogoSmall languageTag={LANGUAGE_TAG} {width} />
{/if}
