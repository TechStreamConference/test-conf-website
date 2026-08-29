<script lang="ts">
	import type { HTMLAttributes } from 'svelte/elements';

	import type { PlaceholderBackendTagClass } from '$src/placeholder/tag';
	import Tag from '$lib/elements/text/Tag.svelte';
	import { getTagColor } from '$lib/helper/tag';

	interface Props extends HTMLAttributes<HTMLDivElement> {
		tags: PlaceholderBackendTagClass[]; // replace that with the actual backend type later
	}
	const { tags, ...rest }: Props = $props();
</script>

<div {...rest}>
	{#each tags as tag (tag.id)}
		<Tag tag_color={getTagColor(tag.color_id)}>{tag.text}</Tag>
	{/each}
</div>

<style>
	div {
		display: flex;
		flex-direction: row;
		align-items: flex-start;
		justify-content: flex-end;
		align-content: flex-start;
		flex-wrap: wrap;
		gap: 0.2rem;
	}
</style>
