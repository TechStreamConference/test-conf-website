// This hook includes the client and forceses it to set the base URL.

import '$bff/client';

import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
	return resolve(event);
};
