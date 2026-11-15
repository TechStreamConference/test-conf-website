<script lang="ts">
    import { goto } from '$app/navigation';
    import { page } from '$app/state';

    import type { SwitchItem } from '$lib/elements/switch/switch-item';
    import { i18n } from '$lib/helper/translate';
    import { languageTagToFlagCountryCode } from '$lib/helper/language-flag';
    import { nativeLanguageName } from '$lib/helper/language-flag';
    import { withLanguagePrefix } from '$lib/helper/language-url';
    import Switch from '$lib/elements/switch/Switch.svelte';

    import { locales } from '$paraglide/runtime';
    import { m } from '$paraglide/messages';

    interface Props {
        languageTag: string;
    }
    const { languageTag }: Props = $props();

    // Whether `languageTag` is such a fallback. A page sets this via its own page data (not a prop, so it
    // does not have to be threaded through every layout component), once it knows its own backend call
    // fell back. We cannot tell a real `en` choice apart from a fallback to `en` by the tag value alone, so
    // this has to be an explicit flag rather than something guessed from `languageTag` itself.
    const isLanguageFallback = $derived(page.data.isLanguageFallback ?? false);

    // No option is marked as selected for a fallback, since the visitor did not actually choose it.
    let selectedLanguageTag: string | undefined = $derived(
        isLanguageFallback ? undefined : languageTag
    );

    const items: SwitchItem<string>[] = locales.map((tag) => ({
        value: tag,
        label: nativeLanguageName(tag),
        icon: flagIcon
    }));

    /**
     * @brief Stores the chosen language in a cookie, then soft-navigates to its localized URL (e.g. `/de`):
     * the browser does not reload, but `load` functions run again so texts update to the new language.
     * @param tag the newly selected language tag.
     */
    async function selectLanguage(tag: string): Promise<void> {
        selectedLanguageTag = tag;

        await fetch('/language', {
            method: 'PUT',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language: tag })
        });

        // There is no fixed SvelteKit route for a language-prefixed path to resolve against: a hook
        // strips the prefix again before the path reaches the router.
        // eslint-disable-next-line svelte/no-navigation-without-resolve
        await goto(withLanguagePrefix(page.url.pathname, tag) + page.url.search, {
            invalidateAll: true,
            noScroll: true
        });
    }
</script>

{#snippet flagIcon(tag: string)}
    {@const code = languageTagToFlagCountryCode(tag)}
    <span class:fi={true} class:fi-de={code === 'de'} class:fi-gb={code === 'gb'} aria-hidden="true"
    ></span>
{/snippet}
{#snippet triggerIcon()}
    {@const code = languageTagToFlagCountryCode(languageTag)}
    <span
        class:fi={true}
        class:fi-de={code === 'de'}
        class:fi-gb={code === 'gb'}
        class:trigger-flag={true}
        aria-hidden="true"
    ></span>
{/snippet}

<Switch
    {items}
    selected={selectedLanguageTag}
    onSelect={selectLanguage}
    {triggerIcon}
    aria-label={i18n(m.global_languageSelect_aria, languageTag)}
/>

<style>
    .trigger-flag {
        border-radius: var(--border-radius);
        font-size: 1.4rem;
    }
</style>
