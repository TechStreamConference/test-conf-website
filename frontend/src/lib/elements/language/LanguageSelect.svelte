<script lang="ts">
    import type { SwitchItem } from '$lib/elements/switch/switch-item';
    import { i18n } from '$lib/helper/translate';
    import { languageTagToFlagCountryCode } from '$lib/helper/language-flag';
    import { nativeLanguageName } from '$lib/helper/language-flag';
    import Switch from '$lib/elements/switch/Switch.svelte';

    import { locales } from '$paraglide/runtime';
    import { m } from '$paraglide/messages';

    interface Props {
        languageTag: string;
    }
    const { languageTag }: Props = $props();

    // Only changes the local selection for now; actually switching the page's language needs backend wiring that does not exist yet.
    let selectedLanguageTag: string = $derived(languageTag);

    const items: SwitchItem<string>[] = locales.map((tag) => ({
        value: tag,
        label: nativeLanguageName(tag),
        icon: flagIcon
    }));

    /**
     * @brief Selects a language.
     * @param tag the newly selected language tag.
     */
    function selectLanguage(tag: string): void {
        selectedLanguageTag = tag;
    }
</script>

{#snippet flagIcon(tag: string)}
    {@const code = languageTagToFlagCountryCode(tag)}
    <span class:fi={true} class:fi-de={code === 'de'} class:fi-gb={code === 'gb'} aria-hidden="true"
    ></span>
{/snippet}
{#snippet triggerIcon()}
    {@const code = languageTagToFlagCountryCode(selectedLanguageTag)}
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
