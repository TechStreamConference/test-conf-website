<script lang="ts">
	import type { GlobalsResponseV1 } from '$gen/types.gen';

	let { data } = $props<{
		data: {
			globals: GlobalsResponseV1;
		};
	}>();
</script>

<h1>{data.globals.title}</h1>
