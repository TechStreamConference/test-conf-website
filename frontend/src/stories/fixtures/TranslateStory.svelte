<script lang="ts">
    import { i18n } from '$lib/helper/translate';

    import { m } from '$paraglide/messages';

    const MESSAGES = {
        test_plain: m.test_plain,
        test_plain2: m.test_plain2,
        test_withPlaceholder: m.test_withPlaceholder
    } as const;

    interface Props {
        languageTag: string;
        message: keyof typeof MESSAGES;
        placeholder1: string;
        placeholder2: string;
    }
    const { languageTag, message, placeholder1, placeholder2 }: Props = $props();
</script>

{#if message === 'test_withPlaceholder'}
    <button type="button"
        >{i18n(MESSAGES[message], languageTag, {
            placeholder1: placeholder1,
            placeholder2: placeholder2
        })}</button
    >
{:else}
    <button type="button">{i18n(MESSAGES[message], languageTag)}</button>
{/if}
