<script lang="ts">
    import Headline from '$lib/elements/text/Headline.svelte';
    import Paragraph from '$lib/elements/text/Paragraph.svelte';
    import SubHeadline from '$lib/elements/text/SubHeadline.svelte';
</script>

<article>
    <Headline renderLine>Tech Stream Conference</Headline>
    <SubHeadline>Building reliable software together</SubHeadline>
    <Paragraph>
        A two-day online conference for engineers who care about testing, quality and sustainable
        software development. Expect talks, workshops and plenty of hallway conversations.
    </Paragraph>
    <Paragraph>
        The page around this text is the base page: a sticky header, this content area that
        stretches and a footer that always stays at the bottom.
    </Paragraph>
</article>

<style>
    article {
        display: flex;
        flex-direction: column;
        gap: 1rem;

        max-width: 60rem;
        margin: 0 auto;
        padding: 2rem 1rem;
    }
</style>
