<script lang="ts">
	import type { GlobalsResponseV1 } from '$gen/types.gen';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props<{
		data: {
			globals: GlobalsResponseV1;
		};
	}>();
</script>

<h1>{data.globals.footer_text}</h1>

<style>
	h1 {
		color: var(--text-color);
	}
</style>
