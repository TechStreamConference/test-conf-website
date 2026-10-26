<script lang="ts">
    import { i18n } from '$lib/helper/translate';

    import { m } from '$paraglide/messages';

    const MESSAGES = {
        global_themeSelectDark: m.global_themeSelectDark,
        global_themeSelectLight: m.global_themeSelectLight,
        footer_copyright: m.footer_copyright
    } as const;

    interface Props {
        languageTag: string;
        message: keyof typeof MESSAGES;
        year: string;
    }
    const { languageTag, message, year }: Props = $props();
</script>

{#if message === 'footer_copyright'}
    <button type="button"
        >{i18n(MESSAGES[message], languageTag, {
            year
        })}</button
    >
{:else}
    <button type="button">{i18n(MESSAGES[message], languageTag)}</button>
{/if}
