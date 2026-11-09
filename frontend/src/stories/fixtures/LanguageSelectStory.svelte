<script lang="ts">
    import LanguageSelect from '$lib/elements/language/LanguageSelect.svelte';

    interface Props {
        languageTag: string;
    }
    const { languageTag }: Props = $props();
</script>

<div>
    <LanguageSelect {languageTag} />
</div>

<style>
    div {
        display: flex;
        align-items: center;
        justify-content: center;

        min-height: 100vh;

        background-color: var(--primary-color-600);
    }
</style>
