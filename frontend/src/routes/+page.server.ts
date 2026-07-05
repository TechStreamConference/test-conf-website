import { loadGlobals } from '$bff/v1/globals.server';

export async function load() {
	return {
		globals: await loadGlobals()
	};
}
