<script lang="ts">
    import ThemeSelect from '$lib/elements/theme/ThemeSelect.svelte';

    interface Props {
        languageTag: string;
    }
    const { languageTag }: Props = $props();
</script>

<div>
    <ThemeSelect {languageTag} />
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
