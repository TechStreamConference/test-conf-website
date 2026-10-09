<script lang="ts">
    import type { Menu } from '$lib/helper/menus';
    import type { UserState } from '$lib/helper/menus';

    import BasePage from '$lib/elements/layout/BasePage.svelte';

    interface Props {
        languageTag: string;
        userState: UserState;
        headerMenu: Menu;
        footerMenu: Menu;
        events: { label: string; url: string }[];
        footerText: string;
        paragraphs: number;
    }
    const { paragraphs, ...rest }: Props = $props();
</script>

<BasePage {...rest}>
    <article>
        {#each Array(paragraphs) as _, i (i)}
            <p>Sample content, paragraph {i + 1}.</p>
        {/each}
    </article>
</BasePage>

<style>
    article {
        display: flex;
        flex-direction: column;
        gap: 1rem;

        padding: 2rem var(--full-padding);
    }
</style>
