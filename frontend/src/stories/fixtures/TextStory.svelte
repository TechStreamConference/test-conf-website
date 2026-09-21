<!--
    Tech Stream Conference
    2026

    Storybook fixture for the text elements.
-->
<script lang="ts">
    import Headline from '$lib/elements/text/Headline.svelte';
    import Paragraph from '$lib/elements/text/Paragraph.svelte';
    import SubHeadline from '$lib/elements/text/SubHeadline.svelte';
    import Tag from '$lib/elements/text/Tag.svelte';
    import { TagColor } from '$lib/helper/tag';

    interface Props {
        variant: 'headline' | 'subheadline' | 'paragraph' | 'tag';
        text: string;
        renderLine: boolean;
        preserveNewlines: boolean;
        tagColor: TagColor;
    }
    let { variant, text, renderLine, preserveNewlines, tagColor }: Props = $props();
</script>

{#if variant === 'headline'}
    <Headline {renderLine}>{text}</Headline>
{:else if variant === 'subheadline'}
    <SubHeadline>{text}</SubHeadline>
{:else if variant === 'paragraph'}
    <Paragraph {preserveNewlines}>{text}</Paragraph>
{:else}
    <Tag {tagColor}>{text}</Tag>
{/if}
